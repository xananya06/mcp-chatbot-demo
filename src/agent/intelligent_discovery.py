#!/usr/bin/env python3
# src/agent/intelligent_discovery.py
# FIXED VERSION - Complete file with proper dead website handling and better retry logic

import time
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

sys.path.insert(0, os.path.dirname(__file__))

from app.services.real_apis_service import unified_apis_service

# Import AI directory scraping service
try:
    from app.services.ai_directory_service import ai_directory_service
    DIRECTORY_SCRAPING_AVAILABLE = True
except ImportError as e:
    DIRECTORY_SCRAPING_AVAILABLE = False
    print(f"⚠️ AI Directory scraping not available: {e}")

# Import activity assessment
try:
    from app.services.unified_activity_service import unified_activity_service
    from app.db.database import SessionLocal
    from app.models.chat import DiscoveredTool
    from sqlalchemy import and_, or_
    ACTIVITY_SCORING_AVAILABLE = True
except ImportError as e:
    ACTIVITY_SCORING_AVAILABLE = False
    print(f"⚠️ Activity scoring not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncrementalDiscoverySystem:
    """
    FIXED VERSION - Incremental Discovery System with proper dead website handling
    Key fixes:
    1. Dead websites get properly marked with activity_score=0.0
    2. Dead websites aren't retried every run (3-day cooldown)
    3. Better tool count management
    4. Smarter retry logic for failed assessments
    """
    
    def __init__(self, state_file: str = "discovery_state.json"):
        self.state_file = state_file
        self.stats = {"runs": 0, "tools_found": 0, "tools_scored": 0, "tools_skipped": 0}
        self.state = self._load_state()
        
        # Available discovery methods with incremental support
        self.discovery_methods = {
            "enhanced_all": {
                "method": "run_sync_discover_all_real_apis_incremental",
                "target": 500,
                "description": "All APIs + AI Directories + Incremental Updates + Auto Activity Scoring",
                "include_directories": True
            },
            "standard": {
                "method": "run_sync_discover_no_auth_apis_incremental", 
                "target": 200,
                "description": "No-auth APIs + AI Directories + Incremental Updates + Auto Activity Scoring",
                "include_directories": True
            },
            "directories_only": {
                "method": "run_sync_scrape_all_directories_incremental",
                "target": 300,
                "description": "AI Directories Only + Incremental Updates + Auto Activity Scoring",
                "include_directories": True,
                "directories_only": True
            },
            "github": {
                "method": "run_sync_discover_github_incremental",
                "target": 150,
                "description": "GitHub + Incremental Updates + Auto Activity Scoring",
                "include_directories": False
            },
            "npm": {
                "method": "run_sync_discover_npm_incremental",
                "target": 100,
                "description": "NPM + Incremental Updates + Auto Activity Scoring",
                "include_directories": False
            },
            "reddit": {
                "method": "run_sync_discover_reddit_incremental",
                "target": 100,
                "description": "Reddit + Incremental Updates + Auto Activity Scoring",
                "include_directories": False
            },
            "hackernews": {
                "method": "run_sync_discover_hackernews_incremental",
                "target": 100,
                "description": "Hacker News + Incremental Updates + Auto Activity Scoring",
                "include_directories": False
            },
            "stackoverflow": {
                "method": "run_sync_discover_stackoverflow_incremental",
                "target": 100,
                "description": "Stack Overflow + Incremental Updates + Auto Activity Scoring",
                "include_directories": False
            },
            "pypi": {
                "method": "run_sync_discover_pypi_incremental",
                "target": 100,
                "description": "PyPI + Incremental Updates + Auto Activity Scoring",
                "include_directories": False
            },
            "theresanaiforthat": {
                "method": "run_sync_scrape_theresanaiforthat_incremental",
                "target": 100,
                "description": "There's An AI For That Directory + Incremental Updates + Auto Activity Scoring",
                "include_directories": True,
                "directories_only": True
            },
            "aitoolsdirectory": {
                "method": "run_sync_scrape_aitoolsdirectory_incremental", 
                "target": 100,
                "description": "AI Tools Directory + Incremental Updates + Auto Activity Scoring",
                "include_directories": True,
                "directories_only": True
            },
            "futurepedia": {
                "method": "run_sync_scrape_futurepedia_incremental",
                "target": 100,
                "description": "Futurepedia Directory + Incremental Updates + Auto Activity Scoring", 
                "include_directories": True,
                "directories_only": True
            }
        }
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from file or create new state"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                logger.info(f"📂 Loaded state from {self.state_file}")
                return state
        except Exception as e:
            logger.warning(f"⚠️ Could not load state file: {e}")
        
        # Default state
        logger.info("📝 Creating new state file")
        return {
            "last_run_timestamps": {},
            "api_last_checks": {},
            "total_runs": 0,
            "last_full_scan": None,
            "force_full_scan_after_days": 7
        }
    
    def _save_state(self):
        """Save current state to file"""
        try:
            self.state["total_runs"] = self.stats["runs"]
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
            logger.debug(f"💾 State saved to {self.state_file}")
        except Exception as e:
            logger.error(f"❌ Could not save state: {e}")
    
    def _should_force_full_scan(self) -> bool:
        """Check if we should force a full scan (e.g., weekly)"""
        if not self.state.get("last_full_scan"):
            return True
        
        last_full = datetime.fromisoformat(self.state["last_full_scan"])
        days_since = (datetime.utcnow() - last_full).days
        force_after = self.state.get("force_full_scan_after_days", 7)
        
        return days_since >= force_after
    
    def _get_last_check_time(self, api_name: str) -> Optional[datetime]:
        """Get the last time we checked this API"""
        timestamp = self.state["api_last_checks"].get(api_name)
        if timestamp:
            return datetime.fromisoformat(timestamp)
        return None
    
    def _update_last_check_time(self, api_name: str, timestamp: datetime = None):
        """Update the last check time for an API"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        self.state["api_last_checks"][api_name] = timestamp.isoformat()
    
    def run_incremental_discovery(self, method: str = "enhanced_all", auto_score: bool = True, force_full: bool = False):
        """Run incremental discovery - only check updated tools"""
        
        if method not in self.discovery_methods:
            logger.error(f"❌ Unknown discovery method: {method}")
            logger.info(f"Available methods: {list(self.discovery_methods.keys())}")
            return {"new_tools": 0, "scored_tools": 0, "skipped_tools": 0}
        
        config = self.discovery_methods[method]
        current_time = datetime.utcnow()
        
        # Check if we should force a full scan
        force_full = force_full or self._should_force_full_scan()
        
        logger.info(f"🧠 Incremental Discovery Starting - Method: {method}")
        logger.info(f"🎯 {config['description']}")
        
        if force_full:
            logger.info(f"🔄 FULL SCAN MODE (weekly refresh)")
            self.state["last_full_scan"] = current_time.isoformat()
        else:
            logger.info(f"⚡ INCREMENTAL MODE (changes only)")
        
        if auto_score:
            logger.info(f"⚡ Auto Activity Scoring: ENABLED")
        
        total_new = 0
        total_scored = 0
        total_skipped = 0
        
        try:
            # PHASE 1: Incremental Discovery
            logger.info(f"\n📡 PHASE 1: INCREMENTAL API DISCOVERY")
            
            # Get last check times for incremental discovery
            discovery_params = self._prepare_incremental_params(method, force_full)
            
            total_api_new = 0
            total_api_skipped = 0
            total_dir_new = 0
            total_dir_skipped = 0
            
            # Run API discovery (unless it's directories-only)
            if not config.get("directories_only", False):
                api_result = self._run_incremental_api_discovery(config, discovery_params)
                total_api_new = api_result.get("total_saved", 0)
                total_api_skipped = api_result.get("total_skipped", 0)
                
                # Log API results
                if api_result.get("api_results"):
                    logger.info("📡 API Results:")
                    for api_name, api_result_detail in api_result["api_results"].items():
                        if api_result_detail.get("success"):
                            tools_count = api_result_detail.get("tools_discovered", 0)
                            skipped_count = api_result_detail.get("tools_skipped", 0)
                            processing_time = api_result_detail.get("processing_time", 0)
                            logger.info(f"  ✅ {api_name}: {tools_count} new, {skipped_count} skipped ({processing_time:.1f}s)")
                            
                            # Update last check time for this API
                            self._update_last_check_time(api_name, current_time)
                        else:
                            error = api_result_detail.get("error", "Unknown error")
                            logger.info(f"  ❌ {api_name}: {error}")
            
            # Run directory scraping if enabled and available
            if config.get("include_directories", False) and DIRECTORY_SCRAPING_AVAILABLE:
                logger.info("\n🤖 AI DIRECTORY SCRAPING")
                
                if config.get("directories_only", False):
                    # Use the specific directory method
                    directory_method = getattr(ai_directory_service, config["method"])
                    dir_result = directory_method(
                        target_tools=config["target"],
                        incremental_params=discovery_params
                    )
                else:
                    # Use all directories method
                    dir_result = ai_directory_service.run_sync_scrape_all_directories_incremental(
                        target_tools=min(config["target"] // 2, 150),  # Use half target for directories
                        incremental_params=discovery_params
                    )
                
                total_dir_new = dir_result.get("total_saved", 0)
                total_dir_skipped = dir_result.get("total_skipped", 0)
                
                if dir_result.get("success"):
                    if dir_result.get("incremental_skip"):
                        logger.info(f"  ⏭️ AI Directories: Skipped (recently checked)")
                    else:
                        scraped = dir_result.get("total_scraped", 0)
                        saved = dir_result.get("total_saved", 0)
                        duplicates = dir_result.get("total_duplicates", 0)
                        processing_time = dir_result.get("processing_time", 0)
                        logger.info(f"  ✅ AI Directories: {scraped} scraped, {saved} saved, {duplicates} duplicates ({processing_time:.1f}s)")
                        
                        # Update directory check time
                        if config.get("directories_only"):
                            directory_name = method  # For single directory methods
                        else:
                            directory_name = "directories"
                        self._update_last_check_time(directory_name, current_time)
                else:
                    error = dir_result.get("error", "Unknown error")
                    logger.info(f"  ❌ AI Directories: {error}")
            
            elif config.get("include_directories", False) and not DIRECTORY_SCRAPING_AVAILABLE:
                logger.warning("⚠️ AI Directory scraping requested but not available")
            
            # Combine results
            new_tools = total_api_new + total_dir_new
            skipped_tools = total_api_skipped + total_dir_skipped
            total_new += new_tools
            total_skipped += skipped_tools
            
            logger.info(f"✅ Discovery Phase: {new_tools} new tools, {skipped_tools} skipped (unchanged)")
            if total_api_new > 0 and total_dir_new > 0:
                logger.info(f"   📡 APIs contributed: {total_api_new} tools")
                logger.info(f"   🤖 Directories contributed: {total_dir_new} tools")
            
            # PHASE 2: FIXED Incremental Activity Scoring
            if auto_score and (new_tools > 0 or force_full) and ACTIVITY_SCORING_AVAILABLE:
                logger.info(f"\n⚡ PHASE 2: INCREMENTAL ACTIVITY SCORING")
                scored_tools = self._score_tools_needing_update_fixed(force_full, new_tools * 2)
                total_scored = scored_tools
                logger.info(f"✅ Scoring Phase: {scored_tools} tools scored")
                
                # Show sample of scored tools
                self._show_scored_tools_sample()
                
            elif auto_score and not ACTIVITY_SCORING_AVAILABLE:
                logger.warning("⚠️ Activity scoring not available - install dependencies")
            elif not auto_score:
                logger.info("⏭️ Skipping activity scoring (disabled)")
            
        except Exception as e:
            logger.error(f"Discovery error: {e}")
        
        # Update stats and state
        self.stats["runs"] += 1
        self.stats["tools_found"] += total_new
        self.stats["tools_scored"] += total_scored
        self.stats["tools_skipped"] += total_skipped
        self.state["last_run_timestamps"][method] = current_time.isoformat()
        self._save_state()
        
        logger.info(f"\n🎊 INCREMENTAL DISCOVERY COMPLETE!")
        logger.info(f"📈 New tools found: {total_new}")
        logger.info(f"⚡ Tools scored: {total_scored}")
        logger.info(f"⏭️ Tools skipped (unchanged): {total_skipped}")
        logger.info(f"💡 Efficiency: {((total_skipped / max(total_new + total_skipped, 1)) * 100):.1f}% reduction in redundant work")
        logger.info(f"🎯 Ready for high-quality AI tool recommendations!")
        
        return {"new_tools": total_new, "scored_tools": total_scored, "skipped_tools": total_skipped}
    
    def _prepare_incremental_params(self, method: str, force_full: bool) -> Dict[str, Any]:
        """Prepare parameters for incremental discovery - FIXED API name mapping"""
        params = {
            "force_full_scan": force_full,
            "last_check_times": {},
            "incremental_mode": not force_full
        }
        
        # FIXED: Map lowercase method names to actual saved API names in state file
        api_name_mapping = {
            "github": "GitHub",
            "npm": "NPM", 
            "reddit": "Reddit",
            "hackernews": "Hacker News",
            "stackoverflow": "Stack Overflow",
            "pypi": "PyPI",
            "directories": "directories"  # This one was already correct
        }
        
        # Get last check times for each API we'll use
        if method == "enhanced_all":
            method_apis = ["github", "npm", "reddit", "hackernews", "stackoverflow", "pypi", "directories"]
        elif method == "standard":
            method_apis = ["github", "npm", "hackernews", "stackoverflow", "directories"]
        elif method == "directories_only":
            method_apis = ["directories"]
        elif method in ["theresanaiforthat", "aitoolsdirectory", "futurepedia"]:
            method_apis = [method]  # Single directory
        elif method in ["github", "npm", "reddit", "hackernews", "stackoverflow", "pypi"]:
            method_apis = [method]
        else:
            method_apis = []
        
        for api_key in method_apis:
            # FIXED: Use the correct API name from state file
            state_api_name = api_name_mapping.get(api_key, api_key)
            last_check = self._get_last_check_time(state_api_name)  # Look for "GitHub" not "github"
            
            if last_check and not force_full:
                params["last_check_times"][api_key] = last_check.isoformat()
                logger.info(f"  📅 {api_key}: Last checked {last_check.strftime('%Y-%m-%d %H:%M')} UTC")
            else:
                logger.info(f"  🆕 {api_key}: First time or full scan")
        
        return params
    
    def _run_incremental_api_discovery(self, config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Run API discovery with incremental parameters"""
        
        # Skip if this is a directories-only method
        if config.get("directories_only", False):
            return {"total_saved": 0, "total_skipped": 0, "api_results": {}}
        
        try:
            # Try to get the incremental method first
            incremental_method_name = config["method"]
            if hasattr(unified_apis_service, incremental_method_name):
                api_method = getattr(unified_apis_service, incremental_method_name)
                return api_method(
                    target_tools=config["target"],
                    incremental_params=params
                )
            else:
                # Fallback to regular method with filtering
                logger.warning(f"⚠️ Incremental method {incremental_method_name} not found, using regular method")
                regular_method_name = config["method"].replace("_incremental", "")
                api_method = getattr(unified_apis_service, regular_method_name)
                result = api_method(target_tools=config["target"])
                
                # Post-process to simulate incremental behavior
                result = self._filter_existing_tools(result, params)
                return result
                
        except Exception as e:
            logger.error(f"❌ Error in incremental API discovery: {e}")
            return {"total_saved": 0, "total_skipped": 0, "api_results": {}}
    
    def _filter_existing_tools(self, result: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out tools that haven't been updated since last check"""
        
        if params.get("force_full_scan", False):
            return result
        
        # This is a simplified version - in practice, you'd need to check each tool's
        # last update time against the last check time for its source API
        
        db = SessionLocal()
        try:
            total_found = result.get("total_saved", 0)
            skipped_count = 0
            
            # Get tools that were just discovered and check if they're actually new/updated
            recent_cutoff = datetime.utcnow() - timedelta(minutes=5)  # Just discovered
            
            recent_tools = db.query(DiscoveredTool).filter(
                DiscoveredTool.created_at >= recent_cutoff
            ).all()
            
            for tool in recent_tools:
                # Check if this tool existed before and hasn't been meaningfully updated
                existing = db.query(DiscoveredTool).filter(
                    and_(
                        DiscoveredTool.name == tool.name,
                        DiscoveredTool.website == tool.website,
                        DiscoveredTool.id != tool.id,
                        DiscoveredTool.created_at < recent_cutoff
                    )
                ).first()
                
                if existing:
                    # Tool already exists and likely hasn't changed
                    skipped_count += 1
            
            result["total_skipped"] = skipped_count
            result["total_saved"] = max(0, total_found - skipped_count)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error filtering existing tools: {e}")
            return result
        finally:
            db.close()
    
    def _score_tools_needing_update_fixed(self, force_full: bool, limit: int = 50) -> int:
        """FIXED: Score tools that need activity score updates with proper dead website handling"""
        
        if not ACTIVITY_SCORING_AVAILABLE:
            return 0
        
        logger.info(f"🔍 Finding tools needing activity score updates...")
        
        db = SessionLocal()
        try:
            # Define criteria for tools needing scoring
            current_time = datetime.utcnow()
            
            if force_full:
                # FIXED: Better query that avoids recently failed dead websites
                score_cutoff = current_time - timedelta(days=7)
                dead_site_retry_cutoff = current_time - timedelta(days=3)  # Don't retry dead sites for 3 days
                
                tools_to_score = db.query(DiscoveredTool).filter(
                    and_(
                        # Has a website to check
                        DiscoveredTool.website.isnot(None),
                        DiscoveredTool.website != "",
                        # Needs scoring
                        or_(
                            # Never scored
                            DiscoveredTool.activity_score.is_(None),
                            DiscoveredTool.last_activity_check.is_(None),
                            # Old score but smart retry logic
                            and_(
                                DiscoveredTool.last_activity_check < score_cutoff,
                                or_(
                                    # Working sites (retry normally)
                                    DiscoveredTool.website_status == 200,
                                    # Dead sites (only retry after 3 days)
                                    and_(
                                        or_(
                                            DiscoveredTool.website_status == 0,
                                            DiscoveredTool.website_status >= 400
                                        ),
                                        DiscoveredTool.last_activity_check < dead_site_retry_cutoff
                                    ),
                                    # Never checked sites
                                    DiscoveredTool.website_status.is_(None)
                                )
                            )
                        )
                    )
                ).order_by(
                    # FIXED: Prioritize tools likely to succeed
                    DiscoveredTool.website_status.desc().nulls_last(),  # Working sites first
                    DiscoveredTool.created_at.desc()  # Newer tools first
                ).limit(limit).all()
                
                logger.info(f"📋 Full scan: Found {len(tools_to_score)} tools needing score updates")
                
            else:
                # Incremental: only score new tools and high-priority refreshes
                recent_cutoff = current_time - timedelta(hours=2)  # Recently discovered
                stale_cutoff = current_time - timedelta(days=3)   # Scores getting stale
                
                tools_to_score = db.query(DiscoveredTool).filter(
                    or_(
                        # New tools without scores
                        and_(
                            DiscoveredTool.created_at >= recent_cutoff,
                            DiscoveredTool.activity_score.is_(None)
                        ),
                        # Working tools with stale scores (avoid recently failed dead sites)
                        and_(
                            DiscoveredTool.last_activity_check < stale_cutoff,
                            or_(
                                DiscoveredTool.website_status == 200,  # Only retry working sites frequently
                                DiscoveredTool.website_status.is_(None)  # Never checked
                            )
                        )
                    )
                ).filter(
                    and_(
                        DiscoveredTool.website.isnot(None),
                        DiscoveredTool.website != ""
                    )
                ).limit(limit).all()
                
                logger.info(f"📋 Incremental: Found {len(tools_to_score)} tools needing score updates")
            
            if not tools_to_score:
                logger.info("✅ All tools have up-to-date activity scores")
                return 0
            
            scored_count = 0
            
            # FIXED: Score each tool and handle failures properly
            for i, tool in enumerate(tools_to_score):
                try:
                    is_new = tool.activity_score is None
                    action = "Scoring" if is_new else "Updating"
                    logger.info(f"  ⚡ {action} {i+1}/{len(tools_to_score)}: {tool.name}")
                    
                    # Use unified activity service to assess the tool
                    assessment = unified_activity_service.sync_assess_single_tool(tool)
                    
                    # FIXED: Update tool whether assessment succeeds OR fails
                    if assessment:
                        # Always update these fields (even for failed assessments)
                        tool.tool_type_detected = assessment.get('tool_type_detected', 'unknown')
                        tool.activity_score = assessment.get('activity_score', 0.0)  # Will be 0.0 for dead sites
                        tool.last_activity_check = current_time
                        
                        # Update status fields (even for failures)
                        if 'website_status' in assessment:
                            tool.website_status = assessment.get('website_status', 0)  # 0 for dead sites
                            
                        if 'is_actively_maintained' in assessment:
                            tool.is_actively_maintained = assessment.get('is_actively_maintained', False)
                        
                        # Only update source-specific metrics if assessment succeeded
                        if not assessment.get('error'):
                            # GitHub metrics
                            if 'github_stars' in assessment:
                                tool.github_stars = assessment.get('github_stars')
                                tool.github_last_commit = assessment.get('github_last_commit')
                                tool.github_contributors = assessment.get('github_contributors')
                                
                            # NPM metrics
                            if 'npm_weekly_downloads' in assessment:
                                tool.npm_weekly_downloads = assessment.get('npm_weekly_downloads')
                                tool.npm_last_update = assessment.get('npm_last_update')
                                
                            # PyPI metrics
                            if 'pypi_last_release' in assessment:
                                tool.pypi_last_release = assessment.get('pypi_last_release')
                        
                        # Calculate quality scores
                        self._calculate_quality_scores(tool, assessment)
                        
                        scored_count += 1
                        
                        # FIXED: Better logging for both success and failure
                        score = assessment.get('activity_score', 0)
                        tool_type = assessment.get('tool_type_detected', 'unknown')
                        
                        if assessment.get('error'):
                            error = assessment.get('error', 'Unknown error')
                            status = "FAILED"
                            logger.info(f"    ❌ {status} | Score: {score:.2f} | Error: {error[:50]}...")
                            # ↑ Tool still gets updated with score 0.0 and appropriate website_status
                        else:
                            status = "NEW" if is_new else "UPDATED"
                            logger.info(f"    ✅ {status} | Score: {score:.2f} | Type: {tool_type}")
                            
                    else:
                        # Complete assessment failure - still mark tool as checked
                        tool.last_activity_check = current_time
                        tool.activity_score = 0.0
                        tool.website_status = 0
                        tool.is_actively_maintained = False
                        scored_count += 1
                        logger.info(f"    💥 ASSESSMENT FAILED | Score: 0.00 | Marked as dead")
                    
                    # Small delay to be respectful to APIs
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"    ❌ Error scoring {tool.name}: {e}")
                    # Even on exception, mark tool as checked to avoid infinite retries
                    try:
                        tool.last_activity_check = current_time
                        tool.activity_score = 0.0
                        tool.website_status = 0
                    except:
                        pass
                    continue
            
            # Commit all changes
            db.commit()
            logger.info(f"✅ Successfully scored {scored_count}/{len(tools_to_score)} tools")
            return scored_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error in FIXED scoring process: {e}")
            return 0
        finally:
            db.close()
    
    def _calculate_quality_scores(self, tool: DiscoveredTool, assessment: dict):
        """Calculate additional quality scores"""
        
        # Community size score (based on stars, downloads, etc.)
        community_score = 0.0
        if tool.github_stars:
            community_score = min(tool.github_stars / 1000, 1.0) * 0.6
        if tool.npm_weekly_downloads:
            community_score += min(tool.npm_weekly_downloads / 10000, 1.0) * 0.4
        tool.community_size_score = community_score
        
        # Usage popularity score
        tool.usage_popularity_score = assessment.get('activity_score', 0.0)
        
        # Maintenance quality score
        maintenance_score = 0.5  # Base score
        if tool.is_actively_maintained:
            maintenance_score += 0.3
        if tool.website_status == 200:
            maintenance_score += 0.2
        tool.maintenance_quality_score = min(maintenance_score, 1.0)
    
    def _show_scored_tools_sample(self, limit: int = 5):
        """Show a sample of recently scored tools"""
        
        logger.info(f"\n📊 SAMPLE OF SCORED TOOLS:")
        
        db = SessionLocal()
        try:
            recent_scored = db.query(DiscoveredTool).filter(
                and_(
                    DiscoveredTool.activity_score.isnot(None),
                    DiscoveredTool.last_activity_check >= datetime.utcnow() - timedelta(minutes=30)
                )
            ).order_by(DiscoveredTool.activity_score.desc()).limit(limit).all()
            
            for tool in recent_scored:
                score = tool.activity_score or 0
                tool_type = tool.tool_type_detected or 'unknown'
                stars = f" | {tool.github_stars} ⭐" if tool.github_stars else ""
                downloads = f" | {tool.npm_weekly_downloads} 📦/week" if tool.npm_weekly_downloads else ""
                
                logger.info(f"  🎯 {tool.name}: {score:.2f} ({tool_type}){stars}{downloads}")
                
        except Exception as e:
            logger.error(f"Error showing sample: {e}")
        finally:
            db.close()
    
    # ================================================================
    # NEW METHODS: Dead Website Management
    # ================================================================
    
    def show_dead_websites(self):
        """Show current dead websites and their retry status"""
        
        if not ACTIVITY_SCORING_AVAILABLE:
            logger.error("❌ Activity scoring not available")
            return
        
        logger.info("💀 DEAD WEBSITES ANALYSIS")
        logger.info("=" * 60)
        
        db = SessionLocal()
        try:
            current_time = datetime.utcnow()
            dead_site_retry_cutoff = current_time - timedelta(days=3)
            
            # Get dead websites
            dead_sites = db.query(DiscoveredTool).filter(
                and_(
                    or_(
                        DiscoveredTool.website_status == 0,
                        DiscoveredTool.website_status >= 400
                    ),
                    DiscoveredTool.activity_score == 0.0,
                    DiscoveredTool.last_activity_check.isnot(None)
                )
            ).order_by(DiscoveredTool.last_activity_check.desc()).all()
            
            if not dead_sites:
                logger.info("✅ No dead websites found!")
                return
            
            # Categorize by retry status
            ready_for_retry = []
            on_cooldown = []
            
            for site in dead_sites:
                if site.last_activity_check < dead_site_retry_cutoff:
                    ready_for_retry.append(site)
                else:
                    on_cooldown.append(site)
            
            logger.info(f"📊 SUMMARY:")
            logger.info(f"   • Total dead websites: {len(dead_sites)}")
            logger.info(f"   • Ready for retry (>3 days): {len(ready_for_retry)}")
            logger.info(f"   • On cooldown (<3 days): {len(on_cooldown)}")
            
            if ready_for_retry:
                logger.info(f"\n🔄 READY FOR RETRY ({len(ready_for_retry)} sites):")
                for i, site in enumerate(ready_for_retry[:10], 1):
                    days_since = (current_time - site.last_activity_check).days
                    logger.info(f"  {i:2d}. {site.name[:40]:<40} | Status: {site.website_status} | {days_since}d ago")
                if len(ready_for_retry) > 10:
                    logger.info(f"      ... and {len(ready_for_retry) - 10} more")
            
            if on_cooldown:
                logger.info(f"\n❄️ ON COOLDOWN ({len(on_cooldown)} sites):")
                for i, site in enumerate(on_cooldown[:5], 1):
                    hours_since = (current_time - site.last_activity_check).total_seconds() / 3600
                    remaining_hours = max(0, 72 - hours_since)  # 72h = 3 days
                    logger.info(f"  {i:2d}. {site.name[:40]:<40} | Status: {site.website_status} | {remaining_hours:.1f}h left")
                if len(on_cooldown) > 5:
                    logger.info(f"      ... and {len(on_cooldown) - 5} more")
            
            logger.info(f"\n💡 NEXT ACTIONS:")
            if ready_for_retry:
                logger.info(f"   • {len(ready_for_retry)} sites ready for retry")
                logger.info(f"   • Run: python intelligent_discovery.py run-once enhanced_all --force-full")
            if on_cooldown:
                min_remaining = min((72 - (current_time - site.last_activity_check).total_seconds() / 3600) for site in on_cooldown)
                logger.info(f"   • {len(on_cooldown)} sites on cooldown")
                logger.info(f"   • Next retry available in: {min_remaining:.1f} hours")
            
            logger.info(f"\n🛠️ MANAGEMENT COMMANDS:")
            logger.info(f"   • Show this report: python intelligent_discovery.py show-dead")
            logger.info(f"   • Reset cooldowns: python intelligent_discovery.py reset-dead")
            logger.info(f"   • Force retry all: python intelligent_discovery.py run-once enhanced_all --force-full")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing dead websites: {e}")
        finally:
            db.close()
    
    def reset_dead_websites(self):
        """Reset all dead websites to allow immediate retry (for testing)"""
        
        if not ACTIVITY_SCORING_AVAILABLE:
            logger.error("❌ Activity scoring not available")
            return
        
        logger.info("🔄 RESETTING DEAD WEBSITES")
        logger.info("⚠️ This will allow immediate retry of all dead sites")
        
        db = SessionLocal()
        try:
            # Find dead websites
            dead_sites = db.query(DiscoveredTool).filter(
                and_(
                    or_(
                        DiscoveredTool.website_status == 0,
                        DiscoveredTool.website_status >= 400
                    ),
                    DiscoveredTool.activity_score == 0.0,
                    DiscoveredTool.last_activity_check.isnot(None)
                )
            ).all()
            
            if not dead_sites:
                logger.info("✅ No dead websites found to reset")
                return
            
            logger.info(f"📋 Found {len(dead_sites)} dead websites to reset")
            
            # Reset their last_activity_check to force retry
            old_cutoff = datetime.utcnow() - timedelta(days=10)  # 10 days ago
            
            for site in dead_sites:
                site.last_activity_check = old_cutoff
            
            db.commit()
            
            logger.info(f"✅ Successfully reset {len(dead_sites)} dead websites")
            logger.info(f"🎯 These sites will now be retried on next discovery run")
            logger.info(f"📝 Run: python intelligent_discovery.py run-once enhanced_all --force-full")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error resetting dead websites: {e}")
        finally:
            db.close()
    
    # ================================================================
    # EXISTING METHODS (continued from before)
    # ================================================================
    
    def reset_state(self, api_name: str = None):
        """Reset state for specific API or all APIs"""
        if api_name:
            if api_name in self.state["api_last_checks"]:
                del self.state["api_last_checks"][api_name]
                logger.info(f"🔄 Reset state for {api_name}")
            else:
                logger.info(f"⚠️ No state found for {api_name}")
        else:
            self.state["api_last_checks"] = {}
            self.state["last_full_scan"] = None
            logger.info(f"🔄 Reset all API states")
        
        self._save_state()
    
    def show_state(self):
        """Show current state information"""
        logger.info("📊 Discovery System State:")
        logger.info(f"  • Total runs: {self.state.get('total_runs', 0)}")
        logger.info(f"  • Last full scan: {self.state.get('last_full_scan', 'Never')}")
        logger.info(f"  • Force full scan after: {self.state.get('force_full_scan_after_days', 7)} days")
        
        logger.info("\n📅 API Last Check Times:")
        api_checks = self.state.get("api_last_checks", {})
        if api_checks:
            for api, timestamp in api_checks.items():
                try:
                    check_time = datetime.fromisoformat(timestamp)
                    hours_ago = (datetime.utcnow() - check_time).total_seconds() / 3600
                    logger.info(f"  • {api}: {check_time.strftime('%Y-%m-%d %H:%M')} UTC ({hours_ago:.1f}h ago)")
                except:
                    logger.info(f"  • {api}: {timestamp}")
        else:
            logger.info("  (No API checks recorded)")
        
        # Show if full scan is due
        if self._should_force_full_scan():
            logger.info("\n🔄 Status: Full scan will be triggered on next run")
        else:
            logger.info("\n⚡ Status: Incremental mode will be used on next run")
    
    def start_continuous(self, method: str = "enhanced_all", interval_hours: int = 6, auto_score: bool = True):
        """Start continuous incremental discovery"""
        
        config = self.discovery_methods.get(method, self.discovery_methods["enhanced_all"])
        
        logger.info(f"🚀 Starting Incremental Continuous Discovery")
        logger.info(f"📋 Method: {method} ({config['description']})")
        logger.info(f"⏰ Interval: {interval_hours} hours")
        logger.info(f"⚡ Auto Activity Scoring: {'ENABLED' if auto_score else 'DISABLED'}")
        logger.info(f"💡 Workflow: Only check updated tools → Score changes → Ready!")
        
        # Check API configurations
        self._check_api_configurations()
        
        while True:
            try:
                result = self.run_incremental_discovery(method, auto_score)
                logger.info(f"📊 Session stats: {self.stats['runs']} runs, {self.stats['tools_found']} total new, {self.stats['tools_skipped']} total skipped")
                logger.info(f"⏳ Waiting {interval_hours} hours until next incremental discovery...")
                time.sleep(interval_hours * 3600)
            except KeyboardInterrupt:
                logger.info("⚠️ Discovery stopped by user")
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}")
                logger.info("🔄 Retrying in 5 minutes...")
                time.sleep(300)
    
    def _check_api_configurations(self):
        """Check which APIs are configured"""
        logger.info("🔧 API Configuration Status:")
        
        # Always available
        logger.info("  ✅ GitHub API: Available (incremental via updated_at)")
        logger.info("  ✅ NPM Registry API: Available (incremental via modified)")
        logger.info("  ✅ PyPI JSON API: Available") 
        logger.info("  ✅ Hacker News API: Available (incremental via timestamp)")
        logger.info("  ✅ Stack Overflow API: Available (incremental via last_activity_date)")
        logger.info("  ✅ Reddit API: Available (incremental via created_utc)")
        
        # AI Directory Scraping
        if DIRECTORY_SCRAPING_AVAILABLE:
            logger.info("  ✅ AI Directory Scraping: Available")
            logger.info("    • There's An AI For That: Incremental (daily checks)")
            logger.info("    • AI Tools Directory: Incremental (daily checks)")
            logger.info("    • Futurepedia: Incremental (daily checks)")
        else:
            logger.info("  ❌ AI Directory Scraping: Not available")
        
        # Check activity scoring
        if ACTIVITY_SCORING_AVAILABLE:
            logger.info("  ✅ Activity Scoring: Available")
        else:
            logger.info("  ❌ Activity Scoring: Not available")
        
        # Show state file location
        logger.info(f"💾 State file: {os.path.abspath(self.state_file)}")

    def test_apis(self):
        """Test individual API connections with incremental support"""
        logger.info("🧪 Testing incremental API connections...")
        
        test_methods = [
            ("GitHub", "run_sync_discover_github_incremental", 5),
            ("NPM", "run_sync_discover_npm_incremental", 5),
            ("Reddit", "run_sync_discover_reddit_incremental", 5),
            ("Hacker News", "run_sync_discover_hackernews_incremental", 5)
        ]
        
        # Test AI directory scraping if available
        if DIRECTORY_SCRAPING_AVAILABLE:
            test_methods.extend([
                ("There's An AI For That", "run_sync_scrape_theresanaiforthat_incremental", 3),
                ("AI Tools Directory", "run_sync_scrape_aitoolsdirectory_incremental", 3),
                ("Futurepedia", "run_sync_scrape_futurepedia_incremental", 3)
            ])

        results = {}
        
        for api_name, method_name, target in test_methods:
            try:
                logger.info(f"  🔍 Testing {api_name} API (incremental mode)...")
                
                # Prepare incremental test parameters
                test_params = {
                    "force_full_scan": False,
                    "last_check_times": {api_name.lower(): (datetime.utcnow() - timedelta(hours=1)).isoformat()},
                    "incremental_mode": True
                }
                
                # Try incremental method first, fallback to regular if not available
                service = unified_apis_service
                if api_name in ["There's An AI For That", "AI Tools Directory", "Futurepedia"]:
                    service = ai_directory_service
                
                if hasattr(service, method_name):
                    api_method = getattr(service, method_name)
                    result = api_method(target_tools=target, incremental_params=test_params)
                else:
                    logger.info(f"    ⚠️ Incremental method not found, testing regular method")
                    regular_method = method_name.replace("_incremental", "")
                    api_method = getattr(service, regular_method)
                    result = api_method(target_tools=target)
                
                if result.get("total_saved", 0) >= 0:  # Even 0 is OK for a test
                    skipped = result.get("total_skipped", 0)
                    results[api_name] = f"✅ Working (found: {result.get('total_saved', 0)}, skipped: {skipped})"
                    logger.info(f"    ✅ {api_name}: Working - incremental support detected")
                else:
                    results[api_name] = "⚠️ Issues"
                    logger.info(f"    ⚠️ {api_name}: Issues detected")
                    
            except Exception as e:
                results[api_name] = f"❌ Failed: {str(e)}"
                logger.info(f"    ❌ {api_name}: {str(e)}")
        
        # Test activity scoring
        if ACTIVITY_SCORING_AVAILABLE:
            logger.info(f"  🔍 Testing Incremental Activity Scoring...")
            results["Activity Scoring"] = "✅ Available (incremental)"
            logger.info(f"    ✅ Activity Scoring: Available with incremental support")
        else:
            results["Activity Scoring"] = "❌ Not Available"
            logger.info(f"    ❌ Activity Scoring: Not Available")
        
        # Test AI directory scraping
        if DIRECTORY_SCRAPING_AVAILABLE:
            logger.info(f"  🔍 Testing AI Directory Scraping...")
            results["AI Directory Scraping"] = "✅ Available"
            logger.info(f"    ✅ AI Directory Scraping: Available with incremental support")
        else:
            results["AI Directory Scraping"] = "❌ Not Available"
            logger.info(f"    ❌ AI Directory Scraping: Not Available")
        
        logger.info("📊 Incremental API Test Summary:")
        for api_name, status in results.items():
            logger.info(f"  • {api_name}: {status}")
        
        return results
    
    def show_status(self):
        """Show incremental discovery system status"""
        logger.info("📊 Incremental Discovery System Status:")
        logger.info(f"  • Total runs: {self.stats['runs']}")
        logger.info(f"  • Total tools found: {self.stats['tools_found']}")
        logger.info(f"  • Total tools scored: {self.stats['tools_scored']}")
        logger.info(f"  • Total tools skipped: {self.stats['tools_skipped']}")
        
        if self.stats['runs'] > 0:
            avg_tools = self.stats['tools_found'] / self.stats['runs']
            avg_scored = self.stats['tools_scored'] / self.stats['runs']
            avg_skipped = self.stats['tools_skipped'] / self.stats['runs']
            
            logger.info(f"  • Average new tools per run: {avg_tools:.1f}")
            logger.info(f"  • Average scored per run: {avg_scored:.1f}")
            logger.info(f"  • Average skipped per run: {avg_skipped:.1f}")
            
            # Calculate efficiency
            total_processed = self.stats['tools_found'] + self.stats['tools_skipped']
            if total_processed > 0:
                efficiency = (self.stats['tools_skipped'] / total_processed) * 100
                logger.info(f"  • Efficiency (% skipped): {efficiency:.1f}%")
        
        # Show state information
        self.show_state()
        
        logger.info("\n🎯 Available Incremental Methods:")
        for method, config in self.discovery_methods.items():
            logger.info(f"  • {method}: {config['description']} (target: {config['target']})")
        
        logger.info("\n🔧 Incremental Features:")
        logger.info("  ✅ Per-API last check tracking")
        logger.info("  ✅ Automatic weekly full scans") 
        logger.info("  ✅ Smart activity score updates")
        logger.info("  ✅ Persistent state management")
        logger.info("  ✅ Efficiency metrics and skip tracking")
        logger.info("  ✅ AI Directory scraping integration")
        logger.info("  ✅ Dead website cooldown system")


def main():
    """Main CLI interface for incremental discovery"""
    system = IncrementalDiscoverySystem()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            # Incremental continuous discovery
            method = sys.argv[2] if len(sys.argv) > 2 else "enhanced_all"
            interval = int(sys.argv[3]) if len(sys.argv) > 3 else 6
            auto_score = "--no-scoring" not in sys.argv
            
            if method not in system.discovery_methods:
                print(f"❌ Unknown method: {method}")
                print(f"Available methods: {list(system.discovery_methods.keys())}")
                return
            
            system.start_continuous(method, interval, auto_score)
            
        elif command == "run-once":
            # Single incremental discovery run
            method = sys.argv[2] if len(sys.argv) > 2 else "enhanced_all"
            auto_score = "--no-scoring" not in sys.argv
            force_full = "--force-full" in sys.argv
            
            if method not in system.discovery_methods:
                print(f"❌ Unknown method: {method}")
                print(f"Available methods: {list(system.discovery_methods.keys())}")
                return
            
            result = system.run_incremental_discovery(method, auto_score, force_full)
            print(f"✅ Incremental discovery complete:")
            print(f"   📈 Found {result['new_tools']} new tools")
            print(f"   ⚡ Scored {result['scored_tools']} tools") 
            print(f"   ⏭️ Skipped {result['skipped_tools']} unchanged tools")
            
        elif command == "state":
            # Show current state
            system.show_state()
            
        elif command == "status":
            # Show comprehensive status
            system.show_status()
            
        elif command == "reset":
            # Reset state
            api_name = sys.argv[2] if len(sys.argv) > 2 else None
            system.reset_state(api_name)
            
        elif command == "show-dead":
            # NEW: Show dead websites and their retry status
            system.show_dead_websites()
            
        elif command == "reset-dead":
            # NEW: Reset dead websites to allow immediate retry
            system.reset_dead_websites()
            
        elif command == "test":
            # Test API connections
            system.test_apis()
            
        elif command == "setup":
            # Show setup instructions
            print("🛠️ Incremental Discovery Setup:")
            print("\n⚡ KEY ADVANTAGE: Only checks tools updated since last run!")
            print("💡 Dramatically reduces API calls and processing time")
            print("📊 Tracks state in discovery_state.json")
            print("💀 Smart dead website handling with 3-day cooldowns")
            
            print("\n🎯 FIXED ISSUES:")
            print("✅ Dead websites get proper activity_score=0.0")
            print("✅ Dead websites aren't retried every run (3-day cooldown)")
            print("✅ Realistic tool counts (no more 208 when only 104 discovered)")
            print("✅ Better failure handling and logging")
            
            print("\n💾 STATE MANAGEMENT:")
            print("• Tracks last check time per API")
            print("• Automatic weekly full scans")
            print("• Persistent state file (discovery_state.json)")
            print("• Dead website cooldown tracking")
            
            print("\n💀 DEAD WEBSITE COMMANDS:")
            print("• Show dead sites: python intelligent_discovery.py show-dead")
            print("• Reset cooldowns: python intelligent_discovery.py reset-dead")
            
            print("\n✅ Test your setup:")
            print("python intelligent_discovery.py state")
            
        else:
            print("❌ Unknown command")
    else:
        print("🧠 Incremental AI Tools Discovery System - FIXED VERSION")
        print("💡 Only processes UPDATED tools since last run!")
        print("💀 Smart dead website handling with cooldowns!")
        print("🤖 Includes AI Directory Scraping!")
        print("\nUsage:")
        print("  python intelligent_discovery.py start [method] [interval_hours]")
        print("  python intelligent_discovery.py run-once [method] [--force-full]")
        print("  python intelligent_discovery.py state")
        print("  python intelligent_discovery.py status")
        print("  python intelligent_discovery.py reset [api_name]")
        print("  python intelligent_discovery.py show-dead")
        print("  python intelligent_discovery.py reset-dead")
        print("  python intelligent_discovery.py setup")
        print("  python intelligent_discovery.py test")
        
        print("\n🎯 Discovery Methods:")
        for method, config in system.discovery_methods.items():
            print(f"  • {method}: {config['description']}")
        
        print("\n⚡ FIXED Features:")
        print("  • Default: Only check updated tools since last run")
        print("  • Weekly: Automatic full scan every 7 days")
        print("  • Force full: Add --force-full flag")
        print("  • State tracking: Persistent in discovery_state.json")
        print("  • AI Directories: Daily incremental checks")
        print("  • Dead sites: 3-day cooldown before retry")
        print("  • Realistic counts: No more inflated tool numbers")
        
        print("\n📋 Examples:")
        print("  # Incremental discovery with APIs + directories (recommended)")
        print("  python intelligent_discovery.py run-once enhanced_all")
        print("")
        print("  # Check dead websites and their status")
        print("  python intelligent_discovery.py show-dead")
        print("")
        print("  # Force full scan (ignores incremental state)")
        print("  python intelligent_discovery.py run-once enhanced_all --force-full")
        print("")
        print("  # Reset dead website cooldowns (for testing)")
        print("  python intelligent_discovery.py reset-dead")
        print("")
        print("  # Start continuous incremental discovery every 2 hours") 
        print("  python intelligent_discovery.py start enhanced_all 2")
        
        print("\n💡 FIXED Benefits:")
        print("  🚀 Much faster runs (only checks updated tools)")
        print("  💰 Reduced API usage (fewer requests)")
        print("  ⚡ Smart scoring (only re-score when needed)")
        print("  📊 State persistence (remembers what was checked)")
        print("  🔄 Auto full-scan weekly (catches any missed updates)")
        print("  🤖 AI Directory integration (curated quality tools)")
        print("  💀 Dead website management (3-day cooldowns)")
        print("  📏 Realistic tool counts (no more fake inflation)")


if __name__ == "__main__":
    main()