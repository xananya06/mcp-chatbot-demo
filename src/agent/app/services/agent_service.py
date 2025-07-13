# src/agent/app/services/agent_service.py - Updated with Unified Activity System
import os
import sys
import asyncio
import threading
import time

from opentelemetry import trace

from mcp.types import PromptMessage, TextContent
from mcp_agent.core.fastagent import FastAgent
from mcp_agent.core.request_params import RequestParams
from mcp_agent.mcp.prompt_message_multipart import PromptMessageMultipart
from mcp_agent.mcp.helpers.content_helpers import get_text
from mcp_agent.logging.logger import get_logger

class AgentService:
    """Agentic Service for handling asynchronous agent requests."""
    def __init__(self, config: str | None = None) -> None:

        # Process Configurations
        self.config = config or os.environ.get("AGENT_CONFIG_PATH")
        # Handle YAML configuration if provided
        yconfig = os.environ.get("AGENT_CONFIG_YAML")
        if yconfig:
            import tempfile
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
                print(f"Temporary file created at: {temp.name}")
                temp.write(yconfig)
                self.config = temp.name

        self.running = True
        self.history = True
        self.logger = get_logger(__name__)
        self.logger.info("Agentic Runner initializing...")

        # Initialize asyncio event loop and thread. All asyncio tasks will run in this loop.
        # This allows us to run async code in a synchronous context.
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

        self.tracer = trace.get_tracer(__name__)
        self.logger.info("Agentic Runner initialized...")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        # Schedule the main runner coroutine
        self.loop.create_task(self.runner())
        self.loop.run_forever()

    async def runner(self):
        """FIXED: Proper initialization with error handling and retry logic"""
        
        # Run this service once and process multiple requests
        self.agent = None
        self.running = True

        # FIX: Save and clear sys.argv to prevent argument parsing conflicts
        original_argv = sys.argv.copy()
        sys.argv = ['fastagent']  # Provide minimal args
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries and self.running:
            try:
                self.logger.info(f"Initializing FastAgent (attempt {retry_count + 1}/{max_retries})...")
                
                self.fast_agent = FastAgent(
                    "Acuvity Agent",
                    config_path=self.config,
                )
                
                self.logger.info("FastAgent created successfully")
                break
                
            except Exception as e:
                retry_count += 1
                self.logger.error(f"FastAgent initialization failed (attempt {retry_count}): {e}")
                
                if retry_count >= max_retries:
                    self.logger.error("Max retries reached. Agent initialization failed.")
                    return
                
                # Wait before retrying
                await asyncio.sleep(5)
            finally:
                # Restore original sys.argv
                sys.argv = original_argv

        if not hasattr(self, 'fast_agent'):
            self.logger.error("Failed to initialize FastAgent after all retries")
            return

        # Get server keys with error handling
        server_keys = {}
        try:
            mcp_config = self.fast_agent.config.get("mcp", {})
            servers_config = mcp_config.get("servers", {})
            server_keys = servers_config.keys()
            self.logger.info(f"Found {len(server_keys)} MCP servers: {list(server_keys)}")
        except Exception as e:
            self.logger.error(f"Error getting server keys: {e}")
            server_keys = {}

        try:
            @self.fast_agent.agent(
                name="acuvity",
                instruction="""You are an AI assistant with access to specialized tools AND a comprehensive database of 25,000+ AI tools with unified activity scoring.

IMPORTANT RULES:
1. Always think step-by-step before using tools
2. Explain what you're doing: "I'll search for..." or "Let me query..."
3. Prioritize high-activity tools and show quality transparency
4. After getting results, summarize key findings with activity scores
5. Mention when tools have recent activity issues

AVAILABLE TOOLS:
- Use brave_search for current information and real-time data
- Use fetch for reading specific web pages
- Use sequential_thinking for complex problems requiring multiple steps
- Use memory to remember important context from our conversation
- Use postgres_query to search the enhanced tools database directly

DATABASE ACCESS - UNIFIED ACTIVITY SCORING:
You now have direct access to a quality-enhanced discovered_tools database with 25,000+ AI tools using unified activity assessment.

**When users ask about tools, software, or applications:**

1. **Search Database First with Activity Filters** (25K+ activity-tracked tools):
   - Use postgres_query to search the discovered_tools table
   - PRIORITIZE high-activity tools (activity_score >= 0.7)
   - Check tool type and source-specific metrics
   - Example SQL: 
   ```sql
   SELECT name, website, description, tool_type_detected, activity_score, 
          github_stars, npm_weekly_downloads, last_activity_check,
          is_actively_maintained
   FROM discovered_tools 
   WHERE (name ILIKE '%React%' OR description ILIKE '%React%') 
   AND activity_score >= 0.7
   ORDER BY activity_score DESC, github_stars DESC NULLS LAST 
   LIMIT 10;
   ```

2. **Enhanced Database Schema** (discovered_tools table):
   - activity_score: Unified quality score (0.0-1.0) - **PRIORITIZE >= 0.7**
   - tool_type_detected: Actual tool type (github_repo, npm_package, web_application, etc.)
   - github_stars: Star count for GitHub repositories
   - npm_weekly_downloads: Weekly download count for NPM packages
   - pypi_last_release: Last release date for Python packages
   - website_status: HTTP status for web applications
   - last_activity_check: When we last verified the tool works
   - is_actively_maintained: Boolean indicating active development/maintenance

3. **Tool Type Specific Queries**:
   ```sql
   -- For GitHub repositories (prioritize by stars and activity)
   SELECT name, website, github_stars, github_last_commit, activity_score
   FROM discovered_tools 
   WHERE tool_type_detected = 'github_repo' 
   AND activity_score >= 0.7
   ORDER BY github_stars DESC, activity_score DESC;

   -- For NPM packages (prioritize by downloads and activity)
   SELECT name, website, npm_weekly_downloads, npm_last_version, activity_score
   FROM discovered_tools 
   WHERE tool_type_detected = 'npm_package'
   AND npm_weekly_downloads > 1000
   ORDER BY npm_weekly_downloads DESC;

   -- For Python packages
   SELECT name, website, pypi_last_release, activity_score
   FROM discovered_tools 
   WHERE tool_type_detected = 'pypi_package'
   AND activity_score >= 0.6
   ORDER BY activity_score DESC;

   -- For web applications
   SELECT name, website, website_status, activity_score, last_activity_check
   FROM discovered_tools 
   WHERE tool_type_detected = 'web_application'
   AND website_status = 200
   ORDER BY activity_score DESC;
   ```

4. **Quality Transparency (Enhanced):**
   - Show activity scores: "This tool has an activity score of 0.9/1.0"
   - Mention tool type: "GitHub repository with 15K stars" or "NPM package with 50K weekly downloads"
   - Activity indicators: "Actively maintained (last commit 2 days ago)" or "High usage (100K downloads/week)"
   - Cross-platform tools: "Available as both GitHub repo and NPM package"

5. **When Database Has Limited Results**:
   - If <5 high-activity results, expand to activity_score >= 0.5
   - Mention: "Found 3 high-activity tools (>0.7), expanding to include 5 more moderate-activity tools (>0.5)"
   - Always try brave_search for the latest tools if database results are insufficient
   - Explain: "Our database contains 25K+ tools but may not have the very latest releases"

6. **Response Format with Activity Info**:
   When recommending tools, ALWAYS include:
   ```
   🔧 **Tool Name** (Activity: 8.5/10, Type: GitHub Repo)
   🌐 Website: [URL]
   ⭐ GitHub: 15,000 stars, last commit 2 days ago
   📦 Package: 50K weekly downloads on NPM
   📝 Description: [What it does]
   💰 Pricing: [Pricing model]
   ✅ Status: Actively maintained, high community engagement
   ```

7. **Tool Type Detection Logic**:
   - GitHub repos: Assess by stars, commits, contributors
   - NPM packages: Assess by downloads, update frequency
   - PyPI packages: Assess by release activity, maintenance
   - Web apps: Assess by website health, SSL, performance
   - CLI tools: Usually GitHub-based, assess accordingly

RESPONSE STYLE WITH ACTIVITY FOCUS:
- Start with direct answer from high-activity database results
- Show the SQL query you used: "I searched our activity database with: [SQL]"
- Present results with activity scores and tool type indicators
- Use activity indicators: ✅ (high activity), ⚠️ (moderate), 🔄 (recently checked)
- Mention total database size and activity features
- If recommending tools, always include activity levels and tool type

EXAMPLE ENHANCED WORKFLOW:
User: "Find React frameworks"
1. Query database with activity filters:
   ```sql
   SELECT name, website, description, tool_type_detected, activity_score, github_stars
   FROM discovered_tools 
   WHERE (name ILIKE '%React%' OR description ILIKE '%React%') 
   AND activity_score >= 0.7
   ORDER BY activity_score DESC, github_stars DESC 
   LIMIT 10;
   ```
2. Present results with activity transparency:
   "Found 8 high-activity React tools (activity >= 0.7) from our database of 25,000+ activity-tracked tools"
3. Show each tool with activity score, tool type, and source-specific metrics
4. If needed, use brave_search for latest React frameworks not yet in database

DATABASE ACTIVITY FEATURES:
- ✅ 25,000+ tools with unified activity scoring
- ✅ Tool type detection (GitHub, NPM, PyPI, web apps, CLI tools)  
- ✅ Source-specific metrics (GitHub stars, NPM downloads, PyPI releases)
- ✅ Activity assessment (development activity, community engagement)
- ✅ Cross-platform awareness (same tool available on multiple platforms)
- ✅ Maintenance indicators (actively developed vs. stagnant projects)

The database is your PRIMARY source for tool recommendations. Always use activity filters and show transparency about activity scores and tool types - this gives much better quality than just "website works"!""",
                servers=server_keys,
                request_params=RequestParams(
                    use_history=True, 
                    max_iterations=10000
                ),
            )
            async def dummy():
                # This function is needed for the decorator but not used directly
                pass

            self.logger.info("Agent decorator configured successfully")

            # Start the agent with proper error handling
            async with self.fast_agent.run() as agent:
                self.logger.info("FastAgent started successfully")
                self.agent = agent
                
                # Keep the agent alive
                while self.running:
                    await asyncio.sleep(60)  # Check every minute

        except Exception as e:
            self.logger.error(f"Error in agent setup: {e}")
            return

        self.logger.warning("Agentic Runner stopped")

    async def process_message(self, message: str) -> str:
        """Asynchronous send method to process messages."""

        if not self.agent:
            self.logger.debug("Agent is not initialized.")
            return "error: agent not initialized"

        self.logger.info(
            f"running agentic runner with span-context: {trace.get_current_span().get_span_context()} {message}"
        )

        try:
            prompts = PromptMessageMultipart.to_multipart(
                [
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=message),
                    ),
                ]
            )
            
            # Standard timeout for database queries
            response = await asyncio.wait_for(
                self.agent.acuvity.generate(
                    multipart_messages=prompts,
                    request_params=RequestParams(use_history=self.history, max_iterations=10000),
                ),
                timeout=120  # 2 minute timeout for database queries
            )

            # Use history until explicitly cleared
            self.history = True

            # Format the response
            response_text = "Sorry, I couldn't find any information on that."
            for content in response.content:
                response_text = get_text(content)
            return response_text
            
        except asyncio.TimeoutError:
            return "error: Request timed out. Please try a simpler query or try again later."
        except Exception as e:
            # Handle errors - could put them on the output queue too
            response = f"error: {e}, original_message: {message}"
            self.logger.error(f"Error processing message: {e}")
        return response

    def send(self, message, block=True, timeout=None) -> str:
        """Send a message in the background loop"""
        if not self.thread.is_alive():
            return "error: agent service thread is not running"
            
        try:
            fut = asyncio.run_coroutine_threadsafe(self.process_message(message), self.loop)
            return fut.result(timeout=timeout) if block else None
        except Exception as e:
            return f"error: failed to send message: {e}"

    def clear(self) -> str:
        """Clear the agentic history in the same loop"""
        self.logger.info("history clearing...")
        self.history = False
        return "clear"

    def is_ready(self) -> bool:
        """Check if agent is ready to process messages"""
        return self.agent is not None and self.thread.is_alive()

agent_service = AgentService()