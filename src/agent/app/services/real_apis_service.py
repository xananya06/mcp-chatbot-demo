# src/agent/app/services/real_apis_service.py
# ENHANCED VERSION - Adding Product Hunt, Reddit, and Crunchbase APIs

import asyncio
import aiohttp
import time
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.services.chat_service import save_discovered_tools_with_deduplication

class UnifiedRealAPIsService:
    """
    Unified Real APIs Service - ENHANCED with Product Hunt, Reddit, and Crunchbase
    All official APIs, no web scraping
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
            },
            # NEW: Product Hunt API
            'producthunt': {
                'client_id': os.getenv('PRODUCT_HUNT_CLIENT_ID'),
                'client_secret': os.getenv('PRODUCT_HUNT_CLIENT_SECRET'),
                'access_token': os.getenv('PRODUCT_HUNT_ACCESS_TOKEN'),
                'base_url': 'https://api.producthunt.com/v2/api/graphql',
                'oauth_url': 'https://api.producthunt.com/v2/oauth/token',
                'rate_limit': 1.0,
                'requests_per_hour': 1000,
                'auth_required': True,
                'quality': 'very_high'
            },
            # NEW: Reddit API
            'reddit': {
                'base_url': 'https://www.reddit.com',
                'rate_limit': 2.0,  # Reddit requires 2 second delays
                'requests_per_hour': 600,
                'auth_required': False,
                'quality': 'medium'
            },
            # NEW: Crunchbase API (basic endpoints)
            'crunchbase': {
                'api_key': os.getenv('CRUNCHBASE_API_KEY'),
                'base_url': 'https://api.crunchbase.com/api/v4',
                'rate_limit': 1.0,
                'requests_per_hour': 200,
                'auth_required': True,
                'quality': 'high'
            }
        }
        
    # ================================================================
    # MAIN DISCOVERY METHODS
    # ================================================================

    async def discover_all_real_apis(self, target_tools: int = 30000) -> Dict[str, Any]:
        """Discover from ALL real APIs including new ones"""
        
        results = {
            "discovery_id": f"unified_real_apis_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_discovered": 0,
            "total_saved": 0,
            "api_results": {},
            "processing_mode": "enhanced_real_apis_only"
        }
        
        print(f"🚀 ENHANCED UNIFIED REAL APIs DISCOVERY")
        print(f"🎯 Target: {target_tools} tools")
        print(f"✅ Enhanced with Product Hunt, Reddit, Crunchbase APIs")
        print(f"💰 Cost: $0")
        
        # Enhanced API tasks including new ones
        api_tasks = [
            ("Product Hunt API", self._discover_producthunt, 4000),  # NEW - High priority
            ("Hacker News API", self._discover_hackernews, 2000),
            ("Stack Overflow API", self._discover_stackoverflow, 3000), 
            ("GitHub API", self._discover_github, 5000),
            ("NPM Registry API", self._discover_npm, 3000),
            ("PyPI JSON API", self._discover_pypi, 2500),
            ("VS Code Marketplace API", self._discover_vscode, 2000),
            ("Reddit API", self._discover_reddit, 3000),  # NEW
            ("Crunchbase API", self._discover_crunchbase, 2000),  # NEW
            ("Dev.to API", self._discover_devto, 1500),
            ("Stack Exchange API", self._discover_stackexchange, 3000)
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
            headers={'User-Agent': 'AI Tool Discovery System v4.0 - Enhanced APIs'}
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
        
        print(f"\n🎊 ENHANCED REAL APIs DISCOVERY COMPLETE!")
        print(f"📈 RESULTS:")
        print(f"   • Total tools discovered: {results['total_discovered']}")
        print(f"   • Total tools saved: {results['total_saved']}")
        print(f"   • Successful APIs: {results['successful_apis']}")
        
        return results

    # ================================================================
    # NEW API DISCOVERY METHODS
    # ================================================================

    async def _discover_producthunt(self, session: aiohttp.ClientSession, max_tools: int = 4000) -> List[Dict[str, Any]]:
        """Product Hunt API v2 (GraphQL) - NEW"""
        
        tools = []
        
        # Get access token first
        access_token = await self._get_producthunt_token(session)
        if not access_token:
            print(f"    ❌ Product Hunt: Could not get access token")
            return tools
        
        print(f"    🎯 Product Hunt: Using GraphQL API v2")
        
        # GraphQL queries for different strategies
        queries = [
            {
                "name": "Today's Posts",
                "query": """
                    query TodayPosts($first: Int!) {
                        posts(first: $first) {
                            edges {
                                node {
                                    id name tagline description url website
                                    votesCount commentsCount featuredAt
                                    topics { edges { node { name } } }
                                    thumbnail { url }
                                }
                            }
                        }
                    }
                """,
                "variables": {"first": 20}
            },
            {
                "name": "AI Tools Search",
                "query": """
                    query SearchAI($first: Int!) {
                        posts(first: $first, postedAfter: "{}", order: VOTES_COUNT) {{
                            edges {{
                                node {{
                                    id name tagline description url website
                                    votesCount commentsCount featuredAt
                                    topics {{ edges {{ node {{ name }} }} }}
                                    thumbnail {{ url }}
                                }}
                            }}
                        }}
                    }}
                """.format((datetime.utcnow() - timedelta(days=30)).isoformat()),
                "variables": {"first": 30}
            }
        ]
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        for query_info in queries:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.apis['producthunt']['rate_limit'])
                
                payload = {
                    "query": query_info["query"],
                    "variables": query_info["variables"]
                }
                
                async with session.post(self.apis['producthunt']['base_url'], 
                                      json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "errors" not in data and "data" in data:
                            query_tools = self._parse_producthunt_response(data, query_info["name"])
                            tools.extend(query_tools)
                            print(f"      ✅ {query_info['name']}: {len(query_tools)} tools")
                        else:
                            print(f"      ⚠️ {query_info['name']}: GraphQL errors")
                    else:
                        print(f"      ❌ {query_info['name']}: HTTP {response.status}")
                        
            except Exception as e:
                print(f"      ❌ {query_info['name']}: {str(e)}")
                continue
        
        return tools[:max_tools]

    async def _get_producthunt_token(self, session: aiohttp.ClientSession) -> Optional[str]:
        """Get Product Hunt access token"""
        
        # Use existing token if available
        if self.apis['producthunt']['access_token']:
            return self.apis['producthunt']['access_token']
        
        # Get token via client credentials
        client_id = self.apis['producthunt']['client_id']
        client_secret = self.apis['producthunt']['client_secret']
        
        if not client_id or not client_secret:
            return None
        
        try:
            data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials"
            }
            
            async with session.post(self.apis['producthunt']['oauth_url'], json=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    return token_data.get("access_token")
        except Exception:
            pass
        
        return None

    def _parse_producthunt_response(self, data: Dict[str, Any], category: str) -> List[Dict[str, Any]]:
        """Parse Product Hunt GraphQL response"""
        
        tools = []
        
        try:
            posts = data.get("data", {}).get("posts", {})
            edges = posts.get("edges", [])
            
            for edge in edges:
                node = edge.get("node", {})
                
                name = node.get("name", "").strip()
                if not name or len(name) < 3:
                    continue
                
                # Get website (prefer actual website over PH URL)
                website = node.get("website", "").strip()
                if not website:
                    website = node.get("url", "").strip()
                
                # Build description
                tagline = node.get("tagline", "").strip()
                description = node.get("description", "").strip()
                full_description = tagline
                if description and description != tagline:
                    full_description = f"{tagline}. {description}"
                
                # Extract topics
                topics = []
                topic_edges = node.get("topics", {}).get("edges", [])
                for topic_edge in topic_edges:
                    topic_name = topic_edge.get("node", {}).get("name")
                    if topic_name:
                        topics.append(topic_name)
                
                # Build features
                features = []
                votes = node.get("votesCount", 0)
                comments = node.get("commentsCount", 0)
                if votes > 0:
                    features.append(f"{votes} votes")
                if comments > 0:
                    features.append(f"{comments} comments")
                if topics:
                    features.append(f"Topics: {', '.join(topics[:3])}")
                
                # Determine tool type
                tool_type = self._determine_ph_tool_type(topics, full_description)
                
                # Calculate confidence
                confidence = 0.8
                if votes > 50:
                    confidence += 0.1
                if votes > 100:
                    confidence += 0.1
                
                tool = {
                    "name": name,
                    "website": website,
                    "description": full_description[:500],
                    "tool_type": tool_type,
                    "category": f"Product Hunt - {category}",
                    "pricing": "Unknown",
                    "features": ". ".join(features),
                    "confidence": min(confidence, 1.0),
                    "source_data": json.dumps({
                        "source": "product_hunt_api_v2",
                        "votes": votes,
                        "comments": comments,
                        "topics": topics,
                        "featured_at": node.get("featuredAt")
                    })
                }
                
                tools.append(tool)
                
        except Exception as e:
            print(f"      ❌ Error parsing Product Hunt response: {e}")
        
        return tools

    def _determine_ph_tool_type(self, topics: List[str], description: str) -> str:
        """Determine tool type for Product Hunt tools"""
        
        topics_lower = [topic.lower() for topic in topics]
        desc_lower = description.lower()
        
        if any(term in topics_lower or term in desc_lower for term in [
            'artificial-intelligence', 'ai', 'machine-learning', 'automation'
        ]):
            return "ai_services"
        elif any(term in topics_lower or term in desc_lower for term in [
            'developer-tools', 'programming', 'coding'
        ]):
            return "ai_coding_tools"
        elif any(term in topics_lower or term in desc_lower for term in [
            'productivity', 'workflow'
        ]):
            return "productivity_tools"
        else:
            return "web_applications"

    async def _discover_reddit(self, session: aiohttp.ClientSession, max_tools: int = 3000) -> List[Dict[str, Any]]:
        """Reddit API - NEW"""
        
        tools = []
        
        print(f"    🔍 Reddit: Searching AI/tool subreddits")
        
        # Subreddits to search
        subreddits = [
            'artificial',
            'MachineLearning', 
            'programming',
            'webdev',
            'SideProject',
            'startups',
            'Entrepreneur',
            'productivity'
        ]
        
        for subreddit in subreddits:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.apis['reddit']['rate_limit'])
                
                # Use Reddit JSON API (no auth required)
                url = f"{self.apis['reddit']['base_url']}/r/{subreddit}/hot.json"
                params = {'limit': 25}
                
                headers = {'User-Agent': 'AI Tool Discovery Bot 1.0'}
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        subreddit_tools = self._parse_reddit_response(data, subreddit)
                        tools.extend(subreddit_tools)
                        print(f"      ✅ r/{subreddit}: {len(subreddit_tools)} tools")
                    else:
                        print(f"      ❌ r/{subreddit}: HTTP {response.status}")
                        
            except Exception as e:
                print(f"      ❌ r/{subreddit}: {str(e)}")
                continue
        
        return tools[:max_tools]

    def _parse_reddit_response(self, data: Dict[str, Any], subreddit: str) -> List[Dict[str, Any]]:
        """Parse Reddit API response"""
        
        tools = []
        
        try:
            posts = data.get("data", {}).get("children", [])
            
            for post in posts:
                post_data = post.get("data", {})
                
                title = post_data.get("title", "").strip()
                url = post_data.get("url", "").strip()
                selftext = post_data.get("selftext", "").strip()
                
                # Skip if no title or URL
                if not title or not url or len(title) < 10:
                    continue
                
                # Filter for tool-related posts
                title_lower = title.lower()
                tool_keywords = [
                    'tool', 'app', 'platform', 'service', 'api', 'library',
                    'framework', 'ai', 'automation', 'generator', 'built',
                    'created', 'launched', 'released'
                ]
                
                if not any(keyword in title_lower for keyword in tool_keywords):
                    continue
                
                # Skip reddit URLs
                if 'reddit.com' in url:
                    continue
                
                # Build description
                description = title
                if selftext and len(selftext) > 20:
                    description = f"{title}. {selftext[:200]}"
                
                tool = {
                    "name": title[:100],
                    "website": url,
                    "description": description[:500],
                    "tool_type": "web_applications",
                    "category": f"Reddit - r/{subreddit}",
                    "pricing": "Unknown",
                    "features": f"Reddit score: {post_data.get('score', 0)}",
                    "confidence": 0.6,
                    "source_data": json.dumps({
                        "source": "reddit_api",
                        "subreddit": subreddit,
                        "score": post_data.get("score", 0),
                        "created_utc": post_data.get("created_utc")
                    })
                }
                
                tools.append(tool)
                
        except Exception as e:
            print(f"      ❌ Error parsing Reddit response: {e}")
        
        return tools

    async def _discover_crunchbase(self, session: aiohttp.ClientSession, max_tools: int = 2000) -> List[Dict[str, Any]]:
        """Crunchbase API - NEW"""
        
        tools = []
        
        api_key = self.apis['crunchbase']['api_key']
        if not api_key:
            print(f"    ❌ Crunchbase: API key not configured")
            return tools
        
        print(f"    🏢 Crunchbase: Searching AI startups")
        
        try:
            # Search for AI-related organizations
            await asyncio.sleep(self.apis['crunchbase']['rate_limit'])
            
            url = f"{self.apis['crunchbase']['base_url']}/searches/organizations"
            
            headers = {
                'X-cb-user-key': api_key,
                'Content-Type': 'application/json'
            }
            
            # Search for AI companies
            search_data = {
                "field_ids": [
                    "identifier",
                    "name", 
                    "short_description",
                    "website",
                    "categories",
                    "funding_total",
                    "last_funding_at"
                ],
                "query": [
                    {
                        "type": "predicate",
                        "field_id": "categories",
                        "operator_id": "includes",
                        "values": ["artificial-intelligence", "machine-learning", "automation"]
                    }
                ],
                "limit": min(50, max_tools)
            }
            
            async with session.post(url, json=search_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    tools = self._parse_crunchbase_response(data)
                    print(f"      ✅ Crunchbase: {len(tools)} AI companies")
                else:
                    print(f"      ❌ Crunchbase: HTTP {response.status}")
                    
        except Exception as e:
            print(f"      ❌ Crunchbase: {str(e)}")
        
        return tools

    def _parse_crunchbase_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Crunchbase API response"""
        
        tools = []
        
        try:
            entities = data.get("entities", [])
            
            for entity in entities:
                properties = entity.get("properties", {})
                
                name = properties.get("name", "").strip()
                website = properties.get("website", {}).get("value", "").strip()
                description = properties.get("short_description", "").strip()
                
                if not name or not website or len(name) < 3:
                    continue
                
                # Get categories
                categories = []
                cat_data = properties.get("categories", [])
                for cat in cat_data:
                    if isinstance(cat, dict):
                        cat_name = cat.get("value", "")
                        if cat_name:
                            categories.append(cat_name)
                
                # Build features
                features = []
                funding = properties.get("funding_total", {})
                if funding and funding.get("value"):
                    features.append(f"Funding: ${funding['value']:,}")
                
                last_funding = properties.get("last_funding_at", {})
                if last_funding and last_funding.get("value"):
                    features.append(f"Last funding: {last_funding['value'][:10]}")
                
                if categories:
                    features.append(f"Categories: {', '.join(categories[:3])}")
                
                tool = {
                    "name": name,
                    "website": website,
                    "description": description[:500] if description else f"AI startup: {name}",
                    "tool_type": "ai_services",
                    "category": "Crunchbase - AI Startups",
                    "pricing": "Unknown",
                    "features": ". ".join(features),
                    "confidence": 0.85,
                    "source_data": json.dumps({
                        "source": "crunchbase_api",
                        "categories": categories,
                        "funding_total": funding.get("value") if funding else None
                    })
                }
                
                tools.append(tool)
                
        except Exception as e:
            print(f"      ❌ Error parsing Crunchbase response: {e}")
        
        return tools

    # ================================================================
    # EXISTING API METHODS (keeping your original methods)
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
        
        headers = {'User-Agent': 'AI Tool Discovery v4.0'}
        
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
        """NPM Registry Search API"""
        
        tools = []
        
        keywords = [
            'cli', 'tool', 'framework', 'library', 'utility', 'build-tool',
            'developer-tool', 'automation', 'testing', 'productivity'
        ]
        
        for keyword in keywords:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.apis['npm']['rate_limit'])
                
                url = f"{self.apis['npm']['base_url']}/-/v1/search"
                params = {
                    'text': keyword,
                    'size': 20,
                    'quality': 0.65,
                    'popularity': 0.98
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        keyword_tools = self._parse_npm_response(data, keyword)
                        tools.extend(keyword_tools)
                        
            except Exception as e:
                continue
        
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
        
        always_ready = ['hackernews', 'stackoverflow', 'npm', 'pypi', 'vscode', 'github', 'stackexchange', 'reddit']
        needs_token = {
            'devto': 'DEV_TO_TOKEN',
            'producthunt': 'PRODUCT_HUNT_CLIENT_ID',
            'crunchbase': 'CRUNCHBASE_API_KEY'
        }
        
        if api_key in always_ready:
            return True
        elif api_key in needs_token:
            env_var = needs_token[api_key]
            return bool(os.getenv(env_var))
        
        return False

    # ================================================================
    # PARSING METHODS (keeping your existing ones + new ones)
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
    # SYNC WRAPPERS FOR FASTAPI - INCLUDING NEW APIS
    # ================================================================

    def run_sync_discover_all_real_apis(self, target_tools: int = 30000) -> Dict[str, Any]:
        """Sync wrapper for all real APIs discovery including new ones"""
        return asyncio.run(self.discover_all_real_apis(target_tools))
    
    def run_sync_discover_no_auth_apis(self, target_tools: int = 15000) -> Dict[str, Any]:
        """Sync wrapper for no-auth APIs discovery"""
        return asyncio.run(self.discover_no_auth_apis(target_tools))
    
    def run_sync_discover_producthunt(self, target_tools: int = 4000) -> Dict[str, Any]:
        """Sync wrapper for Product Hunt only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v4.0'}
            ) as session:
                tools = await self._discover_producthunt(session, target_tools)
                
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
    
    def run_sync_discover_reddit(self, target_tools: int = 3000) -> Dict[str, Any]:
        """Sync wrapper for Reddit only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v4.0'}
            ) as session:
                tools = await self._discover_reddit(session, target_tools)
                
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
    
    def run_sync_discover_crunchbase(self, target_tools: int = 2000) -> Dict[str, Any]:
        """Sync wrapper for Crunchbase only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v4.0'}
            ) as session:
                tools = await self._discover_crunchbase(session, target_tools)
                
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

    # Keep your existing sync wrappers
    def run_sync_discover_hackernews(self, target_tools: int = 2500) -> Dict[str, Any]:
        """Sync wrapper for Hacker News only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v4.0'}
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

    def run_sync_discover_github(self, target_tools: int = 6000) -> Dict[str, Any]:
        """Sync wrapper for GitHub only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v4.0'}
            ) as session:
                tools = await self._discover_github(session, target_tools)
                
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
        """Sync wrapper for NPM only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v4.0'}
            ) as session:
                tools = await self._discover_npm(session, target_tools)
                
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

    def run_sync_discover_pypi(self, target_tools: int = 3000) -> Dict[str, Any]:
        """Sync wrapper for PyPI only"""
        async def _run():
            results = {
                "start_time": datetime.utcnow().isoformat(),
                "total_saved": 0
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI Tool Discovery System v4.0'}
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

    async def discover_no_auth_apis(self, target_tools: int = 15000) -> Dict[str, Any]:
        """Discover from APIs that need NO authentication - ENHANCED"""
        
        results = {
            "discovery_id": f"no_auth_apis_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_saved": 0
        }
        
        print(f"⚡ ENHANCED NO-AUTH APIs DISCOVERY")
        print(f"🎯 Target: {target_tools} tools")
        
        # APIs that work immediately (including Reddit)
        no_auth_tasks = [
            ("Hacker News", self._discover_hackernews, 2500),
            ("Stack Overflow", self._discover_stackoverflow, 3000),
            ("NPM Registry", self._discover_npm, 3000),
            ("PyPI JSON", self._discover_pypi, 2500),
            ("VS Code Marketplace", self._discover_vscode, 2000),
            ("Reddit", self._discover_reddit, 2000)  # NEW - No auth required
        ]
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AI Tool Discovery System v4.0'}
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

# Global instance
unified_apis_service = UnifiedRealAPIsService()