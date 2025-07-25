# Add these methods to your existing UnifiedRealAPIsService class in real_apis_service.py

# ================================================================
# ENTERPRISE-GRADE INCREMENTAL DISCOVERY METHODS
# ================================================================

def run_sync_discover_all_real_apis_incremental(self, target_tools: int = 30000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise-grade incremental discovery for all real APIs"""
    return asyncio.run(self.discover_all_real_apis_incremental(target_tools, incremental_params))

def run_sync_discover_no_auth_apis_incremental(self, target_tools: int = 15000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise-grade incremental discovery for no-auth APIs"""
    return asyncio.run(self.discover_no_auth_apis_incremental(target_tools, incremental_params))

def run_sync_discover_github_incremental(self, target_tools: int = 6000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise-grade incremental GitHub discovery"""
    return asyncio.run(self._discover_single_api_incremental("github", self._discover_github_incremental, target_tools, incremental_params))

def run_sync_discover_npm_incremental(self, target_tools: int = 4000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise-grade incremental NPM discovery"""
    return asyncio.run(self._discover_single_api_incremental("npm", self._discover_npm_incremental, target_tools, incremental_params))

def run_sync_discover_reddit_incremental(self, target_tools: int = 3000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise-grade incremental Reddit discovery"""
    return asyncio.run(self._discover_single_api_incremental("reddit", self._discover_reddit_incremental, target_tools, incremental_params))

def run_sync_discover_hackernews_incremental(self, target_tools: int = 2500, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise-grade incremental Hacker News discovery"""
    return asyncio.run(self._discover_single_api_incremental("hackernews", self._discover_hackernews_incremental, target_tools, incremental_params))

def run_sync_discover_producthunt_incremental(self, target_tools: int = 4000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise-grade incremental Product Hunt discovery"""
    return asyncio.run(self._discover_single_api_incremental("producthunt", self._discover_producthunt_incremental, target_tools, incremental_params))

def run_sync_discover_crunchbase_incremental(self, target_tools: int = 2000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise-grade incremental Crunchbase discovery"""
    return asyncio.run(self._discover_single_api_incremental("crunchbase", self._discover_crunchbase_incremental, target_tools, incremental_params))

def run_sync_discover_stackoverflow_incremental(self, target_tools: int = 3000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise-grade incremental Stack Overflow discovery"""
    return asyncio.run(self._discover_single_api_incremental("stackoverflow", self._discover_stackoverflow_incremental, target_tools, incremental_params))

# ================================================================
# CORE INCREMENTAL ASYNC METHODS
# ================================================================

async def discover_all_real_apis_incremental(self, target_tools: int = 30000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise incremental discovery for all real APIs"""
    
    # Handle incremental parameters
    incremental_params = incremental_params or {}
    force_full_scan = incremental_params.get("force_full_scan", False)
    last_check_times = incremental_params.get("last_check_times", {})
    
    results = {
        "discovery_id": f"incremental_all_apis_{int(time.time())}",
        "start_time": datetime.utcnow().isoformat(),
        "target_tools": target_tools,
        "total_discovered": 0,
        "total_saved": 0,
        "total_skipped": 0,
        "api_results": {},
        "processing_mode": "incremental_real_apis",
        "incremental_params": incremental_params
    }
    
    print(f"🚀 INCREMENTAL ALL REAL APIs DISCOVERY")
    print(f"🎯 Target: {target_tools} tools")
    print(f"⚡ Mode: {'FULL SCAN' if force_full_scan else 'INCREMENTAL'}")
    
    # Enhanced incremental API tasks
    api_tasks = [
        ("GitHub API", "github", self._discover_github_incremental, 5000),
        ("NPM Registry API", "npm", self._discover_npm_incremental, 3000),
        ("Product Hunt API", "producthunt", self._discover_producthunt_incremental, 4000),
        ("Reddit API", "reddit", self._discover_reddit_incremental, 3000),
        ("Hacker News API", "hackernews", self._discover_hackernews_incremental, 2000),
        ("Stack Overflow API", "stackoverflow", self._discover_stackoverflow_incremental, 3000),
        ("Crunchbase API", "crunchbase", self._discover_crunchbase_incremental, 2000),
        ("PyPI JSON API", "pypi", self._discover_pypi_incremental, 2500),
        ("VS Code Marketplace API", "vscode", self._discover_vscode_incremental, 2000)
    ]
    
    # Filter ready APIs
    ready_apis = []
    for api_name, api_key, discovery_func, max_tools in api_tasks:
        if self._is_api_ready(api_key):
            # Check if we should skip due to incremental logic
            last_check = last_check_times.get(api_key)
            should_skip = self._should_skip_api_incremental(api_key, last_check, force_full_scan)
            
            if should_skip:
                print(f"⏭️  {api_name}: Skipped (recently checked)")
                results["api_results"][api_name] = {
                    "tools_discovered": 0,
                    "tools_skipped": max_tools,  # Estimate skipped
                    "processing_time": 0,
                    "success": True,
                    "incremental_skip": True,
                    "last_check": last_check
                }
                results["total_skipped"] += max_tools
            else:
                ready_apis.append((api_name, api_key, discovery_func, max_tools))
        else:
            print(f"⚠️  {api_name}: Not configured (will skip)")
    
    print(f"✅ APIs to process: {len(ready_apis)}")
    print(f"⏭️ APIs skipped: {len([r for r in results['api_results'].values() if r.get('incremental_skip')])}")
    
    if not ready_apis:
        print("🎯 All APIs recently checked - no discovery needed")
        results["end_time"] = datetime.utcnow().isoformat()
        return results
    
    # Process APIs that need updating
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={'User-Agent': 'AI Tool Discovery System v4.0 - Incremental'}
    ) as session:
        
        all_tools = []
        
        for api_name, api_key, discovery_func, max_tools in ready_apis:
            if results["total_discovered"] >= target_tools:
                break
                
            print(f"\n📡 Processing: {api_name}")
            start_time = time.time()
            
            try:
                # Pass incremental parameters to each API method
                api_incremental_params = self._prepare_api_incremental_params(api_key, incremental_params)
                tools = await discovery_func(session, max_tools, api_incremental_params)
                
                processing_time = time.time() - start_time
                
                results["api_results"][api_name] = {
                    "tools_discovered": len(tools),
                    "tools_skipped": 0,
                    "processing_time": round(processing_time, 2),
                    "success": True,
                    "api_type": "real_api_incremental",
                    "incremental_skip": False
                }
                
                results["total_discovered"] += len(tools)
                all_tools.extend(tools)
                
                print(f"  ✅ {api_name}: {len(tools)} new tools ({processing_time:.1f}s)")
                
            except Exception as e:
                print(f"  ❌ {api_name} failed: {str(e)}")
                results["api_results"][api_name] = {
                    "error": str(e),
                    "tools_discovered": 0,
                    "tools_skipped": 0,
                    "success": False,
                    "incremental_skip": False
                }
    
    # Save tools to database
    if all_tools:
        print(f"\n💾 Saving {len(all_tools)} tools to database...")
        db = SessionLocal()
        try:
            save_result = save_discovered_tools_with_deduplication(db, all_tools)
            results["total_saved"] = save_result.get("saved", 0)
            results["database_result"] = save_result
        finally:
            db.close()
    
    results["end_time"] = datetime.utcnow().isoformat()
    results["successful_apis"] = len([r for r in results["api_results"].values() if r.get("success")])
    
    print(f"\n🎊 INCREMENTAL REAL APIs DISCOVERY COMPLETE!")
    print(f"📈 RESULTS:")
    print(f"   • Total tools discovered: {results['total_discovered']}")
    print(f"   • Total tools saved: {results['total_saved']}")
    print(f"   • Total tools skipped: {results['total_skipped']}")
    print(f"   • Successful APIs: {results['successful_apis']}")
    
    return results

async def discover_no_auth_apis_incremental(self, target_tools: int = 15000, incremental_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enterprise incremental discovery for no-auth APIs"""
    
    incremental_params = incremental_params or {}
    force_full_scan = incremental_params.get("force_full_scan", False)
    last_check_times = incremental_params.get("last_check_times", {})
    
    results = {
        "discovery_id": f"incremental_no_auth_apis_{int(time.time())}",
        "start_time": datetime.utcnow().isoformat(),
        "target_tools": target_tools,
        "total_discovered": 0,
        "total_saved": 0,
        "total_skipped": 0,
        "api_results": {},
        "processing_mode": "incremental_no_auth_apis"
    }
    
    print(f"⚡ INCREMENTAL NO-AUTH APIs DISCOVERY")
    print(f"🎯 Target: {target_tools} tools")
    print(f"⚡ Mode: {'FULL SCAN' if force_full_scan else 'INCREMENTAL'}")
    
    # No-auth API tasks with incremental support
    no_auth_tasks = [
        ("GitHub API", "github", self._discover_github_incremental, 3000),
        ("NPM Registry API", "npm", self._discover_npm_incremental, 3000),
        ("Reddit API", "reddit", self._discover_reddit_incremental, 2000),
        ("Hacker News API", "hackernews", self._discover_hackernews_incremental, 2500),
        ("Stack Overflow API", "stackoverflow", self._discover_stackoverflow_incremental, 3000),
        ("PyPI JSON API", "pypi", self._discover_pypi_incremental, 2500),
        ("VS Code Marketplace API", "vscode", self._discover_vscode_incremental, 2000)
    ]
    
    # Filter APIs that need processing
    ready_apis = []
    for api_name, api_key, discovery_func, max_tools in no_auth_tasks:
        last_check = last_check_times.get(api_key)
        should_skip = self._should_skip_api_incremental(api_key, last_check, force_full_scan)
        
        if should_skip:
            print(f"⏭️  {api_name}: Skipped (recently checked)")
            results["api_results"][api_name] = {
                "tools_discovered": 0,
                "tools_skipped": max_tools,
                "processing_time": 0,
                "success": True,
                "incremental_skip": True
            }
            results["total_skipped"] += max_tools
        else:
            ready_apis.append((api_name, api_key, discovery_func, max_tools))
    
    if not ready_apis:
        print("🎯 All no-auth APIs recently checked")
        results["end_time"] = datetime.utcnow().isoformat()
        return results
    
    # Process APIs
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={'User-Agent': 'AI Tool Discovery System v4.0 - Incremental'}
    ) as session:
        
        all_tools = []
        
        for api_name, api_key, discovery_func, max_tools in ready_apis:
            if len(all_tools) >= target_tools:
                break
                
            print(f"\n📡 Processing: {api_name}")
            start_time = time.time()
            
            try:
                api_incremental_params = self._prepare_api_incremental_params(api_key, incremental_params)
                tools = await discovery_func(session, max_tools, api_incremental_params)
                
                processing_time = time.time() - start_time
                all_tools.extend(tools)
                
                results["api_results"][api_name] = {
                    "tools_discovered": len(tools),
                    "tools_skipped": 0,
                    "processing_time": round(processing_time, 2),
                    "success": True,
                    "incremental_skip": False
                }
                
                print(f"  ✅ {api_name}: {len(tools)} new tools ({processing_time:.1f}s)")
                
            except Exception as e:
                print(f"  ❌ {api_name} failed: {e}")
                results["api_results"][api_name] = {
                    "error": str(e),
                    "tools_discovered": 0,
                    "success": False,
                    "incremental_skip": False
                }
    
    results["total_discovered"] = len(all_tools)
    
    # Save to database
    if all_tools:
        print(f"\n💾 Saving {len(all_tools)} tools to database...")
        db = SessionLocal()
        try:
            save_result = save_discovered_tools_with_deduplication(db, all_tools)
            results["total_saved"] = save_result.get("saved", 0)
        finally:
            db.close()
    
    results["end_time"] = datetime.utcnow().isoformat()
    return results

# ================================================================
# INDIVIDUAL API INCREMENTAL METHODS
# ================================================================

async def _discover_single_api_incremental(self, api_name: str, discovery_func, target_tools: int, incremental_params: Dict[str, Any] = None):
    """Generic wrapper for single API incremental discovery"""
    
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
    
    # Process API
    start_time = time.time()
    
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={'User-Agent': 'AI Tool Discovery System v4.0 - Incremental'}
    ) as session:
        
        api_incremental_params = self._prepare_api_incremental_params(api_name, incremental_params)
        tools = await discovery_func(session, target_tools, api_incremental_params)
        
        processing_time = time.time() - start_time
        
        # Save to database
        total_saved = 0
        if tools:
            db = SessionLocal()
            try:
                save_result = save_discovered_tools_with_deduplication(db, tools)
                total_saved = save_result.get("saved", 0)
            finally:
                db.close()
        
        return {
            "success": True,
            "total_saved": total_saved,
            "total_skipped": 0,
            "incremental_skip": False,
            "processing_time": round(processing_time, 2),
            "tools_discovered": len(tools)
        }

async def _discover_github_incremental(self, session: aiohttp.ClientSession, max_tools: int, incremental_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """GitHub API with incremental support using 'pushed' parameter"""
    
    tools = []
    incremental_params = incremental_params or {}
    
    # Calculate 'since' parameter for incremental updates
    since_date = self._get_since_date_for_api("github", incremental_params)
    
    search_queries = [
        "ai tool stars:>50", "developer-tools stars:>100", "cli tool stars:>40",
        "automation tool stars:>60", "productivity stars:>80", "testing tool stars:>30"
    ]
    
    headers = {'User-Agent': 'AI Tool Discovery v4.0 - Incremental'}
    
    if self.apis['github']['token']:
        headers['Authorization'] = f"token {self.apis['github']['token']}"
    
    print(f"    🔍 GitHub: Using incremental mode (since: {since_date})")
    
    for query in search_queries:
        if len(tools) >= max_tools:
            break
            
        try:
            await asyncio.sleep(self.apis['github']['rate_limit'])
            
            url = f"{self.apis['github']['base_url']}/search/repositories"
            
            # Add date filter for incremental
            incremental_query = f"{query} pushed:>={since_date}"
            
            params = {
                'q': incremental_query,
                'sort': 'updated',  # Sort by recently updated
                'order': 'desc',
                'per_page': 50
            }
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for repo in data.get('items', []):
                        if len(tools) >= max_tools:
                            break
                            
                        # Additional filtering for incremental mode
                        repo_updated = repo.get('updated_at', '')
                        if self._is_item_recent_enough(repo_updated, since_date):
                            tool = self._parse_github_repo(repo)
                            if tool:
                                tools.append(tool)
                                
                elif response.status == 403:
                    print(f"    ⚠️ GitHub rate limit hit, waiting...")
                    await asyncio.sleep(60)
                    
        except Exception as e:
            print(f"    ❌ GitHub query error: {e}")
            continue
    
    print(f"    ✅ GitHub incremental: {len(tools)} updated repositories")
    return tools

async def _discover_npm_incremental(self, session: aiohttp.ClientSession, max_tools: int, incremental_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """NPM API with incremental support"""
    
    tools = []
    incremental_params = incremental_params or {}
    
    since_date = self._get_since_date_for_api("npm", incremental_params)
    
    keywords = [
        'cli', 'tool', 'framework', 'library', 'utility', 'build-tool',
        'developer-tool', 'automation', 'testing', 'productivity'
    ]
    
    print(f"    🔍 NPM: Using incremental mode (since: {since_date})")
    
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
                    
                    for pkg_obj in data.get('objects', []):
                        package_data = pkg_obj.get('package', {})
                        
                        # Check if package was modified since last check
                        modified_date = package_data.get('date', '')
                        if self._is_item_recent_enough(modified_date, since_date):
                            tool = self._parse_npm_package_incremental(package_data, keyword)
                            if tool:
                                tools.append(tool)
                        
                        if len(tools) >= max_tools:
                            break
                            
        except Exception as e:
            print(f"    ❌ NPM keyword '{keyword}' error: {e}")
            continue
    
    print(f"    ✅ NPM incremental: {len(tools)} updated packages")
    return tools

async def _discover_reddit_incremental(self, session: aiohttp.ClientSession, max_tools: int, incremental_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Reddit API with incremental support using created_utc"""
    
    tools = []
    incremental_params = incremental_params or {}
    
    since_timestamp = self._get_since_timestamp_for_api("reddit", incremental_params)
    
    subreddits = [
        'artificial', 'MachineLearning', 'programming', 'webdev',
        'SideProject', 'startups', 'Entrepreneur', 'productivity'
    ]
    
    print(f"    🔍 Reddit: Using incremental mode (since: {datetime.fromtimestamp(since_timestamp)})")
    
    for subreddit in subreddits:
        if len(tools) >= max_tools:
            break
            
        try:
            await asyncio.sleep(self.apis['reddit']['rate_limit'])
            
            url = f"{self.apis['reddit']['base_url']}/r/{subreddit}/new.json"  # Use 'new' for incremental
            params = {'limit': 25}
            headers = {'User-Agent': 'AI Tool Discovery Bot 1.0 - Incremental'}
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for post in data.get("data", {}).get("children", []):
                        post_data = post.get("data", {})
                        created_utc = post_data.get("created_utc", 0)
                        
                        # Only process posts created after last check
                        if created_utc > since_timestamp:
                            tool = self._parse_reddit_post_incremental(post_data, subreddit)
                            if tool:
                                tools.append(tool)
                        
                        if len(tools) >= max_tools:
                            break
                            
        except Exception as e:
            print(f"    ❌ Reddit r/{subreddit} error: {e}")
            continue
    
    print(f"    ✅ Reddit incremental: {len(tools)} new posts")
    return tools

async def _discover_hackernews_incremental(self, session: aiohttp.ClientSession, max_tools: int, incremental_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Hacker News API with incremental support"""
    
    tools = []
    incremental_params = incremental_params or {}
    
    since_timestamp = self._get_since_timestamp_for_api("hackernews", incremental_params)
    
    try:
        print(f"    🔍 Hacker News: Using incremental mode (since: {datetime.fromtimestamp(since_timestamp)})")
        
        # Get new stories instead of top stories for incremental
        url = f"{self.apis['hackernews']['base_url']}/newstories.json"
        
        async with session.get(url) as response:
            if response.status == 200:
                story_ids = await response.json()
                
                for story_id in story_ids[:100]:  # Check more recent stories
                    if len(tools) >= max_tools:
                        break
                        
                    await asyncio.sleep(self.apis['hackernews']['rate_limit'])
                    
                    story_url = f"{self.apis['hackernews']['base_url']}/item/{story_id}.json"
                    
                    async with session.get(story_url) as story_response:
                        if story_response.status == 200:
                            story = await story_response.json()
                            story_time = story.get('time', 0)
                            
                            # Only process stories newer than last check
                            if story_time > since_timestamp:
                                tool = self._parse_hackernews_story(story)
                                if tool:
                                    tools.append(tool)
                            
    except Exception as e:
        print(f"    ❌ Hacker News incremental error: {e}")
    
    print(f"    ✅ Hacker News incremental: {len(tools)} new stories")
    return tools

async def _discover_producthunt_incremental(self, session: aiohttp.ClientSession, max_tools: int, incremental_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Product Hunt API with incremental support"""
    
    tools = []
    incremental_params = incremental_params or {}
    
    since_date = self._get_since_date_for_api("producthunt", incremental_params)
    
    access_token = await self._get_producthunt_token(session)
    if not access_token:
        print(f"    ❌ Product Hunt: Could not get access token")
        return tools
    
    print(f"    🔍 Product Hunt: Using incremental mode (since: {since_date})")
    
    # GraphQL query with date filtering for incremental
    query = f"""
        query IncrementalPosts($first: Int!, $postedAfter: DateTime!) {{
            posts(first: $first, postedAfter: $postedAfter, order: NEWEST) {{
                edges {{
                    node {{
                        id name tagline description url website
                        votesCount commentsCount featuredAt
                        topics {{ edges {{ node {{ name }} }} }}
                    }}
                }}
            }}
        }}
    """
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        payload = {
            "query": query,
            "variables": {
                "first": max_tools,
                "postedAfter": since_date
            }
        }
        
        async with session.post(self.apis['producthunt']['base_url'], 
                              json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                if "errors" not in data and "data" in data:
                    tools = self._parse_producthunt_response(data, "Incremental")
                    print(f"    ✅ Product Hunt incremental: {len(tools)} new posts")
                else:
                    print(f"    ⚠️ Product Hunt: GraphQL errors in incremental query")
            else:
                print(f"    ❌ Product Hunt incremental: HTTP {response.status}")
                
    except Exception as e:
        print(f"    ❌ Product Hunt incremental error: {e}")
    
    return tools

async def _discover_crunchbase_incremental(self, session: aiohttp.ClientSession, max_tools: int, incremental_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Crunchbase API with incremental support"""
    
    tools = []
    incremental_params = incremental_params or {}
    
    api_key = self.apis['crunchbase']['api_key']
    if not api_key:
        return tools
    
    since_date = self._get_since_date_for_api("crunchbase", incremental_params)
    
    print(f"    🔍 Crunchbase: Using incremental mode (since: {since_date})")
    
    try:
        url = f"{self.apis['crunchbase']['base_url']}/searches/organizations"
        
        headers = {
            'X-cb-user-key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Search with date filtering for incremental
        search_data = {
            "field_ids": [
                "identifier", "name", "short_description", "website",
                "categories", "funding_total", "last_funding_at", "updated_at"
            ],
            "query": [
                {
                    "type": "predicate",
                    "field_id": "categories",
                    "operator_id": "includes",
                    "values": ["artificial-intelligence", "machine-learning", "automation"]
                },
                {
                    "type": "predicate",
                    "field_id": "updated_at",
                    "operator_id": "gte",
                    "values": [since_date]
                }
            ],
            "limit": min(50, max_tools)
        }
        
        await asyncio.sleep(self.apis['crunchbase']['rate_limit'])
        
        async with session.post(url, json=search_data, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                tools = self._parse_crunchbase_response(data)
                print(f"    ✅ Crunchbase incremental: {len(tools)} updated companies")
            else:
                print(f"    ❌ Crunchbase incremental: HTTP {response.status}")
                
    except Exception as e:
        print(f"    ❌ Crunchbase incremental error: {e}")
    
    return tools

async def _discover_stackoverflow_incremental(self, session: aiohttp.ClientSession, max_tools: int, incremental_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Stack Overflow API with incremental support using fromdate"""
    
    tools = []
    incremental_params = incremental_params or {}
    
    since_timestamp = self._get_since_timestamp_for_api("stackoverflow", incremental_params)
    tags = ['tools', 'javascript', 'python', 'productivity']
    
    print(f"    🔍 Stack Overflow: Using incremental mode (since: {datetime.fromtimestamp(since_timestamp)})")
    
    for tag in tags:
        if len(tools) >= max_tools:
            break
            
        try:
            await asyncio.sleep(self.apis['stackoverflow']['rate_limit'])
            
            url = f"{self.apis['stackoverflow']['base_url']}/questions"
            params = {
                'order': 'desc',
                'sort': 'activity',  # Sort by recent activity
                'tagged': tag,
                'site': 'stackoverflow',
                'pagesize': 50,
                'filter': 'withbody',
                'fromdate': int(since_timestamp)  # Incremental parameter
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    tag_tools = self._parse_stackoverflow_questions(data, tag)
                    tools.extend(tag_tools)
                    
        except Exception as e:
            print(f"    ❌ Stack Overflow tag '{tag}' error: {e}")
            continue
    
    print(f"    ✅ Stack Overflow incremental: {len(tools)} recent questions")
    return tools

async def _discover_pypi_incremental(self, session: aiohttp.ClientSession, max_tools: int, incremental_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """PyPI API with incremental support (simplified - PyPI has limited incremental options)"""
    
    tools = []
    incremental_params = incremental_params or {}
    
    # PyPI doesn't have great incremental support, so we'll use a different strategy
    # Focus on recently updated popular packages
    since_date = self._get_since_date_for_api("pypi", incremental_params)
    
    print(f"    🔍 PyPI: Using incremental mode (limited API support)")
    
    # Get popular packages that might have been updated
    popular_packages = [
        'requests', 'flask', 'django', 'fastapi', 'pandas', 'numpy',
        'click', 'pytest', 'black', 'mypy', 'asyncio', 'aiohttp'
    ]
    
    for package in popular_packages[:max_tools]:
        try:
            await asyncio.sleep(self.apis['pypi']['rate_limit'])
            
            url = f"{self.apis['pypi']['base_url']}/pypi/{package}/json"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if package was updated since last check
                    release_date = self._get_pypi_latest_release_date(data)
                    if self._is_item_recent_enough(release_date, since_date):
                        tool = self._parse_pypi_package(data, package)
                        if tool:
                            tools.append(tool)
                            
        except Exception as e:
            continue
    
    print(f"    ✅ PyPI incremental: {len(tools)} updated packages")
    return tools

async def _discover_vscode_incremental(self, session: aiohttp.ClientSession, max_tools: int, incremental_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """VS Code Marketplace API with incremental support"""
    
    tools = []
    incremental_params = incremental_params or {}
    
    # VS Code marketplace doesn't have direct date filtering, so we'll sort by update date
    search_terms = ['productivity', 'git', 'python', 'javascript']
    
    print(f"    🔍 VS Code: Using incremental mode (sort by recent updates)")
    
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
                    "pageSize": 30,
                    "sortBy": 4,  # Sort by update date
                    "sortOrder": 1  # Descending
                }],
                "flags": 914
            }
            
            headers = {'Content-Type': 'application/json'}
            
            async with session.post(url, json=body, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    term_tools = self._parse_vscode_response(data, term)
                    tools.extend(term_tools[:10])  # Limit per term for incremental
                    
        except Exception as e:
            continue
    
    print(f"    ✅ VS Code incremental: {len(tools)} recently updated extensions")
    return tools

# ================================================================
# INCREMENTAL HELPER METHODS
# ================================================================

def _should_skip_api_incremental(self, api_name: str, last_check: str, force_full_scan: bool) -> bool:
    """Determine if an API should be skipped in incremental mode"""
    
    if force_full_scan:
        return False
    
    if not last_check:
        return False  # First time, don't skip
    
    try:
        last_check_dt = datetime.fromisoformat(last_check)
        hours_since = (datetime.utcnow() - last_check_dt).total_seconds() / 3600
        
        # API-specific skip thresholds
        skip_thresholds = {
            "github": 2,         # Check every 2 hours (active development)
            "npm": 4,           # Check every 4 hours (frequent updates)
            "reddit": 1,        # Check every hour (very active)
            "hackernews": 2,    # Check every 2 hours (active)
            "stackoverflow": 6, # Check every 6 hours (less frequent)
            "producthunt": 24,  # Check daily (new products daily)
            "crunchbase": 24,   # Check daily (business data)
            "pypi": 12,         # Check every 12 hours
            "vscode": 12        # Check every 12 hours
        }
        
        threshold = skip_thresholds.get(api_name, 6)  # Default 6 hours
        return hours_since < threshold
        
    except Exception:
        return False  # If error parsing date, don't skip

def _prepare_api_incremental_params(self, api_name: str, incremental_params: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare API-specific incremental parameters"""
    
    api_params = {
        "api_name": api_name,
        "force_full_scan": incremental_params.get("force_full_scan", False),
        "incremental_mode": incremental_params.get("incremental_mode", True)
    }
    
    # Add last check time for this specific API
    last_check_times = incremental_params.get("last_check_times", {})
    if api_name in last_check_times:
        api_params["last_check"] = last_check_times[api_name]
    
    return api_params

def _get_since_date_for_api(self, api_name: str, incremental_params: Dict[str, Any]) -> str:
    """Get 'since' date for API incremental queries (ISO format)"""
    
    last_check_times = incremental_params.get("last_check_times", {})
    last_check = last_check_times.get(api_name)
    
    if last_check:
        try:
            # Use last check time
            return datetime.fromisoformat(last_check).isoformat()
        except:
            pass
    
    # Default fallback - last 24 hours
    default_since = datetime.utcnow() - timedelta(days=1)
    return default_since.isoformat()

def _get_since_timestamp_for_api(self, api_name: str, incremental_params: Dict[str, Any]) -> int:
    """Get 'since' timestamp for API incremental queries (Unix timestamp)"""
    
    last_check_times = incremental_params.get("last_check_times", {})
    last_check = last_check_times.get(api_name)
    
    if last_check:
        try:
            # Use last check time
            return int(datetime.fromisoformat(last_check).timestamp())
        except:
            pass
    
    # Default fallback - last 24 hours
    default_since = datetime.utcnow() - timedelta(days=1)
    return int(default_since.timestamp())

def _is_item_recent_enough(self, item_date: str, since_date: str) -> bool:
    """Check if an item is recent enough for incremental processing"""
    
    if not item_date or not since_date:
        return True  # Include if we can't determine
    
    try:
        item_dt = datetime.fromisoformat(item_date.replace('Z', '+00:00'))
        since_dt = datetime.fromisoformat(since_date.replace('Z', '+00:00'))
        return item_dt > since_dt
    except Exception:
        return True  # Include if error parsing dates

def _get_pypi_latest_release_date(self, package_data: Dict[str, Any]) -> str:
    """Extract latest release date from PyPI package data"""
    
    try:
        releases = package_data.get("releases", {})
        if not releases:
            return ""
        
        # Get the latest version
        info = package_data.get("info", {})
        latest_version = info.get("version", "")
        
        if latest_version and latest_version in releases:
            release_files = releases[latest_version]
            if release_files:
                # Get upload time of first file
                return release_files[0].get("upload_time_iso_8601", "")
        
        return ""
    except Exception:
        return ""

def _parse_npm_package_incremental(self, package_data: Dict[str, Any], keyword: str) -> Optional[Dict[str, Any]]:
    """Parse NPM package with incremental-specific handling"""
    
    name = package_data.get('name', '')
    if not name:
        return None
    
    return {
        "name": name,
        "website": f"https://www.npmjs.com/package/{name}",
        "description": package_data.get('description', ''),
        "tool_type": "web_applications",
        "category": "NPM Package",
        "pricing": "Open Source",
        "features": f"NPM, {keyword}, Updated recently",
        "confidence": 0.75,
        "source_data": json.dumps({
            "source": "npm_api_incremental",
            "keyword": keyword,
            "modified_date": package_data.get('date', '')
        })
    }

def _parse_reddit_post_incremental(self, post_data: Dict[str, Any], subreddit: str) -> Optional[Dict[str, Any]]:
    """Parse Reddit post with incremental-specific handling"""
    
    title = post_data.get("title", "").strip()
    url = post_data.get("url", "").strip()
    selftext = post_data.get("selftext", "").strip()
    
    # Skip if no title or URL
    if not title or not url or len(title) < 10:
        return None
    
    # Filter for tool-related posts
    title_lower = title.lower()
    tool_keywords = [
        'tool', 'app', 'platform', 'service', 'api', 'library',
        'framework', 'ai', 'automation', 'generator', 'built',
        'created', 'launched', 'released', 'new'
    ]
    
    if not any(keyword in title_lower for keyword in tool_keywords):
        return None
    
    # Skip reddit URLs
    if 'reddit.com' in url:
        return None
    
    # Build description
    description = title
    if selftext and len(selftext) > 20:
        description = f"{title}. {selftext[:200]}"
    
    return {
        "name": title[:100],
        "website": url,
        "description": description[:500],
        "tool_type": "web_applications",
        "category": f"Reddit - r/{subreddit}",
        "pricing": "Unknown",
        "features": f"Reddit score: {post_data.get('score', 0)}, Recent post",
        "confidence": 0.65,
        "source_data": json.dumps({
            "source": "reddit_api_incremental",
            "subreddit": subreddit,
            "score": post_data.get("score", 0),
            "created_utc": post_data.get("created_utc"),
            "incremental": True
        })
    }

# ================================================================
# ENTERPRISE LOGGING AND MONITORING
# ================================================================

def _log_incremental_performance(self, api_name: str, start_time: float, tools_found: int, tools_skipped: int):
    """Log performance metrics for incremental discovery"""
    
    processing_time = time.time() - start_time
    efficiency = (tools_skipped / max(tools_found + tools_skipped, 1)) * 100
    
    print(f"    📊 {api_name} Performance:")
    print(f"       • Processing time: {processing_time:.2f}s")
    print(f"       • Tools found: {tools_found}")
    print(f"       • Tools skipped: {tools_skipped}")
    print(f"       • Efficiency: {efficiency:.1f}% reduction")

def _validate_incremental_params(self, incremental_params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize incremental parameters"""
    
    if not incremental_params:
        return {}
    
    validated = {
        "force_full_scan": bool(incremental_params.get("force_full_scan", False)),
        "incremental_mode": bool(incremental_params.get("incremental_mode", True)),
        "last_check_times": {}
    }
    
    # Validate last check times
    last_check_times = incremental_params.get("last_check_times", {})
    if isinstance(last_check_times, dict):
        for api_name, timestamp in last_check_times.items():
            try:
                # Validate timestamp format
                datetime.fromisoformat(timestamp)
                validated["last_check_times"][api_name] = timestamp
            except Exception:
                # Skip invalid timestamps
                continue
    
    return validated