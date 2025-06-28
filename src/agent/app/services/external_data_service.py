import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any
import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.services.chat_service import save_discovered_tools_with_deduplication

# Import our new real API service
from app.services.real_external_api_service import RealExternalAPIService

logger = logging.getLogger(__name__)

class ExternalDataService:
    """Enhanced External data integration with REAL API sources"""
    
    def __init__(self):
        self.real_api_service = RealExternalAPIService()
        
    async def integrate_external_sources(self, target_tools: int = 10000) -> Dict[str, Any]:
        """Main integration pipeline with real external APIs - NO DEDUPLICATION"""
        
        results = {
            "integration_id": f"real_external_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_discovered": 0,
            "total_saved": 0,
            "sources_processed": [],
            "processing_mode": "real_apis_no_dedup"
        }
        
        print(f"🌐 REAL EXTERNAL API INTEGRATION STARTED")
        print(f"🎯 Target: {target_tools} tools from real external sources")
        print(f"⚡ Mode: NO DEDUPLICATION for maximum tool count")
        
        # Use the real API service
        async with self.real_api_service as api_service:
            real_results = await api_service.massive_discovery_pipeline(target_tools)
            
            # Merge results
            results.update({
                "total_discovered": real_results.get("total_discovered", 0),
                "total_saved": real_results.get("total_saved", 0),
                "sources_processed": real_results.get("sources_processed", []),
                "errors": real_results.get("errors", [])
            })
        
        results["end_time"] = datetime.utcnow().isoformat()
        
        print(f"\n🎊 REAL API Integration Complete!")
        print(f"📈 Results: {results['total_saved']} new tools added")
        print(f"📊 Sources processed: {len(results['sources_processed'])}")
        
        return results
    
    async def rapid_github_discovery(self, target_tools: int = 5000) -> Dict[str, Any]:
        """Rapid GitHub-only discovery for maximum tool volume"""
        
        results = {
            "discovery_id": f"github_rapid_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_saved": 0,
            "processing_mode": "github_only_rapid"
        }
        
        print(f"🚀 RAPID GITHUB DISCOVERY")
        print(f"🎯 Target: {target_tools} tools from GitHub only")
        
        async with self.real_api_service as api_service:
            github_tools = await api_service._discover_github_ai_tools(target_tools)
            
            if github_tools:
                db = SessionLocal()
                try:
                    # Save without deduplication for speed
                    save_result = self._save_tools_no_dedup(db, github_tools)
                    results["total_saved"] = save_result.get("saved", 0)
                finally:
                    db.close()
        
        results["end_time"] = datetime.utcnow().isoformat()
        print(f"✅ GitHub Rapid Discovery: {results['total_saved']} tools added")
        
        return results

    async def product_hunt_discovery(self, target_tools: int = 2000) -> Dict[str, Any]:
        """Product Hunt focused discovery"""
        
        results = {
            "discovery_id": f"ph_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_saved": 0
        }
        
        print(f"🏆 PRODUCT HUNT DISCOVERY")
        
        async with self.real_api_service as api_service:
            ph_tools = await api_service._discover_product_hunt_tools(target_tools)
            
            if ph_tools:
                db = SessionLocal()
                try:
                    save_result = self._save_tools_no_dedup(db, ph_tools)
                    results["total_saved"] = save_result.get("saved", 0)
                finally:
                    db.close()
        
        results["end_time"] = datetime.utcnow().isoformat()
        print(f"✅ Product Hunt Discovery: {results['total_saved']} tools added")
        
        return results

    async def alternativeto_discovery(self, target_tools: int = 3000) -> Dict[str, Any]:
        """AlternativeTo focused discovery"""
        
        results = {
            "discovery_id": f"alt_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(), 
            "target_tools": target_tools,
            "total_saved": 0
        }
        
        print(f"🔄 ALTERNATIVETO DISCOVERY")
        
        async with self.real_api_service as api_service:
            alt_tools = await api_service._discover_alternativeto_tools(target_tools)
            
            if alt_tools:
                db = SessionLocal()
                try:
                    save_result = self._save_tools_no_dedup(db, alt_tools)
                    results["total_saved"] = save_result.get("saved", 0)
                finally:
                    db.close()
        
        results["end_time"] = datetime.utcnow().isoformat()
        print(f"✅ AlternativeTo Discovery: {results['total_saved']} tools added")
        
        return results

    async def chrome_extensions_discovery(self, target_tools: int = 2000) -> Dict[str, Any]:
        """Chrome extensions focused discovery"""
        
        results = {
            "discovery_id": f"chrome_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_saved": 0
        }
        
        print(f"🌐 CHROME EXTENSIONS DISCOVERY")
        
        async with self.real_api_service as api_service:
            chrome_tools = await api_service._discover_chrome_extensions(target_tools)
            
            if chrome_tools:
                db = SessionLocal()
                try:
                    save_result = self._save_tools_no_dedup(db, chrome_tools)
                    results["total_saved"] = save_result.get("saved", 0)
                finally:
                    db.close()
        
        results["end_time"] = datetime.utcnow().isoformat()
        print(f"✅ Chrome Extensions Discovery: {results['total_saved']} tools added")
        
        return results

    async def vscode_extensions_discovery(self, target_tools: int = 1500) -> Dict[str, Any]:
        """VS Code extensions focused discovery"""
        
        results = {
            "discovery_id": f"vscode_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_saved": 0
        }
        
        print(f"🔧 VS CODE EXTENSIONS DISCOVERY")
        
        async with self.real_api_service as api_service:
            vscode_tools = await api_service._discover_vscode_extensions(target_tools)
            
            if vscode_tools:
                db = SessionLocal()
                try:
                    save_result = self._save_tools_no_dedup(db, vscode_tools)
                    results["total_saved"] = save_result.get("saved", 0)
                finally:
                    db.close()
        
        results["end_time"] = datetime.utcnow().isoformat()
        print(f"✅ VS Code Extensions Discovery: {results['total_saved']} tools added")
        
        return results

    async def npm_packages_discovery(self, target_tools: int = 2000) -> Dict[str, Any]:
        """NPM packages focused discovery"""
        
        results = {
            "discovery_id": f"npm_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_saved": 0
        }
        
        print(f"📦 NPM PACKAGES DISCOVERY")
        
        async with self.real_api_service as api_service:
            npm_tools = await api_service._discover_npm_packages(target_tools)
            
            if npm_tools:
                db = SessionLocal()
                try:
                    save_result = self._save_tools_no_dedup(db, npm_tools)
                    results["total_saved"] = save_result.get("saved", 0)
                finally:
                    db.close()
        
        results["end_time"] = datetime.utcnow().isoformat()
        print(f"✅ NPM Packages Discovery: {results['total_saved']} tools added")
        
        return results

    async def pypi_packages_discovery(self, target_tools: int = 1500) -> Dict[str, Any]:
        """PyPI packages focused discovery"""
        
        results = {
            "discovery_id": f"pypi_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_saved": 0
        }
        
        print(f"🐍 PYPI PACKAGES DISCOVERY")
        
        async with self.real_api_service as api_service:
            pypi_tools = await api_service._discover_pypi_packages(target_tools)
            
            if pypi_tools:
                db = SessionLocal()
                try:
                    save_result = self._save_tools_no_dedup(db, pypi_tools)
                    results["total_saved"] = save_result.get("saved", 0)
                finally:
                    db.close()
        
        results["end_time"] = datetime.utcnow().isoformat()
        print(f"✅ PyPI Packages Discovery: {results['total_saved']} tools added")
        
        return results

    def _save_tools_no_dedup(self, db: Session, tools: List[dict]) -> Dict[str, Any]:
        """Save tools without deduplication for maximum volume"""
        
        from app.models.chat import DiscoveredTool
        
        saved_count = 0
        errors = []
        
        for tool_data in tools:
            try:
                # Create new tool without checking for existing
                new_tool = DiscoveredTool(
                    name=tool_data.get('name', '').strip(),
                    website=tool_data.get('website', '').strip(),
                    description=tool_data.get('description', '').strip(),
                    tool_type=tool_data.get('tool_type', '').strip(),
                    category=tool_data.get('category', '').strip(),
                    pricing=tool_data.get('pricing', '').strip(),
                    features=tool_data.get('features', '').strip(),
                    confidence_score=tool_data.get('confidence', 0.0),
                    source_data=tool_data.get('source_data', '')
                )
                db.add(new_tool)
                saved_count += 1
                
                # Commit in batches for performance
                if saved_count % 100 == 0:
                    db.commit()
                    
            except Exception as e:
                errors.append(f"Error saving {tool_data.get('name', 'unknown')}: {str(e)}")
        
        try:
            db.commit()
            return {
                "success": True,
                "saved": saved_count,
                "updated": 0,
                "skipped": 0,
                "errors": errors
            }
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": f"Database commit failed: {str(e)}",
                "saved": 0,
                "updated": 0,
                "skipped": 0
            }

    # Sync wrappers for FastAPI
    def run_sync_massive_discovery(self, target_tools: int = 10000) -> Dict[str, Any]:
        """Synchronous wrapper for async massive discovery"""
        return asyncio.run(self.integrate_external_sources(target_tools))

    def run_sync_github_discovery(self, target_tools: int = 5000) -> Dict[str, Any]:
        """Synchronous wrapper for GitHub discovery"""
        return asyncio.run(self.rapid_github_discovery(target_tools))

    def run_sync_product_hunt_discovery(self, target_tools: int = 2000) -> Dict[str, Any]:
        """Synchronous wrapper for Product Hunt discovery"""
        return asyncio.run(self.product_hunt_discovery(target_tools))

    def run_sync_alternativeto_discovery(self, target_tools: int = 3000) -> Dict[str, Any]:
        """Synchronous wrapper for AlternativeTo discovery"""
        return asyncio.run(self.alternativeto_discovery(target_tools))

    def run_sync_chrome_discovery(self, target_tools: int = 2000) -> Dict[str, Any]:
        """Synchronous wrapper for Chrome discovery"""
        return asyncio.run(self.chrome_extensions_discovery(target_tools))

    def run_sync_vscode_discovery(self, target_tools: int = 1500) -> Dict[str, Any]:
        """Synchronous wrapper for VS Code discovery"""
        return asyncio.run(self.vscode_extensions_discovery(target_tools))

    def run_sync_npm_discovery(self, target_tools: int = 2000) -> Dict[str, Any]:
        """Synchronous wrapper for NPM discovery"""
        return asyncio.run(self.npm_packages_discovery(target_tools))

    def run_sync_pypi_discovery(self, target_tools: int = 1500) -> Dict[str, Any]:
        """Synchronous wrapper for PyPI discovery"""
        return asyncio.run(self.pypi_packages_discovery(target_tools))

# Global service instance
external_data_service = ExternalDataService()
