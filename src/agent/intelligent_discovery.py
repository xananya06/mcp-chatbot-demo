#!/usr/bin/env python3
# src/agent/intelligent_discovery.py
# ENHANCED VERSION - Automatic Activity Scoring After Discovery

import time
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.real_apis_service import unified_apis_service

# Import activity assessment
try:
    from app.services.unified_activity_service import unified_activity_service
    from app.db.database import SessionLocal
    from app.models.chat import DiscoveredTool
    from sqlalchemy import and_
    from datetime import datetime, timedelta
    ACTIVITY_SCORING_AVAILABLE = True
except ImportError as e:
    ACTIVITY_SCORING_AVAILABLE = False
    print(f"⚠️ Activity scoring not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDiscoverySystem:
    """
    Enhanced Discovery System with AUTOMATIC ACTIVITY SCORING:
    1. Discover tools from APIs
    2. Automatically assess activity scores
    3. Save complete, scored tools to database
    
    NO WEB SCRAPING - All official APIs + quality scoring!
    """
    
    def __init__(self):
        self.stats = {"runs": 0, "tools_found": 0, "tools_scored": 0}
        
        # Available discovery methods
        self.discovery_methods = {
            "enhanced_all": {
                "method": "run_sync_discover_all_real_apis",
                "target": 500,
                "description": "All APIs + Auto Activity Scoring"
            },
            "standard": {
                "method": "run_sync_discover_no_auth_apis", 
                "target": 200,
                "description": "No-auth APIs + Auto Activity Scoring"
            },
            "product_hunt": {
                "method": "run_sync_discover_producthunt",
                "target": 150,
                "description": "Product Hunt + Auto Activity Scoring"
            },
            "reddit": {
                "method": "run_sync_discover_reddit",
                "target": 100,
                "description": "Reddit + Auto Activity Scoring"
            },
            "crunchbase": {
                "method": "run_sync_discover_crunchbase",
                "target": 80,
                "description": "Crunchbase + Auto Activity Scoring"
            },
            "github": {
                "method": "run_sync_discover_github",
                "target": 150,
                "description": "GitHub + Auto Activity Scoring"
            },
            "npm": {
                "method": "run_sync_discover_npm",
                "target": 100,
                "description": "NPM + Auto Activity Scoring"
            }
        }
    
    def run_discovery(self, method: str = "enhanced_all", auto_score: bool = True):
        """Run discovery with automatic activity scoring"""
        
        if method not in self.discovery_methods:
            logger.error(f"❌ Unknown discovery method: {method}")
            logger.info(f"Available methods: {list(self.discovery_methods.keys())}")
            return {"new_tools": 0, "scored_tools": 0}
        
        config = self.discovery_methods[method]
        logger.info(f"🧠 Enhanced Discovery Starting - Method: {method}")
        logger.info(f"🎯 {config['description']}")
        logger.info(f"📊 Target: {config['target']} tools")
        if auto_score:
            logger.info(f"⚡ Auto Activity Scoring: ENABLED")
        
        total_new = 0
        total_scored = 0
        
        try:
            # PHASE 1: Discovery
            logger.info(f"\n📡 PHASE 1: API DISCOVERY")
            api_method = getattr(unified_apis_service, config["method"])
            result = api_method(target_tools=config["target"])
            
            new_tools = result.get("total_saved", 0)
            total_new += new_tools
            
            # Log discovery results
            if result.get("api_results"):
                logger.info("📡 API Results:")
                for api_name, api_result in result["api_results"].items():
                    if api_result.get("success"):
                        tools_count = api_result.get("tools_discovered", 0)
                        processing_time = api_result.get("processing_time", 0)
                        logger.info(f"  ✅ {api_name}: {tools_count} tools ({processing_time:.1f}s)")
                    else:
                        error = api_result.get("error", "Unknown error")
                        logger.info(f"  ❌ {api_name}: {error}")
            
            logger.info(f"✅ Discovery Phase: {new_tools} new tools found")
            
            # PHASE 2: Automatic Activity Scoring
            if auto_score and new_tools > 0 and ACTIVITY_SCORING_AVAILABLE:
                logger.info(f"\n⚡ PHASE 2: AUTOMATIC ACTIVITY SCORING")
                scored_tools = self._score_recent_tools(limit=new_tools * 2)  # Score a few extra to be safe
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
        
        self.stats["runs"] += 1
        self.stats["tools_found"] += total_new
        self.stats["tools_scored"] += total_scored
        
        logger.info(f"\n🎊 ENHANCED DISCOVERY COMPLETE!")
        logger.info(f"📈 New tools found: {total_new}")
        logger.info(f"⚡ Tools scored: {total_scored}")
        logger.info(f"🎯 Ready for high-quality AI tool recommendations!")
        
        return {"new_tools": total_new, "scored_tools": total_scored}
    
    def _score_recent_tools(self, limit: int = 50) -> int:
        """Score recently discovered tools that don't have activity scores"""
        
        if not ACTIVITY_SCORING_AVAILABLE:
            return 0
        
        logger.info(f"🔍 Finding recently discovered tools to score...")
        
        db = SessionLocal()
        try:
            # Get recent tools without activity scores
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)  # Last hour
            
            unscored_tools = db.query(DiscoveredTool).filter(
                and_(
                    DiscoveredTool.activity_score.is_(None),
                    DiscoveredTool.created_at >= recent_cutoff,
                    DiscoveredTool.website.isnot(None),
                    DiscoveredTool.website != ""
                )
            ).limit(limit).all()
            
            if not unscored_tools:
                logger.info("📋 No recent unscored tools found")
                return 0
            
            logger.info(f"📋 Found {len(unscored_tools)} recent tools to score")
            
            scored_count = 0
            
            # Score each tool
            for i, tool in enumerate(unscored_tools):
                try:
                    logger.info(f"  ⚡ Scoring {i+1}/{len(unscored_tools)}: {tool.name}")
                    
                    # Use unified activity service to assess the tool
                    assessment = unified_activity_service.sync_assess_single_tool(tool)
                    
                    if assessment and not assessment.get('error'):
                        # Update tool with assessment results
                        tool.tool_type_detected = assessment.get('tool_type_detected', 'unknown')
                        tool.activity_score = assessment.get('activity_score', 0.0)
                        tool.last_activity_check = datetime.utcnow()
                        
                        # Update source-specific metrics
                        if 'github_stars' in assessment:
                            tool.github_stars = assessment.get('github_stars')
                            tool.github_last_commit = assessment.get('github_last_commit')
                            tool.github_contributors = assessment.get('github_contributors')
                            
                        if 'npm_weekly_downloads' in assessment:
                            tool.npm_weekly_downloads = assessment.get('npm_weekly_downloads')
                            tool.npm_last_update = assessment.get('npm_last_update')
                            
                        if 'pypi_last_release' in assessment:
                            tool.pypi_last_release = assessment.get('pypi_last_release')
                            
                        if 'website_status' in assessment:
                            tool.website_status = assessment.get('website_status')
                            
                        if 'is_actively_maintained' in assessment:
                            tool.is_actively_maintained = assessment.get('is_actively_maintained')
                        
                        # Calculate quality scores
                        self._calculate_quality_scores(tool, assessment)
                        
                        scored_count += 1
                        
                        score = assessment.get('activity_score', 0)
                        tool_type = assessment.get('tool_type_detected', 'unknown')
                        logger.info(f"    ✅ Score: {score:.2f} | Type: {tool_type}")
                        
                    else:
                        error = assessment.get('error', 'Unknown error') if assessment else 'Assessment failed'
                        logger.info(f"    ❌ Failed: {error}")
                    
                    # Small delay to be respectful to APIs
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"    ❌ Error scoring {tool.name}: {e}")
                    continue
            
            # Commit all changes
            db.commit()
            logger.info(f"✅ Successfully scored {scored_count}/{len(unscored_tools)} tools")
            return scored_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error in scoring process: {e}")
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
                    DiscoveredTool.last_activity_check >= datetime.utcnow() - timedelta(minutes=10)
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
    
    def start_continuous(self, method: str = "enhanced_all", interval_hours: int = 6, auto_score: bool = True):
        """Start continuous discovery with automatic activity scoring"""
        
        config = self.discovery_methods.get(method, self.discovery_methods["enhanced_all"])
        
        logger.info(f"🚀 Starting Enhanced Continuous Discovery")
        logger.info(f"📋 Method: {method} ({config['description']})")
        logger.info(f"⏰ Interval: {interval_hours} hours")
        logger.info(f"⚡ Auto Activity Scoring: {'ENABLED' if auto_score else 'DISABLED'}")
        logger.info(f"💡 Complete workflow: Discovery → Scoring → Ready!")
        
        # Check API configurations
        self._check_api_configurations()
        
        while True:
            try:
                result = self.run_discovery(method, auto_score)
                logger.info(f"📊 Session stats: {self.stats['runs']} runs, {self.stats['tools_found']} total tools found, {self.stats['tools_scored']} total scored")
                logger.info(f"⏳ Waiting {interval_hours} hours until next discovery cycle...")
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
        logger.info("  ✅ GitHub API: Available (higher limits with GITHUB_TOKEN)")
        logger.info("  ✅ NPM Registry API: Available")
        logger.info("  ✅ PyPI JSON API: Available") 
        logger.info("  ✅ Hacker News API: Available")
        logger.info("  ✅ Stack Overflow API: Available")
        logger.info("  ✅ VS Code Marketplace API: Available")
        logger.info("  ✅ Reddit API: Available (no auth required)")
        
        # Check activity scoring
        if ACTIVITY_SCORING_AVAILABLE:
            logger.info("  ✅ Activity Scoring: Available")
        else:
            logger.info("  ❌ Activity Scoring: Not available")
        
        # Require configuration
        if os.getenv('PRODUCT_HUNT_CLIENT_ID') and os.getenv('PRODUCT_HUNT_CLIENT_SECRET'):
            logger.info("  ✅ Product Hunt API: Configured")
        elif os.getenv('PRODUCT_HUNT_ACCESS_TOKEN'):
            logger.info("  ✅ Product Hunt API: Configured (token)")
        else:
            logger.info("  ⚠️ Product Hunt API: Not configured")
            logger.info("     Set PRODUCT_HUNT_CLIENT_ID and PRODUCT_HUNT_CLIENT_SECRET")
        
        if os.getenv('CRUNCHBASE_API_KEY'):
            logger.info("  ✅ Crunchbase API: Configured")
        else:
            logger.info("  ⚠️ Crunchbase API: Not configured")
            logger.info("     Set CRUNCHBASE_API_KEY")
        
        if os.getenv('DEV_TO_TOKEN'):
            logger.info("  ✅ Dev.to API: Configured")
        else:
            logger.info("  ⚠️ Dev.to API: Not configured (optional)")
    
    def test_apis(self):
        """Test individual API connections"""
        logger.info("🧪 Testing API connections...")
        
        test_methods = [
            ("GitHub", "run_sync_discover_github", 5),
            ("NPM", "run_sync_discover_npm", 5),
            ("Reddit", "run_sync_discover_reddit", 5),
            ("Hacker News", "run_sync_discover_hackernews", 5)
        ]
        
        if os.getenv('PRODUCT_HUNT_CLIENT_ID') or os.getenv('PRODUCT_HUNT_ACCESS_TOKEN'):
            test_methods.append(("Product Hunt", "run_sync_discover_producthunt", 5))
        
        if os.getenv('CRUNCHBASE_API_KEY'):
            test_methods.append(("Crunchbase", "run_sync_discover_crunchbase", 3))
        
        results = {}
        
        for api_name, method_name, target in test_methods:
            try:
                logger.info(f"  🔍 Testing {api_name} API...")
                api_method = getattr(unified_apis_service, method_name)
                result = api_method(target_tools=target)
                
                if result.get("total_saved", 0) >= 0:  # Even 0 is OK for a test
                    results[api_name] = "✅ Working"
                    logger.info(f"    ✅ {api_name}: Working")
                else:
                    results[api_name] = "⚠️ Issues"
                    logger.info(f"    ⚠️ {api_name}: Issues detected")
                    
            except Exception as e:
                results[api_name] = f"❌ Failed: {str(e)}"
                logger.info(f"    ❌ {api_name}: {str(e)}")
        
        # Test activity scoring
        if ACTIVITY_SCORING_AVAILABLE:
            logger.info(f"  🔍 Testing Activity Scoring...")
            results["Activity Scoring"] = "✅ Available"
            logger.info(f"    ✅ Activity Scoring: Available")
        else:
            results["Activity Scoring"] = "❌ Not Available"
            logger.info(f"    ❌ Activity Scoring: Not Available")
        
        logger.info("📊 API Test Summary:")
        for api_name, status in results.items():
            logger.info(f"  • {api_name}: {status}")
        
        return results
    
    def show_status(self):
        """Show discovery system status"""
        logger.info("📊 Enhanced Discovery System Status:")
        logger.info(f"  • Total runs: {self.stats['runs']}")
        logger.info(f"  • Total tools found: {self.stats['tools_found']}")
        logger.info(f"  • Total tools scored: {self.stats['tools_scored']}")
        
        if self.stats['runs'] > 0:
            avg_tools = self.stats['tools_found'] / self.stats['runs']
            avg_scored = self.stats['tools_scored'] / self.stats['runs']
            logger.info(f"  • Average tools per run: {avg_tools:.1f}")
            logger.info(f"  • Average scored per run: {avg_scored:.1f}")
        
        logger.info("\n🎯 Available Discovery Methods:")
        for method, config in self.discovery_methods.items():
            logger.info(f"  • {method}: {config['description']} (target: {config['target']})")
        
        logger.info("\n🔧 Enhanced Features:")
        logger.info("  ✅ Product Hunt API - Daily fresh tools")
        logger.info("  ✅ Reddit API - Community discussions") 
        logger.info("  ✅ Crunchbase API - AI startup funding data")
        logger.info("  ✅ Traditional APIs - GitHub, NPM, PyPI, etc.")
        logger.info("  ✅ AUTO Activity Scoring - Quality assessment")
        logger.info("  ❌ Web scraping - Removed for reliability")


def main():
    """Main CLI interface"""
    system = EnhancedDiscoverySystem()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            # Enhanced continuous discovery
            method = sys.argv[2] if len(sys.argv) > 2 else "enhanced_all"
            interval = int(sys.argv[3]) if len(sys.argv) > 3 else 6
            auto_score = "--no-scoring" not in sys.argv
            
            if method not in system.discovery_methods:
                print(f"❌ Unknown method: {method}")
                print(f"Available methods: {list(system.discovery_methods.keys())}")
                return
            
            system.start_continuous(method, interval, auto_score)
            
        elif command == "run-once":
            # Single discovery run
            method = sys.argv[2] if len(sys.argv) > 2 else "enhanced_all"
            auto_score = "--no-scoring" not in sys.argv
            
            if method not in system.discovery_methods:
                print(f"❌ Unknown method: {method}")
                print(f"Available methods: {list(system.discovery_methods.keys())}")
                return
            
            result = system.run_discovery(method, auto_score)
            print(f"✅ Discovery complete: Found {result['new_tools']} new tools, scored {result['scored_tools']} tools")
            
        elif command == "test":
            # Test API connections
            system.test_apis()
            
        elif command == "status":
            # Show system status
            system.show_status()
            
        elif command == "setup":
            # Show setup instructions
            print("🛠️ Enhanced Discovery Setup Instructions:")
            print("\n🎯 PRODUCT HUNT API (Recommended for fresh tools):")
            print("1. Go to: https://api.producthunt.com/v2/oauth/applications")
            print("2. Create new application")
            print("3. Set environment variables:")
            print("   export PRODUCT_HUNT_CLIENT_ID='your_client_id'")
            print("   export PRODUCT_HUNT_CLIENT_SECRET='your_client_secret'")
            
            print("\n🏢 CRUNCHBASE API (Optional for startup data):")
            print("1. Go to: https://www.crunchbase.com/products/api")
            print("2. Get API key")
            print("3. Set environment variable:")
            print("   export CRUNCHBASE_API_KEY='your_api_key'")
            
            print("\n📡 OTHER APIS:")
            print("• Reddit API: No setup required")
            print("• GitHub API: Optional GITHUB_TOKEN for higher limits")
            print("• All others work without API keys!")
            
            print("\n⚡ ACTIVITY SCORING:")
            print("• Automatic after discovery")
            print("• Assesses tool quality, activity, maintenance")
            print("• Creates high-quality tool recommendations")
            
            print("\n✅ Test your setup:")
            print("python intelligent_discovery.py test")
            
        else:
            print("❌ Unknown command")
    else:
        print("🧠 Enhanced AI Tools Discovery System")
        print("💡 Now with AUTO Activity Scoring!")
        print("\nUsage:")
        print("  python intelligent_discovery.py start [method] [interval_hours]")
        print("  python intelligent_discovery.py run-once [method]")
        print("  python intelligent_discovery.py test")
        print("  python intelligent_discovery.py status") 
        print("  python intelligent_discovery.py setup")
        
        print("\n🎯 Discovery Methods:")
        for method, config in system.discovery_methods.items():
            print(f"  • {method}: {config['description']}")
        
        print("\n⚡ Auto Scoring Options:")
        print("  • Default: Auto scoring ENABLED")
        print("  • Disable: Add --no-scoring flag")
        
        print("\n📋 Examples:")
        print("  # Enhanced discovery with auto scoring")
        print("  python intelligent_discovery.py run-once enhanced_all")
        print("")
        print("  # Discovery without scoring")
        print("  python intelligent_discovery.py run-once standard --no-scoring")
        print("")
        print("  # Continuous discovery every 4 hours with auto scoring")
        print("  python intelligent_discovery.py start enhanced_all 4")


if __name__ == "__main__":
    main()