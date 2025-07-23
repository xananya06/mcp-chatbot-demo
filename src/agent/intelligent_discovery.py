import time
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.real_apis_service import unified_apis_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDiscovery:
    def __init__(self):
        self.stats = {"runs": 0, "tools_found": 0}
    
    def run_discovery(self):
        logger.info("🧠 Discovery starting...")
        total_new = 0
        
        try:
            # GitHub discovery
            logger.info("  🔍 GitHub discovery...")
            result = unified_apis_service.run_sync_discover_github(target_tools=20)
            new_tools = result.get("total_saved", 0)
            total_new += new_tools
            logger.info(f"    ✅ GitHub: {new_tools} new tools")
            
            # NPM discovery
            logger.info("  📦 NPM discovery...")
            result = unified_apis_service.run_sync_discover_npm(target_tools=15)
            new_tools = result.get("total_saved", 0)
            total_new += new_tools
            logger.info(f"    ✅ NPM: {new_tools} new tools")
            
            # PyPI discovery
            logger.info("  🐍 PyPI discovery...")
            result = unified_apis_service.run_sync_discover_pypi(target_tools=10)
            new_tools = result.get("total_saved", 0)
            total_new += new_tools
            logger.info(f"    ✅ PyPI: {new_tools} new tools")
            
        except Exception as e:
            logger.error(f"Discovery error: {e}")
        
        self.stats["runs"] += 1
        self.stats["tools_found"] += total_new
        logger.info(f"🎊 Discovery complete: {total_new} new tools found total")
        return {"new_tools": total_new}
    
    def start_continuous(self):
        logger.info("🚀 Starting continuous discovery (every 6 hours)...")
        logger.info("💡 This will automatically find new AI tools from GitHub, NPM, and PyPI")
        
        while True:
            try:
                result = self.run_discovery()
                logger.info(f"📊 Session stats: {self.stats['runs']} runs, {self.stats['tools_found']} total tools found")
                logger.info("⏳ Waiting 6 hours until next discovery cycle...")
                time.sleep(6 * 3600)  # 6 hours
            except KeyboardInterrupt:
                logger.info("⚠️ Discovery stopped by user")
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}")
                logger.info("🔄 Retrying in 5 minutes...")
                time.sleep(300)

def main():
    system = SimpleDiscovery()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            system.start_continuous()
        elif command == "run-once":
            result = system.run_discovery()
            print(f"✅ Discovery complete: Found {result['new_tools']} new tools")
        elif command == "status":
            print(f"📊 System stats: {system.stats['runs']} runs, {system.stats['tools_found']} tools discovered")
        else:
            print("❌ Unknown command")
    else:
        print("🧠 AI Tools Discovery System")
        print("Usage:")
        print("  python intelligent_discovery.py start      # Start continuous discovery (every 6 hours)")
        print("  python intelligent_discovery.py run-once   # Run single discovery cycle")
        print("  python intelligent_discovery.py status     # Show discovery statistics")

if __name__ == "__main__":
    main()