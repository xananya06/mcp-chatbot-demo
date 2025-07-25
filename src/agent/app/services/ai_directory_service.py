#!/usr/bin/env python3
# src/agent/app/services/ai_directory_service.py
# All-in-one AI Directory Service (scraping + database integration)
# Follows the same pattern as real_apis_service.py

import requests
from bs4 import BeautifulSoup
import time
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import json
from dataclasses import dataclass

# Database imports
try:
    from app.db.database import SessionLocal
    from app.models.chat import DiscoveredTool
    from sqlalchemy import and_, or_
    DATABASE_AVAILABLE = True
except ImportError as e:
    DATABASE_AVAILABLE = False
    print(f"⚠️ Database not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AITool:
    """Data class for discovered AI tools"""
    name: str
    description: str
    website: str
    category: str
    source: str
    pricing: Optional[str] = None
    tags: List[str] = None
    rating: Optional[float] = None
    last_updated: Optional[str] = None
    github_url: Optional[str] = None
    api_available: Optional[bool] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class AIDirectoryService:
    """
    All-in-one AI Directory Service
    Scrapes AI directories and saves directly to database
    Same pattern as real_apis_service.py
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Rate limiting
        self.request_delay = 2  # seconds between requests
        self.last_request_time = 0
        
        self.stats = {
            'total_scraped': 0,
            'total_saved': 0,
            'total_duplicates': 0,
            'total_errors': 0
        }
    
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _safe_request(self, url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
        """Make a safe HTTP request with error handling"""
        try:
            self._rate_limit()
            logger.debug(f"  📡 Fetching: {url}")
            
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Check if we got actual HTML content
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"  ⚠️ Non-HTML content type: {content_type}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  ❌ Request failed for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"  ❌ Unexpected error for {url}: {str(e)}")
            return None
    
    def _extract_tool_info(self, element, base_url: str, source: str) -> Optional[AITool]:
        """Extract tool information from HTML element"""
        try:
            # Common patterns for extracting tool info
            name = self._extract_text(element, ['.tool-name', '.title', 'h3', 'h2', 'h1', '.name', '.card-title'])
            description = self._extract_text(element, ['.description', '.summary', '.excerpt', 'p', '.card-text'])
            
            # Extract URL
            url = self._extract_url(element, base_url)
            
            # Extract category
            category = self._extract_text(element, ['.category', '.tag', '.label', '.badge'])
            
            # Extract pricing if available
            pricing = self._extract_text(element, ['.pricing', '.price', '.cost'])
            
            # Extract rating if available
            rating = self._extract_rating(element)
            
            if name and url:
                return AITool(
                    name=name.strip()[:255],  # Limit for database
                    description=description.strip()[:1000] if description else "",  # Limit for database
                    website=url,
                    category=category or "AI Tool",
                    source=source,
                    pricing=pricing,
                    rating=rating,
                    last_updated=datetime.now().isoformat()
                )
        except Exception as e:
            logger.debug(f"  ⚠️ Failed to extract tool info: {str(e)}")
        
        return None
    
    def _extract_text(self, element, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple selector fallbacks"""
        for selector in selectors:
            try:
                found = element.select_one(selector)
                if found and found.get_text(strip=True):
                    return found.get_text(strip=True)
            except:
                continue
        return None
    
    def _extract_url(self, element, base_url: str) -> Optional[str]:
        """Extract URL from element"""
        for selector in ['a', '[href]']:
            try:
                link = element.select_one(selector)
                if link and link.get('href'):
                    url = link.get('href')
                    if url.startswith('http'):
                        return url
                    elif url.startswith('/'):
                        return urljoin(base_url, url)
            except:
                continue
        return None
    
    def _extract_rating(self, element) -> Optional[float]:
        """Extract rating from element"""
        try:
            rating_text = self._extract_text(element, ['.rating', '.score', '.stars'])
            if rating_text:
                # Extract number from rating text
                numbers = re.findall(r'\d+\.?\d*', rating_text)
                if numbers:
                    return float(numbers[0])
        except:
            pass
        return None
    
    def _convert_to_discovered_tool(self, ai_tool: AITool) -> DiscoveredTool:
        """Convert AITool to DiscoveredTool database model"""
        
        # Extract GitHub URL if present
        github_url = ai_tool.github_url
        if not github_url:
            # Try to find GitHub URL in description
            github_pattern = r'https?://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+'
            github_matches = re.findall(github_pattern, ai_tool.description + " " + ai_tool.website)
            github_url = github_matches[0] if github_matches else None
        
        # Determine tool type
        tool_type = "ai_tool"
        if "api" in ai_tool.description.lower() or "api" in ai_tool.name.lower():
            tool_type = "api"
        elif "automation" in ai_tool.category.lower():
            tool_type = "automation_tool" 
        elif "ml" in ai_tool.category.lower() or "machine learning" in ai_tool.category.lower():
            tool_type = "ml_tool"
        
        return DiscoveredTool(
            name=ai_tool.name,
            description=ai_tool.description,
            website=ai_tool.website,
            github_url=github_url,
            category=ai_tool.category,
            tool_type_detected=tool_type,
            source_api=ai_tool.source,
            pricing_type=ai_tool.pricing,
            is_free=ai_tool.pricing and "free" in ai_tool.pricing.lower(),
            website_status=200,  # Assume working since we just scraped it
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
    
    def _save_tools_to_database(self, tools: List[AITool]) -> Dict[str, int]:
        """Save scraped tools to database"""
        
        if not DATABASE_AVAILABLE:
            logger.error("❌ Database not available")
            return {"saved": 0, "duplicates": 0, "errors": 0}
        
        db = SessionLocal()
        saved_count = 0
        duplicate_count = 0
        error_count = 0
        
        try:
            for tool in tools:
                try:
                    # Check if tool already exists (by website URL)
                    existing = db.query(DiscoveredTool).filter(
                        DiscoveredTool.website == tool.website
                    ).first()
                    
                    if existing:
                        duplicate_count += 1
                        logger.debug(f"  🔄 Duplicate: {tool.name}")
                        continue
                    
                    # Convert and save new tool
                    db_tool = self._convert_to_discovered_tool(tool)
                    db.add(db_tool)
                    saved_count += 1
                    
                    logger.debug(f"  💾 Saved: {tool.name}")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"  ❌ Error saving {tool.name}: {str(e)}")
                    continue
            
            # Commit all changes
            db.commit()
            
            return {
                "saved": saved_count,
                "duplicates": duplicate_count, 
                "errors": error_count
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"  ❌ Database transaction failed: {str(e)}")
            return {"saved": 0, "duplicates": 0, "errors": len(tools)}
        
        finally:
            db.close()
    
    def _scrape_theresanaiforthat(self, limit: int = 100) -> List[AITool]:
        """Scrape There's An AI For That directory"""
        tools = []
        base_url = "https://theresanaiforthat.com"
        
        try:
            logger.info(f"🤖 Scraping There's An AI For That...")
            
            # Try different page URLs
            urls_to_try = [
                f"{base_url}/ai-tools",
                f"{base_url}/tools", 
                f"{base_url}/directory",
                f"{base_url}/browse",
                base_url
            ]
            
            for url in urls_to_try[:2]:  # Try first 2 URLs
                soup = self._safe_request(url)
                if not soup:
                    continue
                
                # Look for tool listings with various selectors
                tool_selectors = [
                    '.tool-card',
                    '.ai-tool',
                    '.tool-item',
                    '.card',
                    '.tool',
                    '[data-tool]',
                    '.grid-item',
                    '.listing-item'
                ]
                
                for selector in tool_selectors:
                    elements = soup.select(selector)
                    if elements:
                        logger.info(f"  📋 Found {len(elements)} potential tools with selector: {selector}")
                        
                        for element in elements[:limit]:
                            tool = self._extract_tool_info(element, base_url, "There's An AI For That")
                            if tool:
                                tools.append(tool)
                        
                        if tools:
                            break  # Found tools, stop trying selectors
                
                if tools:
                    break  # Found tools, stop trying URLs
            
            logger.info(f"  ✅ Extracted {len(tools)} tools")
            
        except Exception as e:
            logger.error(f"  ❌ Error: {str(e)}")
        
        return tools
    
    def _scrape_aitoolsdirectory(self, limit: int = 100) -> List[AITool]:
        """Scrape AI Tools Directory"""
        tools = []
        base_url = "https://aitoolsdirectory.com"
        
        try:
            logger.info(f"🤖 Scraping AI Tools Directory...")
            
            urls_to_try = [
                f"{base_url}/tools",
                f"{base_url}/directory", 
                f"{base_url}/browse",
                f"{base_url}/all-tools",
                base_url
            ]
            
            for url in urls_to_try[:2]:
                soup = self._safe_request(url)
                if not soup:
                    continue
                
                tool_selectors = [
                    '.tool-card',
                    '.directory-item',
                    '.tool-listing',
                    '.tool',
                    '.card',
                    '.item',
                    '.ai-tool'
                ]
                
                for selector in tool_selectors:
                    elements = soup.select(selector)
                    if elements:
                        logger.info(f"  📋 Found {len(elements)} potential tools")
                        
                        for element in elements[:limit]:
                            tool = self._extract_tool_info(element, base_url, "AI Tools Directory")
                            if tool:
                                tools.append(tool)
                        
                        if tools:
                            break
                
                if tools:
                    break
            
            logger.info(f"  ✅ Extracted {len(tools)} tools")
            
        except Exception as e:
            logger.error(f"  ❌ Error: {str(e)}")
        
        return tools
    
    def _scrape_futurepedia(self, limit: int = 100) -> List[AITool]:
        """Scrape Futurepedia"""
        tools = []
        base_url = "https://www.futurepedia.io"
        
        try:
            logger.info(f"🤖 Scraping Futurepedia...")
            
            urls_to_try = [
                f"{base_url}/ai-tools",
                f"{base_url}/tools",
                f"{base_url}/directory",
                base_url
            ]
            
            for url in urls_to_try[:2]:
                soup = self._safe_request(url)
                if not soup:
                    continue
                
                tool_selectors = [
                    '.tool-card',
                    '.ai-tool-card',
                    '.tool-item',
                    '.directory-item',
                    '.card',
                    '.tool',
                    '.grid-item'
                ]
                
                for selector in tool_selectors:
                    elements = soup.select(selector)
                    if elements:
                        logger.info(f"  📋 Found {len(elements)} potential tools")
                        
                        for element in elements[:limit]:
                            tool = self._extract_tool_info(element, base_url, "Futurepedia")
                            if tool:
                                tools.append(tool)
                        
                        if tools:
                            break
                
                if tools:
                    break
            
            logger.info(f"  ✅ Extracted {len(tools)} tools")
            
        except Exception as e:
            logger.error(f"  ❌ Error: {str(e)}")
        
        return tools
    
    def _deduplicate_tools(self, tools: List[AITool]) -> List[AITool]:
        """Remove duplicate tools based on website URL"""
        seen_urls = set()
        unique_tools = []
        
        for tool in tools:
            # Normalize URL for comparison
            normalized_url = tool.website.lower().rstrip('/')
            
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_tools.append(tool)
        
        return unique_tools
    
    # Main API methods (like real_apis_service.py)
    
    def run_sync_scrape_all_directories(self, target_tools: int = 300) -> Dict[str, Any]:
        """Scrape all AI directories and save to database - main method"""
        
        logger.info(f"🤖 Starting AI Directory Discovery - Target: {target_tools} tools")
        start_time = time.time()
        
        all_tools = []
        tools_per_directory = target_tools // 3  # 3 directories
        
        try:
            # Scrape each directory
            directories = [
                ("theresanaiforthat", self._scrape_theresanaiforthat),
                ("aitoolsdirectory", self._scrape_aitoolsdirectory),
                ("futurepedia", self._scrape_futurepedia)
            ]
            
            directory_results = {}
            
            for dir_name, scrape_method in directories:
                try:
                    dir_start = time.time()
                    tools = scrape_method(tools_per_directory)
                    dir_time = time.time() - dir_start
                    
                    all_tools.extend(tools)
                    
                    directory_results[dir_name] = {
                        "success": True,
                        "tools_discovered": len(tools),
                        "processing_time": dir_time
                    }
                    
                    # Small delay between directories
                    time.sleep(1)
                    
                except Exception as e:
                    directory_results[dir_name] = {
                        "success": False,
                        "error": str(e),
                        "tools_discovered": 0,
                        "processing_time": 0
                    }
            
            # Remove duplicates
            unique_tools = self._deduplicate_tools(all_tools)
            
            # Save to database
            logger.info(f"💾 Saving {len(unique_tools)} unique tools to database...")
            db_result = self._save_tools_to_database(unique_tools)
            
            processing_time = time.time() - start_time
            
            # Update stats
            self.stats["total_scraped"] += len(all_tools)
            self.stats["total_saved"] += db_result["saved"]
            self.stats["total_duplicates"] += db_result["duplicates"]
            self.stats["total_errors"] += db_result["errors"]
            
            logger.info(f"✅ AI Directory Discovery Complete!")
            logger.info(f"📊 Results: {len(all_tools)} scraped, {len(unique_tools)} unique, {db_result['saved']} saved")
            
            return {
                "success": True,
                "total_scraped": len(all_tools),
                "total_saved": db_result["saved"],
                "total_duplicates": db_result["duplicates"],
                "total_errors": db_result["errors"],
                "processing_time": processing_time,
                "directory_results": directory_results
            }
            
        except Exception as e:
            logger.error(f"❌ Directory discovery failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0,
                "directory_results": {}
            }
    
    def run_sync_scrape_theresanaiforthat(self, target_tools: int = 100) -> Dict[str, Any]:
        """Scrape There's An AI For That specifically"""
        start_time = time.time()
        
        try:
            tools = self._scrape_theresanaiforthat(target_tools)
            db_result = self._save_tools_to_database(tools)
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_scraped": len(tools),
                "total_saved": db_result["saved"],
                "processing_time": processing_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0
            }
    
    def run_sync_scrape_aitoolsdirectory(self, target_tools: int = 100) -> Dict[str, Any]:
        """Scrape AI Tools Directory specifically"""
        start_time = time.time()
        
        try:
            tools = self._scrape_aitoolsdirectory(target_tools)
            db_result = self._save_tools_to_database(tools)
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_scraped": len(tools),
                "total_saved": db_result["saved"],
                "processing_time": processing_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0
            }
    
    def run_sync_scrape_futurepedia(self, target_tools: int = 100) -> Dict[str, Any]:
        """Scrape Futurepedia specifically"""
        start_time = time.time()
        
        try:
            tools = self._scrape_futurepedia(target_tools)
            db_result = self._save_tools_to_database(tools)
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_scraped": len(tools),
                "total_saved": db_result["saved"],
                "processing_time": processing_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0
            }
    
    # Incremental methods for integration with incremental discovery
    def run_sync_scrape_all_directories_incremental(self, target_tools: int = 300, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental version - check if we've scraped recently"""
        
        if incremental_params and not incremental_params.get("force_full_scan", False):
            last_check_times = incremental_params.get("last_check_times", {})
            last_check = last_check_times.get("directories")
            
            if last_check:
                last_check_dt = datetime.fromisoformat(last_check)
                hours_since = (datetime.utcnow() - last_check_dt).total_seconds() / 3600
                
                if hours_since < 12:  # Skip if checked within 12 hours
                    logger.info(f"⏭️ Skipping directory scraping - last checked {hours_since:.1f} hours ago")
                    return {
                        "success": True,
                        "total_saved": 0,
                        "total_skipped": target_tools,
                        "incremental_skip": True
                    }
        
        # Run normal scraping
        result = self.run_sync_scrape_all_directories(target_tools)
        result["total_skipped"] = 0
        result["incremental_skip"] = False
        return result
    
    def run_sync_scrape_theresanaiforthat_incremental(self, target_tools: int = 100, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental version for There's An AI For That"""
        if incremental_params and not incremental_params.get("force_full_scan", False):
            last_check_times = incremental_params.get("last_check_times", {})
            last_check = last_check_times.get("theresanaiforthat")
            
            if last_check:
                last_check_dt = datetime.fromisoformat(last_check)
                hours_since = (datetime.utcnow() - last_check_dt).total_seconds() / 3600
                
                if hours_since < 24:  # Check daily
                    logger.info(f"⏭️ Skipping There's An AI For That - last checked {hours_since:.1f} hours ago")
                    return {
                        "success": True,
                        "total_saved": 0,
                        "total_skipped": target_tools,
                        "incremental_skip": True
                    }
        
        result = self.run_sync_scrape_theresanaiforthat(target_tools)
        result["total_skipped"] = 0
        result["incremental_skip"] = False
        return result
    
    def run_sync_scrape_aitoolsdirectory_incremental(self, target_tools: int = 100, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental version for AI Tools Directory"""
        if incremental_params and not incremental_params.get("force_full_scan", False):
            last_check_times = incremental_params.get("last_check_times", {})
            last_check = last_check_times.get("aitoolsdirectory")
            
            if last_check:
                last_check_dt = datetime.fromisoformat(last_check)
                hours_since = (datetime.utcnow() - last_check_dt).total_seconds() / 3600
                
                if hours_since < 24:  # Check daily
                    logger.info(f"⏭️ Skipping AI Tools Directory - last checked {hours_since:.1f} hours ago")
                    return {
                        "success": True,
                        "total_saved": 0,
                        "total_skipped": target_tools,
                        "incremental_skip": True
                    }
        
        result = self.run_sync_scrape_aitoolsdirectory(target_tools)
        result["total_skipped"] = 0
        result["incremental_skip"] = False
        return result
    
    def run_sync_scrape_futurepedia_incremental(self, target_tools: int = 100, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental version for Futurepedia"""
        if incremental_params and not incremental_params.get("force_full_scan", False):
            last_check_times = incremental_params.get("last_check_times", {})
            last_check = last_check_times.get("futurepedia")
            
            if last_check:
                last_check_dt = datetime.fromisoformat(last_check)
                hours_since = (datetime.utcnow() - last_check_dt).total_seconds() / 3600
                
                if hours_since < 24:  # Check daily
                    logger.info(f"⏭️ Skipping Futurepedia - last checked {hours_since:.1f} hours ago")
                    return {
                        "success": True,
                        "total_saved": 0,
                        "total_skipped": target_tools,
                        "incremental_skip": True
                    }
        
        result = self.run_sync_scrape_futurepedia(target_tools)
        result["total_skipped"] = 0
        result["incremental_skip"] = False
        return result


# Create global instance for easy importing (like real_apis_service.py)
ai_directory_service = AIDirectoryService()


def main():
    """CLI interface for testing"""
    import sys
    
    service = AIDirectoryService()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "scrape-all":
            target = int(sys.argv[2]) if len(sys.argv) > 2 else 300
            result = service.run_sync_scrape_all_directories(target)
            
            if result['success']:
                print(f"✅ Scraping complete: {result['total_saved']} tools saved")
            else:
                print(f"❌ Scraping failed: {result.get('error')}")
                
        elif command == "scrape-single":
            if len(sys.argv) < 3:
                print("Usage: python ai_directory_service.py scrape-single <directory>")
                print("Available: theresanaiforthat, aitoolsdirectory, futurepedia")
                return
                
            directory = sys.argv[2]
            target = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            
            if directory == "theresanaiforthat":
                result = service.run_sync_scrape_theresanaiforthat(target)
            elif directory == "aitoolsdirectory":
                result = service.run_sync_scrape_aitoolsdirectory(target)
            elif directory == "futurepedia":
                result = service.run_sync_scrape_futurepedia(target)
            else:
                print(f"Unknown directory: {directory}")
                return
            
            if result['success']:
                print(f"✅ Single directory scrape complete: {result['total_saved']} tools saved")
            else:
                print(f"❌ Scraping failed: {result.get('error')}")
                
        else:
            print("❌ Unknown command")
    else:
        print("🤖 AI Directory Service")
        print("\nUsage:")
        print("  python ai_directory_service.py scrape-all [target]")
        print("  python ai_directory_service.py scrape-single <directory> [target]")
        print("\nExamples:")
        print("  python ai_directory_service.py scrape-all 200")
        print("  python ai_directory_service.py scrape-single theresanaiforthat 50")


if __name__ == "__main__":
    main()