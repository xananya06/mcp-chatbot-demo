import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.database import SessionLocal
from app.models.chat import DiscoveredTool

logger = logging.getLogger(__name__)

class HealthCheckService:
    """Automated health checks for discovered tools as described in PDF"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.max_concurrent = 20
        self.headers = {
            'User-Agent': 'AI Tools Health Check Bot 1.0 (checking tool availability)'
        }
    
    def generate_canonical_url(self, url: str) -> str:
        """Generate canonical URL for duplicate detection"""
        if not url:
            return ""
        
        try:
            parsed = urlparse(url.lower().strip())
            
            # Remove www prefix
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Keep only domain and path, remove query params and fragments
            canonical = f"{parsed.scheme}://{domain}{parsed.path}"
            
            # Remove trailing slash
            if canonical.endswith('/') and len(canonical) > 8:
                canonical = canonical[:-1]
                
            return canonical
            
        except Exception:
            return url.lower().strip()
    
    async def check_single_tool_health(self, session: aiohttp.ClientSession, tool: DiscoveredTool) -> Dict[str, Any]:
        """Check health of a single tool"""
        
        result = {
            "tool_id": tool.id,
            "name": tool.name,
            "website": tool.website,
            "status_code": None,
            "is_healthy": False,
            "redirect_url": None,
            "error": None,
            "response_time": None,
            "title_matches": False,
            "canonical_url": None
        }
        
        if not tool.website:
            result["error"] = "No website URL"
            return result
        
        try:
            start_time = datetime.utcnow()
            
            async with session.get(tool.website, headers=self.headers) as response:
                end_time = datetime.utcnow()
                result["response_time"] = (end_time - start_time).total_seconds()
                result["status_code"] = response.status
                result["is_healthy"] = response.status == 200
                
                # Check for redirects
                if str(response.url) != tool.website:
                    result["redirect_url"] = str(response.url)
                
                # Generate canonical URL
                result["canonical_url"] = self.generate_canonical_url(str(response.url))
                
                # Check if website title matches our tool name (for redirect detection)
                if response.status == 200:
                    try:
                        content = await response.text()
                        if '<title>' in content:
                            title_start = content.find('<title>') + 7
                            title_end = content.find('</title>', title_start)
                            if title_end > title_start:
                                page_title = content[title_start:title_end].strip()
                                # Simple fuzzy matching
                                tool_words = set(tool.name.lower().split())
                                title_words = set(page_title.lower().split())
                                common_words = tool_words.intersection(title_words)
                                result["title_matches"] = len(common_words) > 0
                    except Exception:
                        pass
                        
        except asyncio.TimeoutError:
            result["error"] = "Timeout"
            result["status_code"] = 408
        except aiohttp.ClientError as e:
            result["error"] = f"Client error: {str(e)}"
            result["status_code"] = 0
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            result["status_code"] = 0
            
        return result
    
    async def run_health_checks_batch(self, tools: List[DiscoveredTool]) -> List[Dict[str, Any]]:
        """Run health checks for a batch of tools concurrently"""
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def check_with_semaphore(tool):
                async with semaphore:
                    return await self.check_single_tool_health(session, tool)
            
            # Run all checks concurrently with rate limiting
            tasks = [check_with_semaphore(tool) for tool in tools]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return valid results
            valid_results = []
            for result in results:
                if isinstance(result, dict):
                    valid_results.append(result)
                else:
                    logger.error(f"Health check failed with exception: {result}")
            
            return valid_results
    
    def update_tool_health_status(self, db: Session, health_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Update database with health check results"""
        
        stats = {
            "healthy": 0,
            "unhealthy": 0,
            "updated": 0,
            "confidence_adjustments": 0
        }
        
        for result in health_results:
            try:
                tool = db.query(DiscoveredTool).filter(DiscoveredTool.id == result["tool_id"]).first()
                if not tool:
                    continue
                
                # Update health check fields
                tool.last_health_check = datetime.utcnow()
                tool.website_status = result["status_code"]
                
                # Update canonical URL if we got one
                if result["canonical_url"]:
                    tool.canonical_url = result["canonical_url"]
                
                # Adjust confidence score based on health
                if result["is_healthy"]:
                    stats["healthy"] += 1
                    # Slightly boost confidence for healthy tools
                    if tool.confidence_score and tool.confidence_score < 0.95:
                        tool.confidence_score = min(0.95, tool.confidence_score + 0.02)
                        stats["confidence_adjustments"] += 1
                else:
                    stats["unhealthy"] += 1
                    # Reduce confidence for unhealthy tools
                    if tool.confidence_score and tool.confidence_score > 0.3:
                        tool.confidence_score = max(0.3, tool.confidence_score - 0.1)
                        stats["confidence_adjustments"] += 1
                
                # Handle redirects - update website URL if permanently redirected
                if result["redirect_url"] and result["status_code"] in [301, 308]:
                    logger.info(f"Updating URL for {tool.name}: {tool.website} -> {result['redirect_url']}")
                    tool.website = result["redirect_url"]
                
                stats["updated"] += 1
                
            except Exception as e:
                logger.error(f"Error updating tool {result.get('tool_id')}: {e}")
        
        try:
            db.commit()
            logger.info(f"Health check update complete: {stats}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit health check updates: {e}")
        
        return stats
    
    async def run_daily_health_checks(self, batch_size: int = 100, max_tools: Optional[int] = None) -> Dict[str, Any]:
        """Run daily health checks as mentioned in PDF"""
        
        results = {
            "start_time": datetime.utcnow().isoformat(),
            "total_tools_checked": 0,
            "batches_processed": 0,
            "healthy_tools": 0,
            "unhealthy_tools": 0,
            "confidence_adjustments": 0,
            "processing_time": 0
        }
        
        start_time = datetime.utcnow()
        logger.info("🏥 Starting daily health checks...")
        
        db = SessionLocal()
        try:
            # Get tools that need health checks (haven't been checked in 24 hours or never checked)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            query = db.query(DiscoveredTool).filter(
                and_(
                    DiscoveredTool.website.isnot(None),
                    DiscoveredTool.website != ""
                )
            ).filter(
                or_(
                    DiscoveredTool.last_health_check.is_(None),
                    DiscoveredTool.last_health_check < cutoff_time
                )
            )
            
            if max_tools:
                query = query.limit(max_tools)
            
            tools_to_check = query.all()
            logger.info(f"🔍 Found {len(tools_to_check)} tools needing health checks")
            
            # Process in batches
            for i in range(0, len(tools_to_check), batch_size):
                batch = tools_to_check[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                logger.info(f"📋 Processing batch {batch_num}: {len(batch)} tools")
                
                # Run health checks for this batch
                health_results = await self.run_health_checks_batch(batch)
                
                # Update database with results
                batch_stats = self.update_tool_health_status(db, health_results)
                
                # Update overall results
                results["total_tools_checked"] += len(health_results)
                results["batches_processed"] += 1
                results["healthy_tools"] += batch_stats["healthy"]
                results["unhealthy_tools"] += batch_stats["unhealthy"]
                results["confidence_adjustments"] += batch_stats["confidence_adjustments"]
                
                logger.info(f"✅ Batch {batch_num} complete: {batch_stats['healthy']} healthy, {batch_stats['unhealthy']} unhealthy")
                
                # Small delay between batches to be respectful
                if i + batch_size < len(tools_to_check):
                    await asyncio.sleep(2)
                    
        finally:
            db.close()
        
        end_time = datetime.utcnow()
        results["end_time"] = end_time.isoformat()
        results["processing_time"] = (end_time - start_time).total_seconds()
        
        logger.info(f"🎊 Daily health checks complete!")
        logger.info(f"📈 Results: {results['total_tools_checked']} tools checked, "
                   f"{results['healthy_tools']} healthy, {results['unhealthy_tools']} unhealthy")
        
        return results
    
    def sync_run_daily_health_checks(self, batch_size: int = 100, max_tools: Optional[int] = None) -> Dict[str, Any]:
        """Synchronous wrapper for FastAPI"""
        return asyncio.run(self.run_daily_health_checks(batch_size, max_tools))

# Global service instance
health_check_service = HealthCheckService()