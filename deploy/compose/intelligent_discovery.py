#!/usr/bin/env python3
import asyncio
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
            result = unified_apis_service.run_sync_discover_github(target_tools=20)
            new_tools = result.get("total_saved", 0)
            total_new += new_tools
            logger.info(f"GitHub: {new_tools} tools")
            
            # NPM discovery
            result = unified_apis_service.run_sync_discover_npm(target_tools=15)
            new_tools = result.get("total_saved", 0)
            total_new += new_tools
            logger.info(f"NPM: {new_tools} tools")
            
            # PyPI discovery
            result = unified_apis_service.run_sync_discover_pypi(target_tools=10)
            new_tools = result.get("total_saved", 0)
            total_new += new_tools
            logger.info(f"PyPI: {new_tools} tools")
            
        except Exception as e:
            logger.error(f"Error: {e}")
        
        self.stats["runs"] += 1
        self.stats["tools_found"] += total_new
        logger.info(f"✅ Discovery complete: {total_new} new tools found")
        return {"new_tools": total_new}
    
    def start_continuous(self):
        logger.info("🚀 Starting continuous discovery (every 6 hours)...")
        while True:
            try:
                self.run_discovery()
                logger.info("⏳ Waiting 6 hours until next cycle...")
                time.sleep(6 * 3600)
            except KeyboardInterrupt:
                logger.info("⚠️ Stopped by user")
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}")
                time.sleep(300)

def main():
    system = SimpleDiscovery()
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "start":
            system.start_continuous()
        elif command == "run-once":
            result = system.run_discovery()
            print(f"Found {result['new_tools']} tools")
        elif command == "status":
            print(f"Runs: {system.stats['runs']}, Tools found: {system.stats['tools_found']}")
    else:
        print("Usage: python intelligent_discovery.py [start|run-once|status]")

if __name__ == "__main__":
    main()
