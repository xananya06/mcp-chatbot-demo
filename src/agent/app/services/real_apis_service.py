# src/agent/app/services/real_apis_service.py
# COMPLETE FIXED VERSION - All issues resolved

import asyncio
import aiohttp
import time
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.services.chat_service import save_discovered_tools_with_deduplication

class UnifiedRealAPIsService:
    """
    Unified Real APIs Service - NO WEB SCRAPING
    FIXED: All session management and method issues resolved
    """
    
    def __init__(self):
        # Real API configurations - NO SCRAPING
        self.apis = {
            'hackernews': {
                'base_url': 'https://hacker-news.firebaseio.com/v0',
                'rate_limit': 0.1,
                'requests_per_hour': 10000,
                'auth_required': False,
                'quality': 'very_high'
            },
            'stackoverflow': {
                'base_url': 'https://api.stackexchange.com/2.3',
                'rate_limit': 0.1,
                'requests_per_hour': 300,
                'auth_required': False,
                'quality': 'high'
            },
            'pypi': {
                'base_url': 'https://pypi.org',
                'rate_limit': 0.3,
                'requests_per_hour': 1000,
                'auth_required': False,
                'quality': 'medium'
            },
            'npm': {
                'base_url': 'https://registry.npmjs.org',
                'rate_limit': 0.2,
                'requests_per_hour': 3600,
                'auth_required': False,
                'quality': 'medium'
            },
            'vscode': {
                'base_url': 'https://marketplace.visualstudio.com/_apis/public/gallery',
                'rate_limit': 0.5,
                'requests_per_hour': 3600,
                'auth_required': False,
                'quality': 'high'
            },
            'github': {
                'token': os.getenv('GITHUB_TOKEN'),
                'base_url': 'https://api.github.com',
                'rate_limit': 0.1 if os.getenv('GITHUB_TOKEN') else 1.0,
                'requests_per_hour': 5000 if os.getenv('GITHUB_TOKEN') else 60,
                'auth_required': False,
                'quality': 'high'
            },
            'devto': {
                'token': os.getenv('DEV_TO_TOKEN'),
                'base_url': 'https://dev.to/api',
                'rate_limit': 0.5,
                'requests_per_hour': 1000,
                'auth_required': True,
                'quality': 'high'
            },
            'stackexchange': {
                'key': os.getenv('STACKEXCHANGE_KEY'),
                'base_url': 'https://api.stackexchange.com/2.3',
                'rate_limit': 0.1,
                'requests_per_hour': 10000,
                'auth_required': False,
                'quality': 'high'
            }
        }
        
    # ================================================================
    # MAIN DISCOVERY METHODS
    # ================================================================

    async def discover_all_real_apis(self, target_tools: int = 30000) -> Dict[str, Any]:
        """Discover from ALL real APIs - no scraping"""
        
        results = {
            "discovery_id": f"unified_real_apis_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_discovered": 0,
            "total_saved": 0,
            "api_results": {},
            "processing_mode": "real_apis_only_no_scraping"
        }
        
        print(f"🚀 UNIFIED REAL APIs DISCOVERY")
        print(f"🎯 Target: {target_tools} tools")
        print(f"✅ Real APIs only - NO web scraping")
        print(f"💰 Cost: $0")
        
        # All real API tasks (no scraping)
        api_tasks = [
            ("Hacker News API", self._discover_hackernews, 2500),
            ("Stack Overflow API", self._discover_stackoverflow, 4000), 
            ("GitHub API", self._discover_github, 6000),
            ("NPM Registry API", self._discover_npm, 4000),
            ("PyPI JSON API", self._discover_pypi, 3000),
            ("VS Code Marketplace API", self._discover_vscode, 2000),
            ("Dev.to API", self._discover_devto, 2000),
            ("Stack Exchange API", self._discover_stackexchange, 3500)
        ]
        
        # Check API readiness
        ready_apis = []
        for api_name, discovery_func, max_tools in api_tasks:
            api_key = api_name.lower().replace(' api', '').replace(' ', '')
            if self._is_api_ready(api_key):
                ready_apis.append((api_name, discovery_func, max_tools))
            else:
                print(f"⚠️  {api_name}: Not configured (will skip)")
        
        print(f"✅ Ready APIs: {len(ready_apis)}/{len(api_tasks)}")
        
        # Create session properly
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AI Tool Discovery System v3.0 - Real APIs Only'}
        ) as session:
            
            all_tools = []
            
            # Process each API
            for api_name, discovery_func, max_tools in ready_apis:
                if results["total_discovered"] >= target_tools:
                    print(f"🎉 TARGET REACHED! {results['total_discovered']} tools")
                    break
                    
                print(f"\n📡 Processing: {api_name}")
                start_time = time.time()
                
                try:
                    tools = await discovery_func(session, max_tools)
                    processing_time = time.time() - start_time
                    
                    results["api_results"][api_name] = {
                        "tools_discovered": len(tools),
                        "processing_time": round(processing_time, 2),
                        "success": True,
                        "api_type": "real_api"
                    }
                    
                    results["total_discovered"] += len(tools)
                    all_tools.extend(tools)
                    
                    print(f"  ✅ {api_name}: {len(tools)} tools ({processing_time:.1f}s)")
                    
                except Exception as e:
                    print(f"  ❌ {api_name} failed: {str(e)}")
                    results["api_results"][api_name] = {
                        "error": str(e),
                        "tools_discovered": 0,
                        "success": False
                    }
        
        # Save all tools to database
        if all_tools:
            print(f"\n💾 Saving {len(all_tools)} tools to database...")
            db = SessionLocal()
            try:
                save_result = save_discovered_tools_with_deduplication(db, all_tools)
                results["total_saved"] = save_result.get("saved", 0)
                results["total_updated"] = save_result.get("updated", 0)
                results["database_result"] = save_result
            finally:
                db.close()
        
        results["end_time"] = datetime.utcnow().isoformat()
        results["successful_apis"] = len([r for r in results["api_results"].values() if r.get("success")])
        
        print(f"\n🎊 UNIFIED REAL APIs DISCOVERY COMPLETE!")
        print(f"📈 RESULTS:")
        print(f"   • Total tools discovered: {results['total_discovered']}")
        print(f"   • Total tools saved: {results['total_saved']}")
        print(f"   • Successful APIs: {results['successful_apis']}")
        
        return results

    async def discover_no_auth_apis(self, target_tools: int = 15000) -> Dict[str, Any]:
        """Discover from APIs that need NO authentication"""
        
        results = {
            "discovery_id": f"no_auth_apis_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_saved": 0
        }
        
        print(f"⚡ NO-AUTH APIs DISCOVERY")
        print(f"🎯 Target: {target_tools} tools")
        
        # APIs that work immediately
        no_auth_tasks = [
            ("Hacker News", self._discover_hackernews, 2500),
            ("Stack Overflow", self._discover_stackoverflow, 4000),
            ("NPM Registry", self._discover_npm, 4000),
            ("PyPI JSON", self._discover_pypi, 3000),
            ("VS Code Marketplace", self._discover_vscode, 2000)
        ]
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AI Tool Discovery System v3.0'}
        ) as session:
            
            all_tools = []
            
            for api_name, discovery_func, max_tools in no_auth_tasks:
                if len(all_tools) >= target_tools:
                    break
                    
                print(f"\n📡 Processing: {api_name}")
                
                try:
                    tools = await discovery_func(session, max_tools)
                    all_tools.extend(tools)
                    print(f"  ✅ {api_name}: {len(tools)} tools")
                    
                except Exception as e:
                    print(f"  ❌ {api_name} failed: {e}")
        
        # Save to database
        if all_tools:
            db = SessionLocal()
            try:
                save_result = save_discovered_tools_with_deduplication(db, all_tools)
                results["total_saved"] = save_result.get("saved", 0)
            finally:
                db.close()
        
        results["end_time"] = datetime.utcnow().isoformat()
        return results

    # ================================================================
    # INDIVIDUAL API DISCOVERY METHODS
    # ================================================================

    async def _discover_hackernews(self, session: aiohttp.ClientSession, max_tools: int = 2500) -> List[Dict[str, Any]]:
        """Hacker News Firebase API"""
        
        tools = []
        
        try:
            print(f"    🔍 Fetching Hacker News top stories...")
            
            url = f"{self.apis['hackernews']['base_url']}/topstories.json"
            
            async with session.get(url) as response:
                if response.status == 200:
                    story_ids = await response.json()
                    print(f"    📄 Found {len(story_ids)} top stories")
                    
                    for i, story_id in enumerate(story_ids[:50]):  # Process first 50
                        if len(tools) >= max_tools:
                            break
                            
                        await asyncio.sleep(self.apis['hackernews']['rate_limit'])
                        
                        story_url = f"{self.apis['hackernews']['base_url']}/item/{story_id}.json"
                        
                        async with session.get(story_url) as story_response:
                            if story_response.status == 200:
                                story = await story_response.json()
                                tool = self._parse_hackernews_story(story)
                                if tool:
                                    tools.append(tool)
                            
        except Exception as e:
            print(f"    ❌ Hacker News error: {e}")
        
        return tools

    async def _discover_stackoverflow(self, session: aiohttp.ClientSession, max_tools: int = 4000) -> List[Dict[str, Any]]:
        """Stack Overflow Questions API"""
        
        tools = []
        tags = ['tools', 'javascript', 'python', 'productivity']
        
        for tag in tags:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.apis['stackoverflow']['rate_limit'])
                
                url = f"{self.apis['stackoverflow']['base_url']}/questions"
                params = {
                    'order': 'desc',
                    'sort': 'votes',
                    'tagged': tag,
                    'site': 'stackoverflow',
                    'pagesize': 50,
                    'filter': 'withbody'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        tag_tools = self._parse_stackoverflow_questions(data, tag)
                        tools.extend(tag_tools)
                        
            except Exception as e:
                continue
        
        return tools
    
    async def _discover_github(self, session: aiohttp.ClientSession, max_tools: int = 6000) -> List[Dict[str, Any]]:
        """GitHub Repository Search API"""
        
        tools = []
        
        search_queries = [
            "ai tool stars:>50", "developer-tools stars:>100", "cli tool stars:>40",
            "automation tool stars:>60", "productivity stars:>80", "testing tool stars:>30"
        ]
        
        headers = {'User-Agent': 'AI Tool Discovery v3.0'}
        
        if self.apis['github']['token']:
            headers['Authorization'] = f"token {self.apis['github']['token']}"
        
        for query in search_queries:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.apis['github']['rate_limit'])
                
                url = f"{self.apis['github']['base_url']}/search/repositories"
                params = {
                    'q': query,
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 100
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for repo in data.get('items', []):
                            if len(tools) >= max_tools:
                                break
                                
                            tool = self._parse_github_repo(repo)
                            if tool:
                                tools.append(tool)
                                
                    elif response.status == 403:
                        await asyncio.sleep(60)
                        
            except Exception as e:
                continue
        
        return tools

    async def _discover_npm(self, session: aiohttp.ClientSession, max_tools: int = 4000) -> List[Dict[str, Any]]:
        """NPM Registry Search API - ENHANCED"""
        
        tools = []
        
        # Enhanced keywords for better discovery
        keywords = [
            'cli', 'tool', 'framework', 'library', 'utility', 'build-tool',
            'developer-tool', 'automation', 'testing', 'productivity'
        ]
        
        print(f"    🚀 Processing {len(keywords)} NPM keywords for package discovery")
        
        for i, keyword in enumerate(keywords):
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.apis['npm']['rate_limit'])
                
                url = f"{self.apis['npm']['base_url']}/-/v1/search"
                params = {
                    'text': keyword,
                    'size': 20,  # Reasonable size
                    'quality': 0.65,
                    'popularity': 0.98
                }
                
                print(f"    📦 NPM searching: {keyword}")
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        keyword_tools = self._parse_npm_response(data, keyword)
                        tools.extend(keyword_tools)
                        print(f"    ✅ NPM '{keyword}': {len(keyword_tools)} packages")
                        
                        if (i + 1) % 3 == 0:  # Progress every 3 keywords
                            print(f"    📊 NPM Progress: {i+1}/{len(keywords)} keywords, {len(tools)} packages found")
                    else:
                        print(f"    ⚠️  NPM keyword '{keyword}': HTTP {response.status}")
                        
            except Exception as e:
                print(f"    ❌ NPM keyword '{keyword}' failed: {e}")
                continue
        
        print(f"    ✅ NPM Enhanced: {len(tools)} total packages from {len(keywords)} keywords")
        return tools

    async def _discover_pypi(self, session: aiohttp.ClientSession, max_tools: int = 3000) -> List[Dict[str, Any]]:
        """PyPI JSON API"""
        
        tools = []
        packages = ['click', 'flask', 'fastapi', 'pytest', 'requests', 'django', 'pandas', 'numpy']
        
        for package in packages:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.apis['pypi']['rate_limit'])
                
                url = f"{self.apis['pypi']['base_url']}/pypi/{package}/json"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        tool = self._parse_pypi_package(data, package)
                        if tool:
                            tools.append(tool)
                            
            except Exception as e:
                continue
        
        return tools

    async def _discover_vscode(self, session: aiohttp.ClientSession, max_tools: int = 2000) -> List[Dict[str, Any]]:
        """VS Code Marketplace API"""
        
        tools = []
        search_terms = ['productivity', 'git', 'python', 'javascript']
        
        for term in search_terms:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.apis['vscode']['rate_limit'])
                
                url = f"{self.apis['vscode']['base_url']}/extensionquery"
                
                body = {
                    "filters": [{
                        "criteria": [
                            {"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                            {"filterType": 10, "value": term}
                        ],
                        "pageSize": 50
                    }],
                    "flags": 914
                }
                
                headers = {'Content-Type': 'application/json'}
                
                async with session.post(url, json=body, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        term_tools = self._parse_vscode_response(data, term)
                        tools.extend(term_tools)
                        
            except Exception as e:
                continue
        
        return tools

    async def _discover_devto(self, session: aiohttp.ClientSession, max_tools: int = 2000) -> List[Dict[str, Any]]:
        """Dev.to Articles API"""
        
        if not self.apis['devto']['token']:
            return []
        
        tools = []
        tags = ['tools', 'productivity']
        
        for tag in tags:
            try:
                await asyncio.sleep(self.apis['devto']['rate_limit'])
                
                url = f"{self.apis['devto']['base_url']}/articles"
                params = {'tag': tag, 'per_page': 20}
                headers = {'api-key': self.apis['devto']['token']}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        articles = await response.json()
                        tag_tools = self._parse_devto_articles(articles, tag)
                        tools.extend(tag_tools)
                        
            except Exception as e:
                continue
        
        return tools

    async def _discover_stackexchange(self, session: aiohttp.ClientSession, max_tools: int = 3500) -> List[Dict[str, Any]]:
        """Stack Exchange Network API"""
        
        tools = []
        
        try:
            await asyncio.sleep(self.apis['stackexchange']['rate_limit'])
            
            url = f"{self.apis['stackexchange']['base_url']}/questions"
            params = {
                'order': 'desc',
                'sort': 'votes',
                'tagged': 'tools',
                'site': 'stackoverflow',
                'pagesize': 25
            }
            
            if self.apis['stackexchange']['key']:
                params['key'] = self.apis['stackexchange']['key']
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    tools = self._parse_stackexchange_questions(data, 'stackoverflow', 'tools')
                    
        except Exception as e:
            pass
        
        return tools

    # ================================================================
    # HELPER METHODS
    # ================================================================

    def _is_api_ready(self, api_key: str) -> bool:
        """Check if API is configured and ready"""
        
        always_ready = ['hackernews', 'stackoverflow', 'npm', 'pypi', 'vscode', 'github', 'stackexchange']
        needs_token = {'devto': 'DEV_TO_TOKEN'}
        
        if api_key in always_ready:
            return True
        elif api_key in needs_token:
            return bool(os.getenv(needs_token[api_key]))
        
        return False

    # ================================================================
    # PARSING METHODS
    # ================================================================

    def _parse_hackernews_story(self, story: dict) -> Optional[Dict[str, Any]]:
        """Parse HN story"""
        try:
            title = story.get('title', '')
            url = story.get('url', '')
            
            tool_keywords = ['tool', 'app', 'service', 'show hn', 'launch']
            
            if any(k in title.lower() for k in tool_keywords) and url:
                return {
                    "name": title[:100],
                    "website": url,
                    "description": f"Hacker News: {title}",
                    "tool_type": "ai_services",
                    "category": "Hacker News",
                    "pricing": "Unknown",
                    "features": f"HN Score: {story.get('score', 0)}",
                    "confidence": 0.9,
                    "source_data": json.dumps({
                        "source": "hackernews_api",
                        "score": story.get('score', 0)
                    })
                }
        except:
            pass
        return None

    def _parse_stackoverflow_questions(self, data: dict, tag: str) -> List[Dict[str, Any]]:
        """Parse SO questions"""
        tools = []
        
        for question in data.get('items', []):
            title = question.get('title', '')
            
            if any(k in title.lower() for k in ['tool', 'best', 'recommend']):
                tools.append({
                    "name": title[:100],
                    "website": question.get('link', ''),
                    "description": f"SO discussion: {title[:150]}",
                    "tool_type": "ai_coding_tools",
                    "category": f"Stack Overflow {tag}",
                    "pricing": "Discussion",
                    "features": f"SO Score: {question.get('score', 0)}",
                    "confidence": 0.7,
                    "source_data": json.dumps({
                        "source": "stackoverflow_api",
                        "tag": tag
                    })
                })
        
        return tools

    def _parse_github_repo(self, repo: dict) -> Optional[Dict[str, Any]]:
        """Parse GitHub repo"""
        try:
            return {
                "name": repo['name'],
                "website": repo['html_url'],
                "description": repo.get('description', ''),
                "tool_type": "ai_services",
                "category": "Open Source",
                "pricing": "Open Source",
                "features": f"Stars: {repo['stargazers_count']}",
                "confidence": 0.8,
                "source_data": json.dumps({
                    "source": "github_api",
                    "stars": repo['stargazers_count']
                })
            }
        except:
            pass
        return None

    def _parse_npm_response(self, data: dict, keyword: str) -> List[Dict[str, Any]]:
        """Parse NPM response"""
        tools = []
        
        for pkg in data.get('objects', []):
            package_data = pkg.get('package', {})
            name = package_data.get('name', '')
            
            if name:
                tools.append({
                    "name": name,
                    "website": f"https://www.npmjs.com/package/{name}",
                    "description": package_data.get('description', ''),
                    "tool_type": "web_applications",
                    "category": "NPM Package",
                    "pricing": "Open Source",
                    "features": f"NPM, {keyword}",
                    "confidence": 0.75,
                    "source_data": json.dumps({
                        "source": "npm_api",
                        "keyword": keyword
                    })
                })
        
        return tools

    def _parse_pypi_package(self, data: dict, package: str) -> Optional[Dict[str, Any]]:
        """Parse PyPI package"""
        try:
            info = data.get('info', {})
            
            return {
                "name": info.get('name', package),
                "website": f"https://pypi.org/project/{package}/",
                "description": info.get('summary', ''),
                "tool_type": "ai_coding_tools",
                "category": "Python Package",
                "pricing": "Open Source",
                "features": f"Python, v{info.get('version', '')}",
                "confidence": 0.8,
                "source_data": json.dumps({
                    "source": "pypi_json_api",
                    "version": info.get('version', '')
                })
            }
        except:
            pass
        return None

    def _parse_vscode_response(self, data: dict, term: str) -> List[Dict[str, Any]]:
        """Parse VS Code response"""
        tools = []
        
        try:
            extensions = data.get('results', [{}])[0].get('extensions', [])
            
            for ext in extensions:
                name = ext.get('displayName', '')
                if name:
                    tools.append({
                        "name": f"{name} (VS Code)",
                        "website": f"https://marketplace.visualstudio.com/items?itemName={ext.get('extensionName', '')}",
                        "description": ext.get('shortDescription', ''),
                        "tool_type": "code_editors",
                        "category": "VS Code Extension",
                        "pricing": "Free",
                        "features": f"VS Code, {term}",
                        "confidence": 0.85,
                        "source_data": json.dumps({
                            "source": "vscode_api",
                            "term": term
                        })
                    })
        except:
            pass
        
        return tools

    def _parse_devto_articles(self, articles: List[dict], tag: str) -> List[Dict[str, Any]]:
        """Parse Dev.to articles"""
        tools = []
        
        for article in articles:
            title = article.get('title', '')
            
            if any(k in title.lower() for k in ['tool', 'best', 'guide']):
                tools.append({
                    "name": title[:100],
                    "website": article.get('url', ''),
                    "description": article.get('description', ''),
                    "tool_type": "ai_coding_tools",
                    "category": f"Dev.to {tag}",
                    "pricing": "Article",
                    "features": f"Dev.to, {article.get('positive_reactions_count', 0)} reactions",
                    "confidence": 0.75,
                    "source_data": json.dumps({
                        "source": "devto_api",
                        "tag": tag
                    })
                })
        
        return tools

    def _parse_stackexchange_questions(self, data: dict, site: str, tag: str) -> List[Dict[str, Any]]:
        """Parse Stack Exchange questions"""
        tools = []
        
        for question in data.get('items', []):
            title = question.get('title', '')
            
            if any(k in title.lower() for k in ['tool', 'software', 'recommend']):
                tools.append({
                    "name": title[:100],
                    "website": question.get('link', ''),
                    "description": f"{site} discussion: {title[:150]}",
                    "tool_type": "productivity_tools",
                    "category": f"{site.title()} {tag}",
                    "pricing": "Discussion",
                    "features": f"Score: {question.get('score', 0)}",
                    "confidence": 0.7,
                    "source_data": json.dumps({
                        "source": "stackexchange_api",
                        "site": site,
                        "tag": tag
                    })
                })
        
        return tools

    # ================================================================
    # SYNC WRAPPERS FOR FASTAPI - ALL METHODS INCLUDED
    # ================================================================

    def run_sync_discover_all_real_apis(self, target_tools: int = 30000) -> Dict[str, Any]:
        """Sync wrapper for all real APIs discovery"""
        return asyncio.run(self.discover_all_real_apis(target_tools))
    
    def run_sync_discover_no_auth_apis(self, target_tools: int = 15000) -> Dict[str, Any]:
        """Sync wrapper for no-auth APIs discovery"""
        return asyncio.run(self.discover_no_auth_apis(target_tools))
    
    def run_sync_discover_hackernews(self, target_tools: int = 2500) -> Dict[str, Any]:
        """Sync wrapper for Hacker News only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v3.0'}
            ) as session:
                tools = await self._discover_hackernews(session, target_tools)
                
                if tools:
                    db = SessionLocal()
                    try:
                        save_result = save_discovered_tools_with_deduplication(db, tools)
                        results["total_saved"] = save_result.get("saved", 0)
                    finally:
                        db.close()
            
            results["end_time"] = datetime.utcnow().isoformat()
            return results
        
        return asyncio.run(_run())
    
    def run_sync_discover_stackoverflow(self, target_tools: int = 4000) -> Dict[str, Any]:
        """Sync wrapper for Stack Overflow only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v3.0'}
            ) as session:
                tools = await self._discover_stackoverflow(session, target_tools)
                
                if tools:
                    db = SessionLocal()
                    try:
                        save_result = save_discovered_tools_with_deduplication(db, tools)
                        results["total_saved"] = save_result.get("saved", 0)
                    finally:
                        db.close()
            
            results["end_time"] = datetime.utcnow().isoformat()
            return results
        
        return asyncio.run(_run())
    
    def run_sync_discover_github(self, target_tools: int = 6000) -> Dict[str, Any]:
        """Sync wrapper for GitHub only - FIXED"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v3.0'}
            ) as session:
                tools = await self._discover_github(session, target_tools)
                
                print(f"DEBUG: GitHub found {len(tools)} tools")
                
                if tools:
                    db = SessionLocal()
                    try:
                        save_result = save_discovered_tools_with_deduplication(db, tools)
                        results["total_saved"] = save_result.get("saved", 0)
                        results["total_updated"] = save_result.get("updated", 0)
                        results["database_result"] = save_result
                        print(f"DEBUG: Database save result: {save_result}")
                    except Exception as e:
                        print(f"DEBUG: Database save error: {e}")
                        results["database_error"] = str(e)
                    finally:
                        db.close()
                else:
                    print("DEBUG: No tools found by GitHub API")
            
            results["end_time"] = datetime.utcnow().isoformat()
            return results
        
        return asyncio.run(_run())
    
    def run_sync_discover_pypi(self, target_tools: int = 3000) -> Dict[str, Any]:
        """Sync wrapper for PyPI JSON API only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0,
                "improvement": "Real PyPI JSON API - no scraping"
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v3.0'}
            ) as session:
                tools = await self._discover_pypi(session, target_tools)
                
                if tools:
                    db = SessionLocal()
                    try:
                        save_result = save_discovered_tools_with_deduplication(db, tools)
                        results["total_saved"] = save_result.get("saved", 0)
                    finally:
                        db.close()
            
            results["end_time"] = datetime.utcnow().isoformat()
            return results
        
        return asyncio.run(_run())

    def run_sync_discover_npm(self, target_tools: int = 4000) -> Dict[str, Any]:
        """Sync wrapper for NPM only - FIXED WITH DEBUG"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v3.0'}
            ) as session:
                tools = await self._discover_npm(session, target_tools)
                
                print(f"DEBUG: NPM found {len(tools)} tools")
                
                if tools:
                    db = SessionLocal()
                    try:
                        save_result = save_discovered_tools_with_deduplication(db, tools)
                        results["total_saved"] = save_result.get("saved", 0)
                        results["total_updated"] = save_result.get("updated", 0)
                        results["database_result"] = save_result
                        print(f"DEBUG: NPM save result: {save_result}")
                    except Exception as e:
                        print(f"DEBUG: NPM save error: {e}")
                        results["database_error"] = str(e)
                    finally:
                        db.close()
                else:
                    print("DEBUG: NPM found no tools")
            
            results["end_time"] = datetime.utcnow().isoformat()
            return results
        
        return asyncio.run(_run())

    def run_sync_discover_vscode(self, target_tools: int = 2000) -> Dict[str, Any]:
        """Sync wrapper for VS Code only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v3.0'}
            ) as session:
                tools = await self._discover_vscode(session, target_tools)
                
                if tools:
                    db = SessionLocal()
                    try:
                        save_result = save_discovered_tools_with_deduplication(db, tools)
                        results["total_saved"] = save_result.get("saved", 0)
                    finally:
                        db.close()
            
            results["end_time"] = datetime.utcnow().isoformat()
            return results
        
        return asyncio.run(_run())

    def run_sync_discover_devto(self, target_tools: int = 2000) -> Dict[str, Any]:
        """Sync wrapper for Dev.to only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v3.0'}
            ) as session:
                tools = await self._discover_devto(session, target_tools)
                
                if tools:
                    db = SessionLocal()
                    try:
                        save_result = save_discovered_tools_with_deduplication(db, tools)
                        results["total_saved"] = save_result.get("saved", 0)
                    finally:
                        db.close()
            
            results["end_time"] = datetime.utcnow().isoformat()
            return results
        
        return asyncio.run(_run())

    def run_sync_discover_stackexchange(self, target_tools: int = 3500) -> Dict[str, Any]:
        """Sync wrapper for Stack Exchange only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v3.0'}
            ) as session:
                tools = await self._discover_stackexchange(session, target_tools)
                
                if tools:
                    db = SessionLocal()
                    try:
                        save_result = save_discovered_tools_with_deduplication(db, tools)
                        results["total_saved"] = save_result.get("saved", 0)
                    finally:
                        db.close()
            
            results["end_time"] = datetime.utcnow().isoformat()
            return results
        
        return asyncio.run(_run())


# ================================================================
# GLOBAL SERVICE INSTANCE
# ================================================================

unified_apis_service = UnifiedRealAPIsService()