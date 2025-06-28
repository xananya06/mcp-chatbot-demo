import asyncio
import aiohttp
import time
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
import hashlib

from app.db.database import SessionLocal
from app.services.chat_service import save_discovered_tools_with_deduplication

logger = logging.getLogger(__name__)

class RealExternalAPIService:
    """Real External API Integration for massive tool discovery"""
    
    def __init__(self):
        self.session = None
        self.rate_limits = {
            'product_hunt': 1.0,  # 1 second between requests
            'github': 0.1,       # GitHub has higher limits
            'alternativeto': 2.0, # Be respectful
            'scraping': 3.0      # Slower for scraping
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'AI Tool Discovery Bot 1.0 (Educational/Research)'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def massive_discovery_pipeline(self, target_tools: int = 10000) -> Dict[str, Any]:
        """ENHANCED massive pipeline with ALL API sources"""
        
        results = {
            "pipeline_id": f"massive_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_discovered": 0,
            "total_saved": 0,
            "sources_processed": []
        }
        
        print(f"🚀 ENHANCED MASSIVE DISCOVERY PIPELINE STARTED")
        print(f"🎯 Target: {target_tools} tools from ALL API sources")
        
        # ENHANCED discovery sources with new APIs
        discovery_tasks = [
            ("GitHub AI Repositories", self._discover_github_ai_tools, 4000),
            ("Chrome Web Store Extensions", self._discover_chrome_extensions, 2000),
            ("VS Code Marketplace", self._discover_vscode_extensions, 1500),
            ("NPM Packages", self._discover_npm_packages, 2000),
            ("PyPI Packages", self._discover_pypi_packages, 1500),
            ("Product Hunt AI Tools", self._discover_product_hunt_tools, 1000),
            ("AI Tool Directories", self._scrape_ai_directories, 1000),
            ("Awesome Lists Scraping", self._scrape_awesome_lists, 2000)
        ]
        
        db = SessionLocal()
        
        try:
            for source_name, discovery_func, max_tools in discovery_tasks:
                if results["total_saved"] >= target_tools:
                    print(f"🎉 TARGET REACHED! {results['total_saved']} tools discovered")
                    break
                    
                print(f"\n📡 Processing: {source_name} (max: {max_tools})")
                source_start = time.time()
                
                try:
                    source_tools = await discovery_func(max_tools)
                    source_time = time.time() - source_start
                    
                    if source_tools:
                        # Save to database
                        save_result = save_discovered_tools_with_deduplication(db, source_tools)
                        
                        saved = save_result.get("saved", 0)
                        updated = save_result.get("updated", 0)
                        
                        results["total_discovered"] += len(source_tools)
                        results["total_saved"] += saved
                        
                        results["sources_processed"].append({
                            "source": source_name,
                            "tools_discovered": len(source_tools),
                            "tools_saved": saved,
                            "tools_updated": updated,
                            "processing_time": round(source_time, 2)
                        })
                        
                        print(f"  ✅ {source_name}: {len(source_tools)} discovered, {saved} saved ({source_time:.1f}s)")
                    else:
                        print(f"  ❌ {source_name}: No tools discovered")
                        
                except Exception as e:
                    error_msg = f"{source_name}: {str(e)}"
                    print(f"  💥 ERROR: {error_msg}")
                
                # Progress update
                print(f"  📊 Total progress: {results['total_saved']}/{target_tools} tools ({(results['total_saved']/target_tools)*100:.1f}%)")
                
        finally:
            db.close()
            
        results["end_time"] = datetime.utcnow().isoformat()
        
        print(f"\n🎊 ENHANCED MASSIVE DISCOVERY COMPLETE!")
        print(f"📈 FINAL RESULTS:")
        print(f"   • Total tools discovered: {results['total_discovered']}")
        print(f"   • New tools saved: {results['total_saved']}")
        print(f"   • Sources processed: {len(results['sources_processed'])}")
        
        return results

    async def _discover_github_ai_tools(self, max_tools: int = 3000) -> List[Dict[str, Any]]:
        """Enhanced GitHub discovery with token support and expanded queries"""
        
        tools = []
        
        # MASSIVELY EXPANDED search queries for 10K+ tools
        search_queries = [
            # AI-focused queries (existing)
            "ai tool stars:>50",
            "artificial intelligence tool stars:>100", 
            "machine learning tool stars:>50",
            "chatbot tool stars:>20",
            "ai assistant stars:>30",
            "text generation tool stars:>20",
            "image generation ai stars:>50",
            "voice ai tool stars:>20",
            "ai writing tool stars:>10",
            "ai code tool stars:>50",
            "ai data analysis stars:>20",
            "ai automation tool stars:>30",
            
            # NEW: Developer tools (HIGH VOLUME)
            "developer-tools stars:>100",
            "productivity stars:>80",
            "automation tool stars:>60",
            "cli tool stars:>40",
            "dashboard stars:>50",
            "monitoring tool stars:>40",
            "testing tool stars:>50",
            "deployment tool stars:>30",
            "security tool stars:>40",
            "performance tool stars:>30",
            "analytics tool stars:>35",
            "logging tool stars:>25",
            "debugging tool stars:>20",
            "optimization tool stars:>25",
            
            # NEW: Web development tools
            "web development tool stars:>40",
            "frontend tool stars:>30",
            "backend tool stars:>35",
            "fullstack tool stars:>25",
            "api tool stars:>30",
            "database tool stars:>40",
            "orm tool stars:>20",
            "framework stars:>100",
            
            # NEW: Mobile development
            "mobile app tool stars:>30",
            "android tool stars:>25",
            "ios tool stars:>25",
            "react native tool stars:>20",
            "flutter tool stars:>30",
            
            # NEW: Desktop development  
            "desktop app tool stars:>25",
            "electron tool stars:>20",
            "cross platform tool stars:>20",
            
            # NEW: DevOps and Infrastructure
            "devops tool stars:>40",
            "docker tool stars:>30",
            "kubernetes tool stars:>35",
            "ci cd tool stars:>25",
            "infrastructure tool stars:>30",
            "cloud tool stars:>25",
            
            # NEW: Data and Analytics
            "data science tool stars:>40",
            "data visualization tool stars:>30",
            "business intelligence tool stars:>20",
            "etl tool stars:>15",
            "big data tool stars:>25",
            
            # NEW: Design and Content
            "design tool stars:>30",
            "ui ux tool stars:>25",
            "content management stars:>25",
            "cms tool stars:>20",
            
            # NEW: Gaming and Graphics
            "game development tool stars:>25",
            "graphics tool stars:>20",
            "3d tool stars:>20",
            "rendering tool stars:>15"
        ]
        
        # Setup headers with GitHub token
        import os
        headers = {
            'User-Agent': 'AI Tool Discovery Bot 1.0 (Educational/Research)'
        }
        
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            headers['Authorization'] = f'token {github_token}'
            print(f"  🔑 Using GitHub token - 5000 requests/hour available!")
        else:
            print(f"  ⚠️  No GitHub token - limited to 60 requests/hour")
        
        print(f"  🔍 Searching {len(search_queries)} different query categories")
        
        for i, query in enumerate(search_queries):
            if len(tools) >= max_tools:
                break
                
            try:
                # Faster rate limit with token
                if github_token:
                    await asyncio.sleep(0.05)  # 20 requests/second with token
                else:
                    await asyncio.sleep(self.rate_limits['github'])  # Slower without token
                
                # GitHub API search with authentication
                url = f"https://api.github.com/search/repositories"
                params = {
                    'q': query,
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 100
                }
                
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        query_tools = 0
                        
                        for repo in data.get('items', []):
                            if len(tools) >= max_tools:
                                break
                                
                            tool = self._parse_github_repo_to_tool(repo)
                            if tool:
                                tools.append(tool)
                                query_tools += 1
                        
                        # Progress update every 10 queries
                        if (i + 1) % 10 == 0:
                            print(f"    • Processed {i+1}/{len(search_queries)} queries, found {len(tools)} total tools")
                                
                    elif response.status == 403:
                        print(f"  ⚠️  GitHub rate limit hit, waiting...")
                        await asyncio.sleep(60)
                    elif response.status == 401:
                        print(f"  ❌ GitHub authentication failed - check token")
                        break
                    else:
                        print(f"  ⚠️  GitHub API error: {response.status}")
                        
            except Exception as e:
                print(f"  ❌ GitHub query '{query}' failed: {e}")
                continue
        
        print(f"  📊 GitHub: Discovered {len(tools)} repositories using {len(search_queries)} search queries")
        return tools[:max_tools]

    async def _discover_product_hunt_tools(self, max_tools: int = 1500) -> List[Dict[str, Any]]:
        """Discover tools from Product Hunt (using public data)"""
        
        tools = []
        
        # Product Hunt categories for AI tools
        categories = [
            'artificial-intelligence',
            'developer-tools', 
            'productivity',
            'design-tools',
            'marketing',
            'analytics',
            'automation'
        ]
        
        for category in categories:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.rate_limits['product_hunt'])
                
                # Use Product Hunt's public RSS/JSON feeds or web scraping
                url = f"https://www.producthunt.com/topics/{category}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        category_tools = self._parse_product_hunt_page(html, category)
                        tools.extend(category_tools)
                        
            except Exception as e:
                print(f"  ❌ Product Hunt category '{category}' failed: {e}")
                continue
        
        print(f"  📊 Product Hunt: Discovered {len(tools)} tools")
        return tools[:max_tools]

    async def _discover_alternativeto_tools(self, max_tools: int = 2000) -> List[Dict[str, Any]]:
        """Discover tools from AlternativeTo"""
        
        tools = []
        
        # AlternativeTo categories
        categories = [
            'artificial-intelligence',
            'text-editor',
            'image-editor', 
            'video-editor',
            'audio-editor',
            'development',
            'productivity',
            'automation',
            'chatbot',
            'search-engine'
        ]
        
        for category in categories:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.rate_limits['alternativeto'])
                
                # AlternativeTo browse pages
                for page in range(1, 6):  # First 5 pages per category
                    url = f"https://alternativeto.net/browse/{category}/?page={page}"
                    
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            page_tools = self._parse_alternativeto_page(html, category)
                            tools.extend(page_tools)
                        
                    await asyncio.sleep(1)  # Be respectful
                        
            except Exception as e:
                print(f"  ❌ AlternativeTo category '{category}' failed: {e}")
                continue
        
        print(f"  📊 AlternativeTo: Discovered {len(tools)} tools")
        return tools[:max_tools]

    async def _scrape_ai_directories(self, max_tools: int = 2000) -> List[Dict[str, Any]]:
        """Scrape AI tool directories"""
        
        tools = []
        
        # Popular AI tool directories
        directories = [
            "https://www.futurepedia.io/",
            "https://www.toolify.ai/",
            "https://aitools.fyi/",
            "https://www.aitoolnet.com/",
            "https://aitoptools.com/"
        ]
        
        for directory_url in directories:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.rate_limits['scraping'])
                
                async with self.session.get(directory_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        directory_tools = self._parse_ai_directory_page(html, directory_url)
                        tools.extend(directory_tools)
                        
            except Exception as e:
                print(f"  ❌ AI directory '{directory_url}' failed: {e}")
                continue
        
        print(f"  📊 AI Directories: Discovered {len(tools)} tools")
        return tools[:max_tools]

    async def _scrape_awesome_lists(self, max_tools: int = 1500) -> List[Dict[str, Any]]:
        """Scrape GitHub Awesome lists"""
        
        tools = []
        
        # Popular awesome lists for AI tools
        awesome_lists = [
            "https://raw.githubusercontent.com/sindresorhus/awesome/main/readme.md",
            "https://raw.githubusercontent.com/josephmisiti/awesome-machine-learning/master/README.md",
            "https://raw.githubusercontent.com/ChristosChristofidis/awesome-deep-learning/master/README.md",
            "https://raw.githubusercontent.com/owainlewis/awesome-artificial-intelligence/master/README.md"
        ]
        
        for list_url in awesome_lists:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.rate_limits['github'])
                
                async with self.session.get(list_url) as response:
                    if response.status == 200:
                        markdown = await response.text()
                        list_tools = self._parse_awesome_list_markdown(markdown, list_url)
                        tools.extend(list_tools)
                        
            except Exception as e:
                print(f"  ❌ Awesome list '{list_url}' failed: {e}")
                continue
        
        print(f"  📊 Awesome Lists: Discovered {len(tools)} tools")
        return tools[:max_tools]

    async def _scrape_tool_aggregators(self, max_tools: int = 2000) -> List[Dict[str, Any]]:
        """Scrape tool aggregator websites"""
        
        tools = []
        
        # Tool aggregator sites
        aggregators = [
            "https://www.g2.com/categories/artificial-intelligence",
            "https://www.capterra.com/artificial-intelligence-software/",
            "https://stackshare.io/artificial-intelligence"
        ]
        
        for aggregator_url in aggregators:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.rate_limits['scraping'])
                
                async with self.session.get(aggregator_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        aggregator_tools = self._parse_aggregator_page(html, aggregator_url)
                        tools.extend(aggregator_tools)
                        
            except Exception as e:
                print(f"  ❌ Aggregator '{aggregator_url}' failed: {e}")
                continue
        
        print(f"  📊 Tool Aggregators: Discovered {len(tools)} tools")
        return tools[:max_tools]

    def _parse_github_repo_to_tool(self, repo: dict) -> Optional[Dict[str, Any]]:
        """Convert GitHub repository to tool format"""
        
        try:
            # Determine tool type based on topics and description
            topics = repo.get('topics', [])
            description = repo.get('description', '').lower()
            
            tool_type = self._classify_github_tool_type(topics, description)
            
            return {
                "name": repo['name'],
                "website": repo['html_url'],
                "description": repo.get('description', ''),
                "tool_type": tool_type,
                "category": "Open Source",
                "pricing": "Open Source",
                "features": f"Stars: {repo['stargazers_count']}, Language: {repo.get('language', 'N/A')}, Topics: {', '.join(topics[:3])}",
                "confidence": min(0.9, 0.5 + (repo['stargazers_count'] / 1000) * 0.4),
                "source_data": json.dumps({
                    "source": "github",
                    "stars": repo['stargazers_count'],
                    "language": repo.get('language'),
                    "topics": topics
                })
            }
        except Exception as e:
            return None

    def _classify_github_tool_type(self, topics: List[str], description: str) -> str:
        """Classify GitHub repository into tool type"""
        
        classification_map = {
            'ai_writing_tools': ['writing', 'text-generation', 'gpt', 'content'],
            'ai_image_generation': ['image-generation', 'stable-diffusion', 'dalle', 'midjourney'],
            'ai_video_tools': ['video', 'deepfake', 'video-generation'],
            'ai_audio_tools': ['audio', 'speech', 'voice', 'music-generation'],
            'ai_coding_tools': ['code-generation', 'coding-assistant', 'copilot'],
            'ai_data_analysis': ['data-analysis', 'analytics', 'visualization'],
            'code_editors': ['editor', 'ide', 'vscode'],
            'ai_services': ['api', 'ml-platform', 'inference'],
            'creative_tools': ['design', 'art', 'creative'],
            'productivity_tools': ['productivity', 'automation', 'workflow']
        }
        
        # Check topics first
        for tool_type, keywords in classification_map.items():
            for keyword in keywords:
                if keyword in topics:
                    return tool_type
        
        # Check description
        for tool_type, keywords in classification_map.items():
            for keyword in keywords:
                if keyword in description:
                    return tool_type
        
        return 'ai_services'  # Default category

    def _parse_product_hunt_page(self, html: str, category: str) -> List[Dict[str, Any]]:
        """Parse Product Hunt category page"""
        
        tools = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Product Hunt uses dynamic loading, so this is a simplified parser
        # In practice, you might need to use selenium or their API
        
        # Look for product cards/links
        product_links = soup.find_all('a', href=re.compile(r'/posts/'))
        
        for link in product_links[:50]:  # Limit per page
            try:
                product_name = link.get_text(strip=True)
                product_url = f"https://www.producthunt.com{link['href']}"
                
                if product_name and len(product_name) > 2:
                    tools.append({
                        "name": product_name,
                        "website": product_url,
                        "description": f"Product featured on Product Hunt in {category} category",
                        "tool_type": self._map_ph_category_to_tool_type(category),
                        "category": category.replace('-', ' ').title(),
                        "pricing": "Unknown",
                        "features": "Product Hunt featured",
                        "confidence": 0.7,
                        "source_data": json.dumps({
                            "source": "product_hunt",
                            "category": category
                        })
                    })
            except:
                continue
        
        return tools

    def _parse_alternativeto_page(self, html: str, category: str) -> List[Dict[str, Any]]:
        """Parse AlternativeTo category page"""
        
        tools = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for app listings
        app_items = soup.find_all('div', class_=['appItem', 'item'])
        
        for item in app_items:
            try:
                name_elem = item.find('h3') or item.find('a', class_='appTitle')
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    
                    # Get URL if available
                    link_elem = item.find('a')
                    url = link_elem['href'] if link_elem else f"https://alternativeto.net/software/{name.lower().replace(' ', '-')}/"
                    
                    # Get description
                    desc_elem = item.find('p', class_='appDescription') or item.find('div', class_='description')
                    description = desc_elem.get_text(strip=True) if desc_elem else f"Alternative tool from {category} category"
                    
                    tools.append({
                        "name": name,
                        "website": url,
                        "description": description,
                        "tool_type": self._map_alternativeto_category(category),
                        "category": category.replace('-', ' ').title(),
                        "pricing": "Unknown",
                        "features": "AlternativeTo listed",
                        "confidence": 0.75,
                        "source_data": json.dumps({
                            "source": "alternativeto",
                            "category": category
                        })
                    })
            except:
                continue
        
        return tools

    def _parse_ai_directory_page(self, html: str, directory_url: str) -> List[Dict[str, Any]]:
        """Parse AI tool directory page"""
        
        tools = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Generic parsing for AI tool directories
        # Look for common patterns: cards, lists, links with tool names
        
        # Try different selectors commonly used in tool directories
        selectors = [
            'div[class*="tool"]',
            'div[class*="card"]', 
            'div[class*="item"]',
            'a[href*="tool"]',
            'h3 a',
            'h2 a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            
            for elem in elements[:100]:  # Limit per selector
                try:
                    name = elem.get_text(strip=True)
                    url = elem.get('href') if elem.name == 'a' else elem.find('a')['href'] if elem.find('a') else ""
                    
                    if name and len(name) > 2 and len(name) < 100:
                        # Get description from nearby elements
                        description = ""
                        parent = elem.parent
                        if parent:
                            desc_elem = parent.find('p') or parent.find('div', class_=re.compile(r'desc|summary'))
                            if desc_elem:
                                description = desc_elem.get_text(strip=True)[:200]
                        
                        if not description:
                            description = f"AI tool from {directory_url}"
                        
                        tools.append({
                            "name": name,
                            "website": url if url.startswith('http') else f"{directory_url}{url}",
                            "description": description,
                            "tool_type": "ai_services",
                            "category": "AI Directory",
                            "pricing": "Unknown",
                            "features": "Directory listed",
                            "confidence": 0.6,
                            "source_data": json.dumps({
                                "source": "ai_directory",
                                "directory": directory_url
                            })
                        })
                except:
                    continue
            
            if tools:  # If we found tools with this selector, break
                break
        
        return tools

    def _parse_awesome_list_markdown(self, markdown: str, list_url: str) -> List[Dict[str, Any]]:
        """Parse Awesome list markdown for tools"""
        
        tools = []
        
        # Extract links from markdown
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(link_pattern, markdown)
        
        for name, url in matches:
            if 'github.com' in url and len(name) > 2:
                tools.append({
                    "name": name,
                    "website": url,
                    "description": f"Tool from awesome list: {list_url.split('/')[-2]}",
                    "tool_type": "ai_services",
                    "category": "Awesome List",
                    "pricing": "Open Source",
                    "features": "Community curated",
                    "confidence": 0.8,
                    "source_data": json.dumps({
                        "source": "awesome_list",
                        "list_url": list_url
                    })
                })
        
        return tools

    def _parse_aggregator_page(self, html: str, aggregator_url: str) -> List[Dict[str, Any]]:
        """Parse tool aggregator page"""
        
        tools = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for product listings on aggregator sites
        product_selectors = [
            'div[data-testid*="product"]',
            'div[class*="product"]',
            'div[class*="listing"]',
            'h3 a',
            'h4 a'
        ]
        
        for selector in product_selectors:
            elements = soup.select(selector)
            
            for elem in elements[:50]:
                try:
                    if elem.name == 'a':
                        name = elem.get_text(strip=True)
                        url = elem.get('href')
                    else:
                        link = elem.find('a')
                        if link:
                            name = link.get_text(strip=True)
                            url = link.get('href')
                        else:
                            continue
                    
                    if name and len(name) > 2:
                        tools.append({
                            "name": name,
                            "website": url if url.startswith('http') else f"{aggregator_url}{url}",
                            "description": f"Tool from {aggregator_url}",
                            "tool_type": "business_tools",
                            "category": "Business Software",
                            "pricing": "Unknown",
                            "features": "Enterprise listed",
                            "confidence": 0.7,
                            "source_data": json.dumps({
                                "source": "aggregator",
                                "aggregator": aggregator_url
                            })
                        })
                except:
                    continue
            
            if tools:
                break
        
        return tools

    def _map_ph_category_to_tool_type(self, category: str) -> str:
        """Map Product Hunt category to our tool type"""
        mapping = {
            'artificial-intelligence': 'ai_services',
            'developer-tools': 'ai_coding_tools',
            'productivity': 'productivity_tools',
            'design-tools': 'creative_tools',
            'marketing': 'ai_marketing_tools',
            'analytics': 'ai_data_analysis'
        }
        return mapping.get(category, 'ai_services')

    def _map_alternativeto_category(self, category: str) -> str:
        """Map AlternativeTo category to our tool type"""
        mapping = {
            'artificial-intelligence': 'ai_services',
            'text-editor': 'code_editors',
            'image-editor': 'ai_image_generation',
            'video-editor': 'ai_video_tools',
            'audio-editor': 'ai_audio_tools',
            'development': 'ai_coding_tools',
            'productivity': 'productivity_tools',
            'automation': 'productivity_tools',
            'chatbot': 'ai_customer_service'
        }
        return mapping.get(category, 'ai_services')
    
    # ADD these methods to your src/agent/app/services/real_external_api_service.py

    async def _discover_chrome_extensions(self, max_tools: int = 2000) -> List[Dict[str, Any]]:
        """Discover Chrome Web Store extensions"""
        
        tools = []
        
        # Chrome Web Store categories for developer/productivity tools
        categories = [
            'productivity', 'developer-tools', 'utilities', 'communication', 
            'workflow', 'automation', 'analytics', 'design-tools', 'testing'
        ]
        
        # Chrome Web Store search (using web scraping approach)
        for category in categories:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(self.rate_limits['scraping'])
                
                # Chrome Web Store search URL
                url = f"https://chromewebstore.google.com/category/extensions/{category}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        category_tools = self._parse_chrome_store_page(html, category)
                        tools.extend(category_tools)
                        
            except Exception as e:
                print(f"  ❌ Chrome category '{category}' failed: {e}")
                continue
        
        print(f"  📊 Chrome Extensions: Discovered {len(tools)} extensions")
        return tools[:max_tools]

    async def _discover_vscode_extensions(self, max_tools: int = 1500) -> List[Dict[str, Any]]:
        """Discover VS Code Marketplace extensions"""
        
        tools = []
        
        # VS Code Marketplace API endpoint
        base_url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
        
        # Search categories for developer tools
        search_terms = [
            'productivity', 'developer', 'git', 'debugging', 'testing', 'automation',
            'language', 'theme', 'snippet', 'formatter', 'linter', 'ai', 'code'
        ]
        
        for term in search_terms:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(0.5)  # VS Code API is more generous
                
                # VS Code Marketplace API request body
                body = {
                    "filters": [
                        {
                            "criteria": [
                                {"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                                {"filterType": 10, "value": term},
                                {"filterType": 12, "value": "37888"}
                            ],
                            "pageNumber": 1,
                            "pageSize": 100,
                            "sortBy": 4,
                            "sortOrder": 0
                        }
                    ],
                    "assetTypes": [],
                    "flags": 914
                }
                
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json;api-version=3.0-preview.1'
                }
                
                async with self.session.post(base_url, json=body, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        term_tools = self._parse_vscode_marketplace_response(data, term)
                        tools.extend(term_tools)
                        
            except Exception as e:
                print(f"  ❌ VS Code term '{term}' failed: {e}")
                continue
        
        print(f"  📊 VS Code Extensions: Discovered {len(tools)} extensions")
        return tools[:max_tools]

    async def _discover_npm_packages(self, max_tools: int = 2000) -> List[Dict[str, Any]]:
        """Discover NPM packages"""
        
        tools = []
        
        # NPM search keywords for developer tools
        search_keywords = [
            'cli-tool', 'developer-tool', 'build-tool', 'automation', 'testing',
            'framework', 'library', 'utility', 'productivity', 'webpack', 'babel',
            'typescript', 'react', 'vue', 'angular', 'node', 'express', 'api'
        ]
        
        for keyword in search_keywords:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(0.2)  # NPM API is fast
                
                # NPM search API
                url = f"https://registry.npmjs.org/-/v1/search"
                params = {
                    'text': keyword,
                    'size': 100,
                    'from': 0,
                    'quality': 0.65,
                    'popularity': 0.98,
                    'maintenance': 0.5
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        keyword_tools = self._parse_npm_response(data, keyword)
                        tools.extend(keyword_tools)
                        
            except Exception as e:
                print(f"  ❌ NPM keyword '{keyword}' failed: {e}")
                continue
        
        print(f"  📊 NPM Packages: Discovered {len(tools)} packages")
        return tools[:max_tools]

    async def _discover_pypi_packages(self, max_tools: int = 1500) -> List[Dict[str, Any]]:
        """Discover PyPI packages"""
        
        tools = []
        
        # PyPI search keywords for developer tools
        search_keywords = [
            'cli', 'tool', 'automation', 'testing', 'framework', 'library',
            'web', 'api', 'data', 'machine-learning', 'ai', 'productivity',
            'development', 'utilities', 'scraping', 'analysis'
        ]
        
        for keyword in search_keywords:
            if len(tools) >= max_tools:
                break
                
            try:
                await asyncio.sleep(0.3)
                
                # PyPI simple search (we'll scrape search results)
                url = f"https://pypi.org/search/"
                params = {'q': keyword}
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        keyword_tools = self._parse_pypi_search_page(html, keyword)
                        tools.extend(keyword_tools)
                        
            except Exception as e:
                print(f"  ❌ PyPI keyword '{keyword}' failed: {e}")
                continue
        
        print(f"  📊 PyPI Packages: Discovered {len(tools)} packages")
        return tools[:max_tools]

    # PARSING METHODS - Add these too

    def _parse_chrome_store_page(self, html: str, category: str) -> List[Dict[str, Any]]:
        """Parse Chrome Web Store search page"""
        
        tools = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for extension cards
        extension_elements = soup.find_all('div', class_=re.compile(r'.*item.*|.*extension.*|.*app.*'))
        
        for elem in extension_elements[:50]:  # Limit per category
            try:
                name_elem = elem.find('h3') or elem.find('div', class_=re.compile(r'.*title.*|.*name.*'))
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    
                    if name and len(name) > 2:
                        tools.append({
                            "name": name,
                            "website": f"https://chromewebstore.google.com/search/{name.replace(' ', '%20')}",
                            "description": f"Chrome extension from {category} category",
                            "tool_type": "browser_extensions",
                            "category": category.replace('-', ' ').title(),
                            "pricing": "Free",
                            "features": f"Chrome extension, {category}",
                            "confidence": 0.8,
                            "source_data": json.dumps({
                                "source": "chrome_web_store",
                                "category": category
                            })
                        })
            except:
                continue
        
        return tools

    def _parse_vscode_marketplace_response(self, data: dict, search_term: str) -> List[Dict[str, Any]]:
        """Parse VS Code Marketplace API response"""
        
        tools = []
        
        try:
            extensions = data.get('results', [{}])[0].get('extensions', [])
            
            for ext in extensions:
                try:
                    name = ext.get('displayName', '')
                    publisher = ext.get('publisher', {}).get('displayName', '')
                    
                    if name:
                        tools.append({
                            "name": f"{name} (VS Code)",
                            "website": f"https://marketplace.visualstudio.com/items?itemName={publisher}.{ext.get('extensionName', '')}",
                            "description": ext.get('shortDescription', f"VS Code extension for {search_term}"),
                            "tool_type": "code_editors",
                            "category": "VS Code Extension",
                            "pricing": "Free",
                            "features": f"VS Code extension, {search_term}",
                            "confidence": 0.85,
                            "source_data": json.dumps({
                                "source": "vscode_marketplace",
                                "search_term": search_term,
                                "publisher": publisher
                            })
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"    ❌ Error parsing VS Code response: {e}")
        
        return tools

    def _parse_npm_response(self, data: dict, keyword: str) -> List[Dict[str, Any]]:
        """Parse NPM search API response"""
        
        tools = []
        
        try:
            packages = data.get('objects', [])
            
            for pkg in packages:
                try:
                    package_data = pkg.get('package', {})
                    name = package_data.get('name', '')
                    
                    if name:
                        tools.append({
                            "name": f"{name} (NPM)",
                            "website": f"https://www.npmjs.com/package/{name}",
                            "description": package_data.get('description', f"NPM package for {keyword}"),
                            "tool_type": "web_applications",
                            "category": "NPM Package",
                            "pricing": "Open Source",
                            "features": f"NPM package, {keyword}, JavaScript/Node.js",
                            "confidence": 0.75,
                            "source_data": json.dumps({
                                "source": "npm",
                                "keyword": keyword,
                                "version": package_data.get('version', ''),
                                "weekly_downloads": pkg.get('searchScore', 0)
                            })
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"    ❌ Error parsing NPM response: {e}")
        
        return tools

    def _parse_pypi_search_page(self, html: str, keyword: str) -> List[Dict[str, Any]]:
        """Parse PyPI search results page"""
        
        tools = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for package listings
        package_elements = soup.find_all('a', class_=re.compile(r'.*package.*|.*result.*'))
        
        for elem in package_elements[:30]:  # Limit per keyword
            try:
                name_elem = elem.find('span', class_=re.compile(r'.*name.*')) or elem.find('h3')
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    
                    if name and len(name) > 1:
                        tools.append({
                            "name": f"{name} (Python)",
                            "website": f"https://pypi.org/project/{name}/",
                            "description": f"Python package for {keyword}",
                            "tool_type": "ai_coding_tools",
                            "category": "Python Package",
                            "pricing": "Open Source",
                            "features": f"Python package, {keyword}, PyPI",
                            "confidence": 0.75,
                            "source_data": json.dumps({
                                "source": "pypi",
                                "keyword": keyword
                            })
                        })
            except:
                continue
        
        return tools

# Global service instance
real_external_api_service = RealExternalAPIService()