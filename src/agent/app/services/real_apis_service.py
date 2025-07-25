#!/usr/bin/env python3
# src/agent/app/services/real_apis_service.py
# Complete Real APIs Discovery Service - All-in-One File
# Following the same pattern as ai_directory_service.py

import asyncio
import aiohttp
import requests
import time
import logging
import re
import json
import os
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
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
class APITool:
    """Data class for discovered API tools"""
    name: str
    description: str
    website: str
    category: str
    source: str
    pricing: Optional[str] = None
    features: List[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.metadata is None:
            self.metadata = {}

class UnifiedRealAPIsService:
    """
    Complete Real APIs Discovery Service
    Discovers tools from GitHub, NPM, Reddit, Product Hunt, etc.
    All-in-one file following ai_directory_service.py pattern
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI Tool Discovery System v4.0 - Real APIs',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        })
        
        # Rate limiting
        self.request_delay = 1.0  # Base delay between requests
        self.last_request_time = {}
        
        # API configurations
        self.apis = {
            'github': {
                'base_url': 'https://api.github.com',
                'token': os.getenv('GITHUB_TOKEN'),
                'rate_limit': 1.0
            },
            'npm': {
                'base_url': 'https://registry.npmjs.org',
                'rate_limit': 0.5
            },
            'reddit': {
                'base_url': 'https://www.reddit.com',
                'rate_limit': 2.0
            },
            'hackernews': {
                'base_url': 'https://hacker-news.firebaseio.com/v0',
                'rate_limit': 0.1
            },
            'stackoverflow': {
                'base_url': 'https://api.stackexchange.com/2.3',
                'rate_limit': 0.1
            },
            'producthunt': {
                'base_url': 'https://api.producthunt.com/v2/api/graphql',
                'client_id': os.getenv('PRODUCT_HUNT_CLIENT_ID'),
                'client_secret': os.getenv('PRODUCT_HUNT_CLIENT_SECRET'),
                'access_token': os.getenv('PRODUCT_HUNT_ACCESS_TOKEN'),
                'rate_limit': 2.0
            },
            'crunchbase': {
                'base_url': 'https://api.crunchbase.com/api/v4',
                'api_key': os.getenv('CRUNCHBASE_API_KEY'),
                'rate_limit': 3.0
            },
            'pypi': {
                'base_url': 'https://pypi.org',
                'rate_limit': 0.5
            },
            'vscode': {
                'base_url': 'https://marketplace.visualstudio.com/_apis/public/gallery',
                'rate_limit': 1.0
            }
        }
        
        self.stats = {
            'total_discovered': 0,
            'total_saved': 0,
            'total_duplicates': 0,
            'total_errors': 0
        }
    
    def _rate_limit(self, api_name: str):
        """Implement rate limiting per API"""
        current_time = time.time()
        last_time = self.last_request_time.get(api_name, 0)
        rate_limit = self.apis.get(api_name, {}).get('rate_limit', self.request_delay)
        
        time_since_last = current_time - last_time
        if time_since_last < rate_limit:
            sleep_time = rate_limit - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time[api_name] = time.time()
    
    def _safe_request(self, url: str, headers: Dict = None, params: Dict = None, timeout: int = 15) -> Optional[Dict]:
        """Make a safe HTTP request with error handling"""
        try:
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            logger.debug(f"  📡 Fetching: {url}")
            
            response = self.session.get(url, headers=request_headers, params=params, timeout=timeout)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' in content_type:
                return response.json()
            else:
                logger.warning(f"  ⚠️ Non-JSON response from {url}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  ❌ Request failed for {url}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"  ❌ JSON decode error for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"  ❌ Unexpected error for {url}: {str(e)}")
            return None
    
    def _convert_to_discovered_tool(self, api_tool: APITool) -> DiscoveredTool:
        """Convert APITool to DiscoveredTool database model"""
        
        # Determine tool type based on source and URL
        tool_type = "web_application"
        if api_tool.source == "github":
            tool_type = "github_repo"
        elif api_tool.source == "npm":
            tool_type = "npm_package"
        elif api_tool.source == "pypi":
            tool_type = "pypi_package"
        elif "cli" in api_tool.description.lower() or "command" in api_tool.description.lower():
            tool_type = "cli_tool"
        elif "api" in api_tool.description.lower():
            tool_type = "api_service"
        
        return DiscoveredTool(
            name=api_tool.name,
            description=api_tool.description,
            website=api_tool.website,
            category=api_tool.category,
            tool_type=tool_type,  # Use the existing 'tool_type' field
            tool_type_detected=tool_type,  # Also set the detected type
            pricing=api_tool.pricing,  # Use 'pricing' field (it's Text type)
            features=", ".join(api_tool.features) if api_tool.features else "",
            confidence_score=api_tool.confidence,
            website_status=200,  # Assume working since we got data from API
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            source_data=json.dumps(api_tool.metadata) if api_tool.metadata else None
        )
    
    def _save_tools_to_database(self, tools: List[APITool]) -> Dict[str, int]:
        """Save discovered tools to database"""
        
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
    
    # ================================================================
    # GITHUB API DISCOVERY
    # ================================================================
    
    def _discover_github(self, limit: int = 200) -> List[APITool]:
        """Discover tools from GitHub API"""
        tools = []
        
        try:
            logger.info(f"🐙 Discovering GitHub repositories...")
            
            search_queries = [
                "ai tool stars:>50",
                "developer-tools stars:>100",
                "cli tool stars:>40",
                "automation tool stars:>60",
                "productivity stars:>80",
                "testing tool stars:>30"
            ]
            
            headers = {}
            if self.apis['github']['token']:
                headers['Authorization'] = f"token {self.apis['github']['token']}"
            
            for query in search_queries:
                if len(tools) >= limit:
                    break
                
                self._rate_limit('github')
                
                url = f"{self.apis['github']['base_url']}/search/repositories"
                params = {
                    'q': query,
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 50
                }
                
                data = self._safe_request(url, headers=headers, params=params)
                if not data:
                    continue
                
                for repo in data.get('items', []):
                    if len(tools) >= limit:
                        break
                    
                    tool = self._parse_github_repo(repo)
                    if tool:
                        tools.append(tool)
            
            logger.info(f"  ✅ GitHub: {len(tools)} repositories discovered")
            
        except Exception as e:
            logger.error(f"  ❌ GitHub discovery error: {str(e)}")
        
        return tools
    
    def _parse_github_repo(self, repo: Dict[str, Any]) -> Optional[APITool]:
        """Parse GitHub repository data"""
        try:
            name = repo.get('name', '')
            description = repo.get('description', '') or f"GitHub repository: {name}"
            html_url = repo.get('html_url', '')
            language = repo.get('language', 'Unknown')
            stars = repo.get('stargazers_count', 0)
            
            if not name or not html_url:
                return None
            
            # Determine category based on topics and description
            topics = repo.get('topics', [])
            category = "Developer Tool"
            if any(topic in ['ai', 'machine-learning', 'artificial-intelligence'] for topic in topics):
                category = "AI Tool"
            elif any(topic in ['cli', 'command-line'] for topic in topics):
                category = "CLI Tool"
            elif any(topic in ['automation', 'workflow'] for topic in topics):
                category = "Automation Tool"
            
            return APITool(
                name=name,
                description=description,
                website=html_url,
                category=category,
                source="github",
                pricing="Open Source" if not repo.get('private') else "Private",
                features=[f"⭐ {stars}", f"📝 {language}"] + topics[:3],
                confidence=min(0.8 + (stars / 10000), 1.0),  # Higher confidence for more stars
                metadata={
                    "stars": stars,
                    "language": language,
                    "topics": topics,
                    "updated_at": repo.get('updated_at'),
                    "forks": repo.get('forks_count', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"  ❌ Error parsing GitHub repo: {str(e)}")
            return None
    
    # ================================================================
    # NPM API DISCOVERY
    # ================================================================
    
    def _discover_npm(self, limit: int = 150) -> List[APITool]:
        """Discover tools from NPM registry"""
        tools = []
        
        try:
            logger.info(f"📦 Discovering NPM packages...")
            
            keywords = [
                'cli', 'tool', 'framework', 'library', 'utility',
                'build-tool', 'developer-tool', 'automation', 'testing'
            ]
            
            for keyword in keywords:
                if len(tools) >= limit:
                    break
                
                self._rate_limit('npm')
                
                url = f"{self.apis['npm']['base_url']}/-/v1/search"
                params = {
                    'text': keyword,
                    'size': 20,
                    'quality': 0.65,
                    'popularity': 0.98
                }
                
                data = self._safe_request(url, params=params)
                if not data:
                    continue
                
                for pkg_obj in data.get('objects', []):
                    if len(tools) >= limit:
                        break
                    
                    package_data = pkg_obj.get('package', {})
                    tool = self._parse_npm_package(package_data, keyword)
                    if tool:
                        tools.append(tool)
            
            logger.info(f"  ✅ NPM: {len(tools)} packages discovered")
            
        except Exception as e:
            logger.error(f"  ❌ NPM discovery error: {str(e)}")
        
        return tools
    
    def _parse_npm_package(self, package_data: Dict[str, Any], keyword: str) -> Optional[APITool]:
        """Parse NPM package data"""
        try:
            name = package_data.get('name', '')
            description = package_data.get('description', '') or f"NPM package: {name}"
            version = package_data.get('version', '')
            
            if not name:
                return None
            
            # Filter out packages that don't seem like tools
            if any(word in name.lower() for word in ['test', 'example', 'demo', 'sample']):
                return None
            
            return APITool(
                name=name,
                description=description,
                website=f"https://www.npmjs.com/package/{name}",
                category="NPM Package",
                source="npm",
                pricing="Open Source",
                features=[f"📦 NPM", f"🏷️ {keyword}", f"📋 v{version}"],
                confidence=0.7,
                metadata={
                    "version": version,
                    "keyword": keyword,
                    "publisher": package_data.get('publisher', {}),
                    "date": package_data.get('date')
                }
            )
            
        except Exception as e:
            logger.error(f"  ❌ Error parsing NPM package: {str(e)}")
            return None
    
    # ================================================================
    # REDDIT API DISCOVERY
    # ================================================================
    
    def _discover_reddit(self, limit: int = 100) -> List[APITool]:
        """Discover tools from Reddit"""
        tools = []
        
        try:
            logger.info(f"🤖 Discovering from Reddit...")
            
            subreddits = [
                'artificial', 'MachineLearning', 'programming', 'webdev',
                'SideProject', 'startups', 'Entrepreneur', 'productivity'
            ]
            
            for subreddit in subreddits:
                if len(tools) >= limit:
                    break
                
                self._rate_limit('reddit')
                
                url = f"{self.apis['reddit']['base_url']}/r/{subreddit}/hot.json"
                params = {'limit': 25}
                
                data = self._safe_request(url, params=params)
                if not data:
                    continue
                
                for post in data.get("data", {}).get("children", []):
                    if len(tools) >= limit:
                        break
                    
                    post_data = post.get("data", {})
                    tool = self._parse_reddit_post(post_data, subreddit)
                    if tool:
                        tools.append(tool)
            
            logger.info(f"  ✅ Reddit: {len(tools)} tools discovered")
            
        except Exception as e:
            logger.error(f"  ❌ Reddit discovery error: {str(e)}")
        
        return tools
    
    def _parse_reddit_post(self, post_data: Dict[str, Any], subreddit: str) -> Optional[APITool]:
        """Parse Reddit post data"""
        try:
            title = post_data.get("title", "").strip()
            url = post_data.get("url", "").strip()
            selftext = post_data.get("selftext", "").strip()
            score = post_data.get("score", 0)
            
            # Skip if no title or URL, or if it's a Reddit URL
            if not title or not url or len(title) < 10 or 'reddit.com' in url:
                return None
            
            # Filter for tool-related posts
            title_lower = title.lower()
            tool_keywords = [
                'tool', 'app', 'platform', 'service', 'api', 'library',
                'framework', 'ai', 'automation', 'generator', 'built',
                'created', 'launched', 'released', 'new', 'show hn'
            ]
            
            if not any(keyword in title_lower for keyword in tool_keywords):
                return None
            
            # Build description
            description = title
            if selftext and len(selftext) > 20:
                description = f"{title}. {selftext[:200]}..."
            
            return APITool(
                name=title[:100],
                description=description[:500],
                website=url,
                category=f"Reddit - r/{subreddit}",
                source="reddit",
                pricing="Unknown",
                features=[f"🤖 Reddit", f"⬆️ {score}", f"📝 r/{subreddit}"],
                confidence=min(0.5 + (score / 1000), 0.8),  # Higher confidence for higher scores
                metadata={
                    "subreddit": subreddit,
                    "score": score,
                    "created_utc": post_data.get("created_utc"),
                    "num_comments": post_data.get("num_comments", 0)
                }
            )
            
        except Exception as e:
            logger.error(f"  ❌ Error parsing Reddit post: {str(e)}")
            return None
    
    # ================================================================
    # HACKER NEWS API DISCOVERY
    # ================================================================
    
    def _discover_hackernews(self, limit: int = 100) -> List[APITool]:
        """Discover tools from Hacker News"""
        tools = []
        
        try:
            logger.info(f"📰 Discovering from Hacker News...")
            
            # Get top stories
            url = f"{self.apis['hackernews']['base_url']}/topstories.json"
            story_ids = self._safe_request(url)
            
            if not story_ids:
                return tools
            
            # Process top stories
            for story_id in story_ids[:100]:  # Check top 100 stories
                if len(tools) >= limit:
                    break
                
                self._rate_limit('hackernews')
                
                story_url = f"{self.apis['hackernews']['base_url']}/item/{story_id}.json"
                story = self._safe_request(story_url)
                
                if story:
                    tool = self._parse_hackernews_story(story)
                    if tool:
                        tools.append(tool)
            
            logger.info(f"  ✅ Hacker News: {len(tools)} tools discovered")
            
        except Exception as e:
            logger.error(f"  ❌ Hacker News discovery error: {str(e)}")
        
        return tools
    
    def _parse_hackernews_story(self, story: Dict[str, Any]) -> Optional[APITool]:
        """Parse Hacker News story data"""
        try:
            title = story.get('title', '').strip()
            url = story.get('url', '').strip()
            score = story.get('score', 0)
            
            # Skip if no title or URL, or if it's a HN URL
            if not title or not url or 'news.ycombinator.com' in url:
                return None
            
            # Filter for tool-related stories
            title_lower = title.lower()
            tool_keywords = [
                'tool', 'app', 'platform', 'service', 'api', 'framework',
                'show hn', 'launch', 'built', 'created', 'new', 'open source'
            ]
            
            if not any(keyword in title_lower for keyword in tool_keywords):
                return None
            
            return APITool(
                name=title[:100],
                description=f"{title}. Featured on Hacker News",
                website=url,
                category="Hacker News",
                source="hackernews",
                pricing="Unknown",
                features=[f"📰 HN", f"⬆️ {score}", "🔥 Trending"],
                confidence=min(0.6 + (score / 500), 0.9),  # Higher confidence for higher scores
                metadata={
                    "score": score,
                    "time": story.get('time'),
                    "descendants": story.get('descendants', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"  ❌ Error parsing Hacker News story: {str(e)}")
            return None
    
    # ================================================================
    # STACK OVERFLOW API DISCOVERY
    # ================================================================
    
    def _discover_stackoverflow(self, limit: int = 100) -> List[APITool]:
        """Discover tools from Stack Overflow"""
        tools = []
        
        try:
            logger.info(f"❓ Discovering from Stack Overflow...")
            
            tags = ['tools', 'javascript', 'python', 'productivity', 'automation']
            
            for tag in tags:
                if len(tools) >= limit:
                    break
                
                self._rate_limit('stackoverflow')
                
                url = f"{self.apis['stackoverflow']['base_url']}/questions"
                params = {
                    'order': 'desc',
                    'sort': 'votes',
                    'tagged': tag,
                    'site': 'stackoverflow',
                    'pagesize': 20,
                    'filter': 'withbody'
                }
                
                data = self._safe_request(url, params=params)
                if not data:
                    continue
                
                tag_tools = self._parse_stackoverflow_questions(data, tag)
                tools.extend(tag_tools[:10])  # Limit per tag
            
            logger.info(f"  ✅ Stack Overflow: {len(tools)} tools discovered")
            
        except Exception as e:
            logger.error(f"  ❌ Stack Overflow discovery error: {str(e)}")
        
        return tools
    
    def _parse_stackoverflow_questions(self, data: Dict[str, Any], tag: str) -> List[APITool]:
        """Parse Stack Overflow questions data"""
        tools = []
        
        try:
            for question in data.get('items', []):
                title = question.get('title', '').strip()
                link = question.get('link', '').strip()
                score = question.get('score', 0)
                view_count = question.get('view_count', 0)
                
                if not title or not link:
                    continue
                
                # Filter for tool-related questions
                title_lower = title.lower()
                tool_keywords = [
                    'tool', 'library', 'framework', 'package', 'best',
                    'recommend', 'which', 'what', 'good', 'better'
                ]
                
                if any(keyword in title_lower for keyword in tool_keywords):
                    tools.append(APITool(
                        name=title[:100],
                        description=f"Stack Overflow discussion: {title}",
                        website=link,
                        category=f"Stack Overflow - {tag}",
                        source="stackoverflow",
                        pricing="Unknown",
                        features=[f"❓ SO", f"⬆️ {score}", f"👀 {view_count}"],
                        confidence=min(0.4 + (score / 100), 0.7),
                        metadata={
                            "tag": tag,
                            "score": score,
                            "view_count": view_count,
                            "answer_count": question.get('answer_count', 0)
                        }
                    ))
        
        except Exception as e:
            logger.error(f"  ❌ Error parsing Stack Overflow questions: {str(e)}")
        
        return tools
    
    # ================================================================
    # PYPI API DISCOVERY
    # ================================================================
    
    def _discover_pypi(self, limit: int = 100) -> List[APITool]:
        """Discover tools from PyPI (Python Package Index)"""
        tools = []
        
        try:
            logger.info(f"🐍 Discovering from PyPI...")
            
            # Popular Python packages that are likely to be tools
            popular_packages = [
                'requests', 'flask', 'django', 'fastapi', 'pandas', 'numpy',
                'click', 'pytest', 'black', 'mypy', 'flake8', 'jupyter',
                'scrapy', 'tensorflow', 'pytorch', 'opencv-python', 'pillow'
            ]
            
            for package in popular_packages[:limit]:
                self._rate_limit('pypi')
                
                url = f"{self.apis['pypi']['base_url']}/pypi/{package}/json"
                data = self._safe_request(url)
                
                if data:
                    tool = self._parse_pypi_package(data, package)
                    if tool:
                        tools.append(tool)
            
            logger.info(f"  ✅ PyPI: {len(tools)} packages discovered")
            
        except Exception as e:
            logger.error(f"  ❌ PyPI discovery error: {str(e)}")
        
        return tools
    
    def _parse_pypi_package(self, data: Dict[str, Any], package_name: str) -> Optional[APITool]:
        """Parse PyPI package data"""
        try:
            info = data.get('info', {})
            name = info.get('name', package_name)
            summary = info.get('summary', '')
            version = info.get('version', '')
            author = info.get('author', '')
            
            if not summary:
                summary = f"Python package: {name}"
            
            return APITool(
                name=name,
                description=summary,
                website=f"https://pypi.org/project/{name}/",
                category="Python Package",
                source="pypi",
                pricing="Open Source",
                features=[f"🐍 Python", f"📦 v{version}", f"👤 {author}"],
                confidence=0.7,
                metadata={
                    "version": version,
                    "author": author,
                    "home_page": info.get('home_page'),
                    "keywords": info.get('keywords')
                }
            )
            
        except Exception as e:
            logger.error(f"  ❌ Error parsing PyPI package: {str(e)}")
            return None
    
    # ================================================================
    # MAIN DISCOVERY METHODS (like ai_directory_service.py)
    # ================================================================
    
    def run_sync_discover_all_real_apis(self, target_tools: int = 1000) -> Dict[str, Any]:
        """Discover from all available real APIs"""
        
        logger.info(f"🚀 Starting All Real APIs Discovery - Target: {target_tools} tools")
        start_time = time.time()
        
        all_tools = []
        api_results = {}
        
        try:
            # Define APIs to use with their limits
            apis_to_use = [
                ("GitHub", self._discover_github, 300),
                ("NPM", self._discover_npm, 200),
                ("Reddit", self._discover_reddit, 150),
                ("Hacker News", self._discover_hackernews, 150),
                ("Stack Overflow", self._discover_stackoverflow, 100),
                ("PyPI", self._discover_pypi, 100)
            ]
            
            for api_name, discovery_method, api_limit in apis_to_use:
                if len(all_tools) >= target_tools:
                    break
                
                try:
                    api_start = time.time()
                    tools = discovery_method(api_limit)
                    api_time = time.time() - api_start
                    
                    all_tools.extend(tools)
                    
                    api_results[api_name] = {
                        "success": True,
                        "tools_discovered": len(tools),
                        "processing_time": api_time
                    }
                    
                    # Small delay between APIs
                    time.sleep(1)
                    
                except Exception as e:
                    api_results[api_name] = {
                        "success": False,
                        "error": str(e),
                        "tools_discovered": 0,
                        "processing_time": 0
                    }
                    logger.error(f"❌ {api_name} failed: {str(e)}")
            
            # Remove duplicates
            unique_tools = self._deduplicate_tools(all_tools)
            
            # Save to database
            logger.info(f"💾 Saving {len(unique_tools)} unique tools to database...")
            db_result = self._save_tools_to_database(unique_tools)
            
            processing_time = time.time() - start_time
            
            # Update stats
            self.stats["total_discovered"] += len(all_tools)
            self.stats["total_saved"] += db_result["saved"]
            self.stats["total_duplicates"] += db_result["duplicates"]
            self.stats["total_errors"] += db_result["errors"]
            
            logger.info(f"✅ All Real APIs Discovery Complete!")
            logger.info(f"📊 Results: {len(all_tools)} discovered, {len(unique_tools)} unique, {db_result['saved']} saved")
            
            return {
                "success": True,
                "total_discovered": len(all_tools),
                "total_unique": len(unique_tools),
                "total_saved": db_result["saved"],
                "total_duplicates": db_result["duplicates"],
                "total_errors": db_result["errors"],
                "processing_time": processing_time,
                "api_results": api_results
            }
            
        except Exception as e:
            logger.error(f"❌ All APIs discovery failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0,
                "api_results": api_results
            }

    def run_sync_discover_no_auth_apis(self, target_tools: int = 800) -> Dict[str, Any]:
        """Discover from APIs that don't require authentication"""
        
        logger.info(f"⚡ Starting No-Auth APIs Discovery - Target: {target_tools} tools")
        start_time = time.time()
        
        all_tools = []
        api_results = {}
        
        try:
            # No-auth APIs only
            no_auth_apis = [
                ("GitHub", self._discover_github, 250),  # Works without token (rate limited)
                ("NPM", self._discover_npm, 200),
                ("Reddit", self._discover_reddit, 150),
                ("Hacker News", self._discover_hackernews, 100),
                ("Stack Overflow", self._discover_stackoverflow, 100),
                ("PyPI", self._discover_pypi, 100)
            ]
            
            for api_name, discovery_method, api_limit in no_auth_apis:
                if len(all_tools) >= target_tools:
                    break
                
                try:
                    tools = discovery_method(api_limit)
                    all_tools.extend(tools)
                    
                    api_results[api_name] = {
                        "success": True,
                        "tools_discovered": len(tools)
                    }
                    
                    time.sleep(1)
                    
                except Exception as e:
                    api_results[api_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Process and save
            unique_tools = self._deduplicate_tools(all_tools)
            db_result = self._save_tools_to_database(unique_tools)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_discovered": len(all_tools),
                "total_saved": db_result["saved"],
                "processing_time": processing_time,
                "api_results": api_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0
            }

    def run_sync_discover_github(self, target_tools: int = 200) -> Dict[str, Any]:
        """GitHub discovery specifically"""
        start_time = time.time()
        
        try:
            tools = self._discover_github(target_tools)
            db_result = self._save_tools_to_database(tools)
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_discovered": len(tools),
                "total_saved": db_result["saved"],
                "processing_time": processing_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0
            }

    def run_sync_discover_npm(self, target_tools: int = 150) -> Dict[str, Any]:
        """NPM discovery specifically"""
        start_time = time.time()
        
        try:
            tools = self._discover_npm(target_tools)
            db_result = self._save_tools_to_database(tools)
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_discovered": len(tools),
                "total_saved": db_result["saved"],
                "processing_time": processing_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0
            }

    def run_sync_discover_reddit(self, target_tools: int = 100) -> Dict[str, Any]:
        """Reddit discovery specifically"""
        start_time = time.time()
        
        try:
            tools = self._discover_reddit(target_tools)
            db_result = self._save_tools_to_database(tools)
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_discovered": len(tools),
                "total_saved": db_result["saved"],
                "processing_time": processing_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0
            }

    def run_sync_discover_hackernews(self, target_tools: int = 100) -> Dict[str, Any]:
        """Hacker News discovery specifically"""
        start_time = time.time()
        
        try:
            tools = self._discover_hackernews(target_tools)
            db_result = self._save_tools_to_database(tools)
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_discovered": len(tools),
                "total_saved": db_result["saved"],
                "processing_time": processing_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0
            }

    def run_sync_discover_stackoverflow(self, target_tools: int = 100) -> Dict[str, Any]:
        """Stack Overflow discovery specifically"""
        start_time = time.time()
        
        try:
            tools = self._discover_stackoverflow(target_tools)
            db_result = self._save_tools_to_database(tools)
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_discovered": len(tools),
                "total_saved": db_result["saved"],
                "processing_time": processing_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0
            }

    def run_sync_discover_pypi(self, target_tools: int = 100) -> Dict[str, Any]:
        """PyPI discovery specifically"""
        start_time = time.time()
        
        try:
            tools = self._discover_pypi(target_tools)
            db_result = self._save_tools_to_database(tools)
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_discovered": len(tools),
                "total_saved": db_result["saved"],
                "processing_time": processing_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0
            }

    # ================================================================
    # INCREMENTAL DISCOVERY METHODS
    # ================================================================
    
    def run_sync_discover_all_real_apis_incremental(self, target_tools: int = 1000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental discovery for all real APIs"""
        
        incremental_params = incremental_params or {}
        force_full_scan = incremental_params.get("force_full_scan", False)
        last_check_times = incremental_params.get("last_check_times", {})
        
        logger.info(f"⚡ Starting Incremental All APIs Discovery")
        logger.info(f"🎯 Target: {target_tools} tools")
        logger.info(f"🔄 Mode: {'FULL SCAN' if force_full_scan else 'INCREMENTAL'}")
        
        start_time = time.time()
        all_tools = []
        api_results = {}
        total_skipped = 0
        
        # APIs with incremental support
        incremental_apis = [
            ("GitHub", self._discover_github, 300, "github"),
            ("NPM", self._discover_npm, 200, "npm"),
            ("Reddit", self._discover_reddit, 150, "reddit"),
            ("Hacker News", self._discover_hackernews, 150, "hackernews"),
            ("Stack Overflow", self._discover_stackoverflow, 100, "stackoverflow"),
            ("PyPI", self._discover_pypi, 100, "pypi")
        ]
        
        try:
            for api_name, discovery_method, api_limit, api_key in incremental_apis:
                if len(all_tools) >= target_tools:
                    break
                
                # Check if we should skip this API
                last_check = last_check_times.get(api_key)
                should_skip = self._should_skip_api_incremental(api_key, last_check, force_full_scan)
                
                if should_skip:
                    logger.info(f"⏭️ {api_name}: Skipped (recently checked)")
                    api_results[api_name] = {
                        "tools_discovered": 0,
                        "tools_skipped": api_limit,
                        "success": True,
                        "incremental_skip": True,
                        "last_check": last_check
                    }
                    total_skipped += api_limit
                    continue
                
                try:
                    api_start = time.time()
                    tools = discovery_method(api_limit)
                    api_time = time.time() - api_start
                    
                    all_tools.extend(tools)
                    
                    api_results[api_name] = {
                        "success": True,
                        "tools_discovered": len(tools),
                        "tools_skipped": 0,
                        "processing_time": api_time,
                        "incremental_skip": False
                    }
                    
                    logger.info(f"✅ {api_name}: {len(tools)} tools ({api_time:.1f}s)")
                    time.sleep(1)
                    
                except Exception as e:
                    api_results[api_name] = {
                        "success": False,
                        "error": str(e),
                        "tools_discovered": 0,
                        "incremental_skip": False
                    }
                    logger.error(f"❌ {api_name} failed: {str(e)}")
            
            # Process results
            unique_tools = self._deduplicate_tools(all_tools)
            db_result = self._save_tools_to_database(unique_tools) if unique_tools else {"saved": 0, "duplicates": 0, "errors": 0}
            
            processing_time = time.time() - start_time
            
            logger.info(f"🎊 Incremental All APIs Discovery Complete!")
            logger.info(f"📈 Results: {len(all_tools)} discovered, {db_result['saved']} saved, {total_skipped} skipped")
            
            return {
                "success": True,
                "total_discovered": len(all_tools),
                "total_saved": db_result["saved"],
                "total_skipped": total_skipped,
                "processing_time": processing_time,
                "api_results": api_results,
                "incremental_mode": not force_full_scan
            }
            
        except Exception as e:
            logger.error(f"❌ Incremental discovery failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0,
                "total_skipped": total_skipped,
                "api_results": api_results
            }

    def run_sync_discover_no_auth_apis_incremental(self, target_tools: int = 800, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental discovery for no-auth APIs"""
        
        # For simplicity, delegate to the main incremental method with a subset
        incremental_params = incremental_params or {}
        return self.run_sync_discover_all_real_apis_incremental(target_tools, incremental_params)

    def run_sync_discover_github_incremental(self, target_tools: int = 200, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental GitHub discovery"""
        return self._run_single_api_incremental("github", self._discover_github, target_tools, incremental_params)

    def run_sync_discover_npm_incremental(self, target_tools: int = 150, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental NPM discovery"""
        return self._run_single_api_incremental("npm", self._discover_npm, target_tools, incremental_params)

    def run_sync_discover_reddit_incremental(self, target_tools: int = 100, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental Reddit discovery"""
        return self._run_single_api_incremental("reddit", self._discover_reddit, target_tools, incremental_params)

    def run_sync_discover_hackernews_incremental(self, target_tools: int = 100, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental Hacker News discovery"""
        return self._run_single_api_incremental("hackernews", self._discover_hackernews, target_tools, incremental_params)

    def run_sync_discover_stackoverflow_incremental(self, target_tools: int = 100, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental Stack Overflow discovery"""
        return self._run_single_api_incremental("stackoverflow", self._discover_stackoverflow, target_tools, incremental_params)

    def run_sync_discover_pypi_incremental(self, target_tools: int = 100, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Incremental PyPI discovery"""
        return self._run_single_api_incremental("pypi", self._discover_pypi, target_tools, incremental_params)

    # ================================================================
    # INCREMENTAL HELPER METHODS
    # ================================================================
    
    def _run_single_api_incremental(self, api_name: str, discovery_method, target_tools: int, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run single API with incremental support"""
        
        incremental_params = incremental_params or {}
        force_full_scan = incremental_params.get("force_full_scan", False)
        last_check_times = incremental_params.get("last_check_times", {})
        
        # Check if we should skip
        last_check = last_check_times.get(api_name)
        should_skip = self._should_skip_api_incremental(api_name, last_check, force_full_scan)
        
        if should_skip:
            return {
                "success": True,
                "total_saved": 0,
                "total_skipped": target_tools,
                "incremental_skip": True,
                "last_check": last_check,
                "processing_time": 0
            }
        
        # Run discovery
        start_time = time.time()
        
        try:
            tools = discovery_method(target_tools)
            db_result = self._save_tools_to_database(tools)
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "total_discovered": len(tools),
                "total_saved": db_result["saved"],
                "total_skipped": 0,
                "incremental_skip": False,
                "processing_time": processing_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_saved": 0,
                "total_skipped": 0,
                "incremental_skip": False
            }

    def _should_skip_api_incremental(self, api_name: str, last_check: str, force_full_scan: bool) -> bool:
        """Determine if an API should be skipped in incremental mode"""
        
        if force_full_scan or not last_check:
            return False
        
        try:
            last_check_dt = datetime.fromisoformat(last_check)
            hours_since = (datetime.utcnow() - last_check_dt).total_seconds() / 3600
            
            # API-specific skip thresholds (hours)
            skip_thresholds = {
                "github": 2,         # Active development
                "npm": 4,           # Frequent updates
                "reddit": 1,        # Very active
                "hackernews": 2,    # Active
                "stackoverflow": 6, # Less frequent
                "pypi": 12,         # Even less frequent
                "producthunt": 24,  # Daily
                "crunchbase": 24    # Daily
            }
            
            threshold = skip_thresholds.get(api_name, 6)  # Default 6 hours
            return hours_since < threshold
            
        except Exception:
            return False  # If error parsing date, don't skip

    # ================================================================
    # UTILITY METHODS
    # ================================================================
    
    def _deduplicate_tools(self, tools: List[APITool]) -> List[APITool]:
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


# ================================================================
# GLOBAL INSTANCE (like ai_directory_service.py)
# ================================================================

# Create global instance for easy importing
unified_apis_service = UnifiedRealAPIsService()


# ================================================================
# CLI INTERFACE (like ai_directory_service.py)
# ================================================================

def main():
    """CLI interface for testing"""
    import sys
    
    service = UnifiedRealAPIsService()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "discover-all":
            target = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
            result = service.run_sync_discover_all_real_apis(target)
            
            if result['success']:
                print(f"✅ Discovery complete: {result['total_saved']} tools saved")
                print(f"📊 API Results:")
                for api_name, api_result in result['api_results'].items():
                    if api_result.get('success'):
                        print(f"  • {api_name}: {api_result['tools_discovered']} tools")
                    else:
                        print(f"  • {api_name}: Failed - {api_result.get('error')}")
            else:
                print(f"❌ Discovery failed: {result.get('error')}")
                
        elif command == "discover-no-auth":
            target = int(sys.argv[2]) if len(sys.argv) > 2 else 800
            result = service.run_sync_discover_no_auth_apis(target)
            
            if result['success']:
                print(f"✅ No-auth discovery complete: {result['total_saved']} tools saved")
            else:
                print(f"❌ No-auth discovery failed: {result.get('error')}")
                
        elif command == "discover-single":
            if len(sys.argv) < 3:
                print("Usage: python real_apis_service.py discover-single <api>")
                print("Available APIs: github, npm, reddit, hackernews, stackoverflow, pypi")
                return
                
            api_name = sys.argv[2]
            target = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            
            method_name = f"run_sync_discover_{api_name}"
            if hasattr(service, method_name):
                method = getattr(service, method_name)
                result = method(target)
                
                if result['success']:
                    print(f"✅ {api_name.title()} discovery complete: {result['total_saved']} tools saved")
                else:
                    print(f"❌ {api_name.title()} discovery failed: {result.get('error')}")
            else:
                print(f"❌ Unknown API: {api_name}")
                
        elif command == "test-incremental":
            # Test incremental discovery
            test_params = {
                "force_full_scan": False,
                "last_check_times": {
                    "github": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                    "npm": (datetime.utcnow() - timedelta(hours=5)).isoformat()
                }
            }
            
            result = service.run_sync_discover_all_real_apis_incremental(
                target_tools=200,
                incremental_params=test_params
            )
            
            if result['success']:
                print(f"✅ Incremental test complete:")
                print(f"   📈 Discovered: {result['total_discovered']}")
                print(f"   💾 Saved: {result['total_saved']}")
                print(f"   ⏭️ Skipped: {result['total_skipped']}")
            else:
                print(f"❌ Incremental test failed: {result.get('error')}")
                
        else:
            print("❌ Unknown command")
    else:
        print("🚀 Real APIs Discovery Service")
        print("\nUsage:")
        print("  python real_apis_service.py discover-all [target]")
        print("  python real_apis_service.py discover-no-auth [target]")
        print("  python real_apis_service.py discover-single <api> [target]")
        print("  python real_apis_service.py test-incremental")
        print("\nExamples:")
        print("  python real_apis_service.py discover-all 500")
        print("  python real_apis_service.py discover-single github 100")
        print("  python real_apis_service.py test-incremental")
        
        print("\n📡 Available APIs:")
        print("  • GitHub: Repositories and tools")
        print("  • NPM: JavaScript packages")
        print("  • Reddit: Tool discussions and launches") 
        print("  • Hacker News: Featured tools and launches")
        print("  • Stack Overflow: Tool recommendations")
        print("  • PyPI: Python packages")
        
        print("\n⚡ Features:")
        print("  • Incremental discovery (only updated tools)")
        print("  • Smart deduplication")
        print("  • Rate limiting and error handling")
        print("  • Database integration")
        print("  • Confidence scoring")


if __name__ == "__main__":
    main()