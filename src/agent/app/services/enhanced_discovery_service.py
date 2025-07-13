import asyncio
import aiohttp
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.database import SessionLocal
from app.models.chat import DiscoveredTool, SourceTracking
from app.services.health_check_service import HealthCheckService
from app.services.chat_service import save_discovered_tools_with_deduplication
from app.services.freshness_checker import ai_directory_checker

class EnhancedDiscoveryService:
    """Enhanced discovery service implementing PDF requirements"""
    
    def __init__(self):
        self.health_checker = HealthCheckService()
        
        # Source configurations from PDF
        self.ai_sources = {
            "theresanaiforthat": {
                "url": "https://theresanaiforthat.com",
                "type": "ai_directory",
                "frequency": "weekly",
                "last_checked": None,
                "tools_per_check": 50
            },
            "futurepedia": {
                "url": "https://www.futurepedia.io",
                "type": "ai_directory", 
                "frequency": "weekly",
                "last_checked": None,
                "tools_per_check": 100
            },
            "aitools_fyi": {
                "url": "https://aitools.fyi",
                "type": "ai_directory",
                "frequency": "weekly", 
                "last_checked": None,
                "tools_per_check": 75
            },
            "toolify_ai": {
                "url": "https://www.toolify.ai",
                "type": "ai_directory",
                "frequency": "weekly",
                "last_checked": None, 
                "tools_per_check": 80
            }
        }
    
    def check_source_freshness(self, db: Session, source_name: str) -> Dict[str, Any]:
        """Enhanced source freshness checking with HTTP headers"""
        
        source_track = db.query(SourceTracking).filter(
            SourceTracking.source_name == source_name
        ).first()
        
        if not source_track:
            # First time checking this source
            return {
                "should_scan": True,
                "reason": "never_checked",
                "last_checked": None,
                "freshness_method": "first_time"
            }
        
        # Use AI directory freshness checker for AI sources
        if source_name in ['theresanaiforthat', 'futurepedia', 'aitools_fyi', 'toolify_ai']:
            try:
                freshness_result = ai_directory_checker.sync_should_scan_ai_directory(
                    source_name, 
                    source_track.last_checked
                )
                freshness_result['freshness_method'] = 'http_headers_check'
                return freshness_result
                
            except Exception as e:
                print(f"Freshness check failed for {source_name}: {e}")
                # Fall back to time-based checking
        
        # Fallback to time-based checking for other sources
        now = datetime.utcnow()
        hours_since_check = 0
        
        if source_track.last_checked:
            hours_since_check = (now - source_track.last_checked).total_seconds() / 3600
        
        # Time-based intervals (fallback when HTTP checking fails)
        required_intervals = {
            'theresanaiforthat': 24,    # Daily
            'futurepedia': 24,          # Daily  
            'aitools_fyi': 168,         # Weekly
            'toolify_ai': 168,          # Weekly
            'github_api': 12,           # Twice daily
            'npm_api': 24,              # Daily
            'stackoverflow_api': 72,    # Every 3 days
        }
        
        required_interval = required_intervals.get(source_name, 24)  # Default 24 hours
        
        if hours_since_check >= required_interval:
            return {
                "should_scan": True,
                "reason": f"due_for_refresh ({hours_since_check:.1f}h >= {required_interval}h)",
                "last_checked": source_track.last_checked,
                "freshness_method": "time_based_fallback"
            }
        else:
            return {
                "should_scan": False,
                "reason": f"recently_checked ({hours_since_check:.1f}h < {required_interval}h)",
                "last_checked": source_track.last_checked,
                "freshness_method": "time_based_fallback"
            }
    
    def update_source_tracking(self, db: Session, source_name: str, tools_found: int, source_url: str = None):
        """Update source tracking information"""
        
        source_track = db.query(SourceTracking).filter(
            SourceTracking.source_name == source_name
        ).first()
        
        if not source_track:
            source_track = SourceTracking(
                source_name=source_name,
                source_url=source_url,
                new_tools_count=tools_found,
                last_checked=datetime.utcnow(),
                last_modified=datetime.utcnow()
            )
            db.add(source_track)
        else:
            source_track.last_checked = datetime.utcnow()
            source_track.new_tools_count = tools_found
            source_track.updated_at = datetime.utcnow()
            
            if tools_found > 0:
                source_track.last_modified = datetime.utcnow()
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error updating source tracking: {e}")
    
    def enhanced_duplicate_detection(self, db: Session, new_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Better duplicate detection using canonical URLs and company names"""
        
        duplicates_found = 0
        new_tools_clean = []
        
        for tool_data in new_tools:
            website = tool_data.get('website', '').strip()
            name = tool_data.get('name', '').strip()
            
            # Generate canonical URL
            canonical_url = self.health_checker.generate_canonical_url(website)
            tool_data['canonical_url'] = canonical_url
            
            # Extract company name (simple extraction from domain)
            if website:
                try:
                    domain = urlparse(website).netloc.lower()
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    # Remove .com, .ai, etc
                    company_name = domain.split('.')[0]
                    tool_data['company_name'] = company_name
                except:
                    tool_data['company_name'] = None
            
            # Check for duplicates by canonical URL
            existing_by_url = None
            if canonical_url:
                existing_by_url = db.query(DiscoveredTool).filter(
                    DiscoveredTool.canonical_url == canonical_url
                ).first()
            
            # Check for duplicates by company name + similar tool name
            existing_by_company = None
            if tool_data.get('company_name') and name:
                existing_by_company = db.query(DiscoveredTool).filter(
                    and_(
                        DiscoveredTool.company_name == tool_data['company_name'],
                        DiscoveredTool.name.ilike(f"%{name}%")
                    )
                ).first()
            
            if existing_by_url or existing_by_company:
                duplicates_found += 1
                # Update existing tool with new information if it's better
                existing_tool = existing_by_url or existing_by_company
                self._merge_tool_info(existing_tool, tool_data)
            else:
                new_tools_clean.append(tool_data)
        
        return {
            "original_count": len(new_tools),
            "duplicates_found": duplicates_found,
            "new_tools": new_tools_clean,
            "deduplication_rate": duplicates_found / len(new_tools) if new_tools else 0
        }
    
    def _merge_tool_info(self, existing_tool: DiscoveredTool, new_data: Dict[str, Any]):
        """Merge new tool information with existing tool"""
        
        # Update confidence if new data has higher confidence
        new_confidence = new_data.get('confidence', 0)
        if new_confidence > (existing_tool.confidence_score or 0):
            existing_tool.confidence_score = new_confidence
        
        # Update canonical URL and company name
        if new_data.get('canonical_url'):
            existing_tool.canonical_url = new_data['canonical_url']
        if new_data.get('company_name'):
            existing_tool.company_name = new_data['company_name']
        
        # Update description if new one is more detailed
        new_desc = new_data.get('description', '').strip()
        if len(new_desc) > len(existing_tool.description or ''):
            existing_tool.description = new_desc
        
        # Update features (merge them)
        existing_features = set((existing_tool.features or '').split(', '))
        new_features = set(new_data.get('features', '').split(', '))
        combined_features = existing_features.union(new_features)
        if combined_features:
            existing_tool.features = ', '.join(filter(None, combined_features))
        
        existing_tool.updated_at = datetime.utcnow()
    
    async def discover_from_ai_directories(self, target_tools: int = 200) -> Dict[str, Any]:
        """Discover tools from AI-specific directories mentioned in PDF"""
        
        results = {
            "discovery_id": f"ai_directories_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_discovered": 0,
            "total_saved": 0,
            "sources_processed": 0,
            "source_results": {},
            "processing_mode": "ai_directories_focus"
        }
        
        print(f"🤖 AI DIRECTORIES DISCOVERY")
        print(f"🎯 Target: {target_tools} tools from AI-specific sources")
        
        db = SessionLocal()
        all_discovered_tools = []
        
        try:
            for source_name, source_config in self.ai_sources.items():
                if results["total_discovered"] >= target_tools:
                    break
                
                print(f"\n📡 Checking source: {source_name}")
                
                # Check source freshness
                freshness_check = self.check_source_freshness(db, source_name)
                
                if not freshness_check["should_scan"]:
                    print(f"  ⏭️  Skipping {source_name}: {freshness_check['reason']}")
                    continue
                
                print(f"  🔍 Scanning {source_name}: {freshness_check['reason']}")
                
                # Simulate AI directory discovery (in real implementation, would use AI prompts)
                try:
                    tools = await self._discover_from_ai_directory(source_name, source_config)
                    
                    if tools:
                        # Enhanced duplicate detection
                        dedup_result = self.enhanced_duplicate_detection(db, tools)
                        clean_tools = dedup_result["new_tools"]
                        
                        # Add confidence scoring based on source reliability
                        for tool in clean_tools:
                            if source_name in ["futurepedia", "theresanaiforthat"]:
                                tool["confidence"] = min(0.9, tool.get("confidence", 0.7) + 0.1)
                            else:
                                tool["confidence"] = tool.get("confidence", 0.8)
                        
                        all_discovered_tools.extend(clean_tools)
                        
                        # Update source tracking
                        self.update_source_tracking(db, source_name, len(clean_tools), source_config["url"])
                        
                        results["source_results"][source_name] = {
                            "tools_found": len(tools),
                            "duplicates_removed": dedup_result["duplicates_found"],
                            "new_tools": len(clean_tools),
                            "deduplication_rate": dedup_result["deduplication_rate"],
                            "success": True
                        }
                        
                        results["total_discovered"] += len(clean_tools)
                        results["sources_processed"] += 1
                        
                        print(f"  ✅ {source_name}: {len(tools)} found, {len(clean_tools)} new after dedup")
                    else:
                        print(f"  ⚠️  {source_name}: No tools found")
                        results["source_results"][source_name] = {
                            "error": "No tools found",
                            "success": False
                        }
                
                except Exception as e:
                    print(f"  ❌ {source_name} failed: {e}")
                    results["source_results"][source_name] = {
                        "error": str(e),
                        "success": False
                    }
                
                # Respectful delay between sources
                await asyncio.sleep(3)
        
        finally:
            # Save all discovered tools
            if all_discovered_tools:
                print(f"\n💾 Saving {len(all_discovered_tools)} new tools to database...")
                save_result = save_discovered_tools_with_deduplication(db, all_discovered_tools)
                results["total_saved"] = save_result.get("saved", 0)
                results["database_result"] = save_result
            
            db.close()
        
        results["end_time"] = datetime.utcnow().isoformat()
        
        print(f"\n🎊 AI DIRECTORIES DISCOVERY COMPLETE!")
        print(f"📈 RESULTS:")
        print(f"   • Sources processed: {results['sources_processed']}")
        print(f"   • Tools discovered: {results['total_discovered']}")
        print(f"   • Tools saved: {results['total_saved']}")
        
        return results
    
    async def _discover_from_ai_directory(self, source_name: str, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover tools from a specific AI directory using AI prompts"""
        
        # This would use the agent service to scrape/discover tools
        # For now, simulating with enhanced prompts for AI tools
        from app.services.agent_service import agent_service
        
        target_count = source_config.get("tools_per_check", 50)
        
        # Enhanced prompts for AI-specific discovery
        ai_directory_prompts = {
            "theresanaiforthat": f"""CRITICAL: Return ONLY valid JSON array.

Find {target_count} REAL AI tools from "There's An AI For That" directory.

Focus on:
- Recently added AI tools (2024-2025)
- Tools with clear AI/ML capabilities
- Variety across categories (writing, image, video, audio, coding, business)
- Include both popular and emerging tools

Requirements:
- Must be real tools with working websites
- AI/ML as core functionality
- Mix of pricing models

Return JSON array:
[
  {{
    "name": "Tool Name",
    "website": "https://website.com",
    "description": "What this AI tool does",
    "tool_type": "ai_writing_tools|ai_image_generation|ai_video_tools|ai_audio_tools|ai_coding_tools|ai_data_analysis|ai_marketing_tools",
    "category": "Specific AI Category",
    "pricing": "Free|Freemium|Paid|Enterprise",
    "features": "AI feature1, AI feature2, AI feature3",
    "confidence": 0.9
  }}
]

Focus on AI tools only.""",
            
            "futurepedia": f"""CRITICAL: Return ONLY valid JSON array.

Find {target_count} AI tools from Futurepedia directory.

Categories to cover:
- AI Writing & Content
- AI Image & Art Generation  
- AI Video & Animation
- AI Audio & Music
- AI Code & Development
- AI Business & Productivity
- AI Research & Analysis

Requirements:
- Real AI tools with working websites
- Recently featured or trending tools preferred
- Include ratings/popularity indicators if available

Return JSON format:
[
  {{
    "name": "AI Tool Name",
    "website": "https://website.com", 
    "description": "AI tool description",
    "tool_type": "ai_category",
    "category": "Subcategory",
    "pricing": "Pricing model",
    "features": "Key AI features",
    "confidence": 0.85
  }}
]""",
            
            "aitools_fyi": f"""CRITICAL: Return ONLY valid JSON array.

Find {target_count} AI tools from aitools.fyi directory.

Focus areas:
- Latest AI tool launches
- AI productivity tools
- AI creative tools
- AI developer tools
- AI marketing tools
- Emerging AI startups

Return only real, working AI tools in JSON format.""",
            
            "toolify_ai": f"""CRITICAL: Return ONLY valid JSON array.

Find {target_count} AI tools from toolify.ai directory.

Priorities:
- High-rated AI tools
- Recently added AI tools
- AI tools across different industries
- Both free and premium AI tools

JSON format required with real tool data."""
        }
        
        prompt = ai_directory_prompts.get(source_name, f"Find {target_count} AI tools from {source_name}")
        
        try:
            # Get AI response
            ai_response = agent_service.send(prompt, block=True, timeout=120)
            
            # Parse tools from response
            from app.services.chat_service import parse_tools_from_response
            tools = parse_tools_from_response(ai_response)
            
            # Filter for AI-specific tools only
            ai_tools = []
            for tool in tools:
                if self._is_ai_tool(tool):
                    ai_tools.append(tool)
            
            return ai_tools
            
        except Exception as e:
            print(f"Error discovering from {source_name}: {e}")
            return []
    
    def _is_ai_tool(self, tool: Dict[str, Any]) -> bool:
        """Check if a tool is AI-related based on its description and features"""
        
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml', 'neural',
            'gpt', 'chatbot', 'automation', 'generated', 'smart', 'intelligent',
            'nlp', 'computer vision', 'deep learning', 'algorithm'
        ]
        
        text_to_check = f"{tool.get('name', '')} {tool.get('description', '')} {tool.get('features', '')}".lower()
        
        return any(keyword in text_to_check for keyword in ai_keywords)
    
    async def run_smart_discovery_pipeline(self, target_tools: int = 500) -> Dict[str, Any]:
        """Smart discovery pipeline implementing PDF logic"""
        
        results = {
            "pipeline_id": f"smart_discovery_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_discovered": 0,
            "total_saved": 0,
            "phases": {}
        }
        
        print(f"🧠 SMART DISCOVERY PIPELINE")
        print(f"🎯 Target: {target_tools} tools")
        print(f"📋 Phases: AI Directories → API Sources → Quality Checks")
        
        # Phase 1: AI Directories (primary focus from PDF)
        print(f"\n🤖 PHASE 1: AI-Specific Directories")
        ai_result = await self.discover_from_ai_directories(target_tools // 2)
        results["phases"]["ai_directories"] = ai_result
        results["total_discovered"] += ai_result["total_discovered"]
        results["total_saved"] += ai_result["total_saved"]
        
        # Phase 2: Enhanced API Discovery (if still need more tools)
        remaining_tools = target_tools - results["total_discovered"]
        if remaining_tools > 0:
            print(f"\n🔗 PHASE 2: Enhanced API Sources ({remaining_tools} more needed)")
            from app.services.real_apis_service import unified_apis_service
            api_result = unified_apis_service.run_sync_discover_no_auth_apis(remaining_tools)
            results["phases"]["api_sources"] = api_result
            results["total_saved"] += api_result.get("total_saved", 0)
        
        # Phase 3: Health Checks on new tools
        print(f"\n🏥 PHASE 3: Health Checks on New Tools")
        health_result = await self._run_health_checks_on_recent_tools()
        results["phases"]["health_checks"] = health_result
        
        results["end_time"] = datetime.utcnow().isoformat()
        
        print(f"\n🎊 SMART DISCOVERY PIPELINE COMPLETE!")
        print(f"📈 FINAL RESULTS:")
        print(f"   • Total tools discovered: {results['total_discovered']}")
        print(f"   • Total tools saved: {results['total_saved']}")
        print(f"   • Phases completed: {len(results['phases'])}")
        
        return results
    
    async def _run_health_checks_on_recent_tools(self, hours_back: int = 24) -> Dict[str, Any]:
        """Run health checks on recently discovered tools"""
        
        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            recent_tools = db.query(DiscoveredTool).filter(
                and_(
                    DiscoveredTool.created_at >= cutoff_time,
                    DiscoveredTool.website.isnot(None),
                    DiscoveredTool.website != ""
                )
            ).limit(100).all()
            
            if not recent_tools:
                return {"message": "No recent tools to check"}
            
            print(f"  🔍 Running health checks on {len(recent_tools)} recent tools...")
            
            # Run health checks
            health_results = await self.health_checker.run_health_checks_batch(recent_tools)
            
            # Update database
            stats = self.health_checker.update_tool_health_status(db, health_results)
            
            return {
                "tools_checked": len(recent_tools),
                "healthy": stats["healthy"],
                "unhealthy": stats["unhealthy"],
                "confidence_adjustments": stats["confidence_adjustments"]
            }
            
        finally:
            db.close()
    
    def sync_run_smart_discovery_pipeline(self, target_tools: int = 500) -> Dict[str, Any]:
        """Synchronous wrapper for FastAPI"""
        return asyncio.run(self.run_smart_discovery_pipeline(target_tools))
    
    def sync_discover_from_ai_directories(self, target_tools: int = 200) -> Dict[str, Any]:
        """Synchronous wrapper for AI directories discovery"""
        return asyncio.run(self.discover_from_ai_directories(target_tools))

# Global service instance
enhanced_discovery_service = EnhancedDiscoveryService()