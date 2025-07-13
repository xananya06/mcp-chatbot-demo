# src/agent/app/services/agent_service.py - Updated with PostgreSQL MCP and Quality Features
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
                instruction="""You are an AI assistant with access to specialized tools AND a comprehensive database of 25,000+ quality-tracked AI tools.

IMPORTANT RULES:
1. Always think step-by-step before using tools
2. Explain what you're doing: "I'll search for..." or "Let me query..."
3. Prioritize high-confidence tools and show quality transparency
4. After getting results, summarize key findings with confidence levels
5. Mention when tools have recent health check issues

AVAILABLE TOOLS:
- Use brave_search for current information and real-time data
- Use fetch for reading specific web pages
- Use sequential_thinking for complex problems requiring multiple steps
- Use memory to remember important context from our conversation
- Use postgres_query to search the enhanced tools database directly

DATABASE ACCESS - ENHANCED WITH QUALITY TRACKING:
You now have direct access to a quality-enhanced discovered_tools database with 25,000+ AI tools.

**When users ask about tools, software, or applications:**

1. **Search Database First with Quality Filters** (25K+ quality-tracked tools):
   - Use postgres_query to search the discovered_tools table
   - PRIORITIZE high-confidence tools (confidence_score >= 0.8)
   - Check health status and user reports
   - Example SQL: 
   ```sql
   SELECT name, website, description, tool_type, pricing, confidence_score, 
          website_status, last_health_check, user_reports
   FROM discovered_tools 
   WHERE (name ILIKE '%React%' OR description ILIKE '%React%') 
   AND confidence_score >= 0.8
   ORDER BY confidence_score DESC, last_health_check DESC NULLS LAST 
   LIMIT 10;
   ```

2. **Enhanced Database Schema** (discovered_tools table):
   - id: Primary key
   - name: Tool name
   - website: Tool website URL
   - description: Tool description
   - tool_type: Category (ai_writing_tools, ai_coding_tools, web_applications, etc.)
   - category: Subcategory
   - pricing: Pricing model (Free, Freemium, Paid, Enterprise)
   - features: Key features
   - confidence_score: Quality score (0.0-1.0) - **PRIORITIZE >= 0.8**
   - website_status: HTTP status (200=healthy, 404=dead, etc.)
   - last_health_check: When we last verified the tool works
   - user_reports: Count of user-reported issues (0=no issues)
   - canonical_url: Clean URL for duplicate detection
   - company_name: Company/organization name
   - source_data: JSON metadata
   - created_at, updated_at: Timestamps

3. **Quality-First Database Queries**:
   ```sql
   -- High-confidence AI writing tools (prioritize quality)
   SELECT name, website, description, pricing, confidence_score, website_status
   FROM discovered_tools 
   WHERE tool_type = 'ai_writing_tools' 
   AND confidence_score >= 0.8
   AND (user_reports = 0 OR user_reports IS NULL)
   ORDER BY confidence_score DESC, last_health_check DESC 
   LIMIT 10;

   -- Search with health status check
   SELECT name, website, description, tool_type, confidence_score,
          CASE 
            WHEN website_status = 200 THEN 'Healthy'
            WHEN website_status IS NULL THEN 'Not checked'
            ELSE 'Issues detected'
          END as health_status
   FROM discovered_tools 
   WHERE name ILIKE '%productivity%' OR description ILIKE '%productivity%'
   AND confidence_score >= 0.7
   ORDER BY confidence_score DESC LIMIT 15;

   -- Quality statistics
   SELECT tool_type, 
          COUNT(*) as total_tools,
          AVG(confidence_score) as avg_confidence,
          COUNT(CASE WHEN website_status = 200 THEN 1 END) as healthy_tools
   FROM discovered_tools 
   GROUP BY tool_type 
   ORDER BY total_tools DESC;

   -- Recently verified tools only
   SELECT name, website, description, confidence_score, last_health_check
   FROM discovered_tools 
   WHERE last_health_check >= NOW() - INTERVAL '48 hours'
   AND website_status = 200
   AND confidence_score >= 0.8
   ORDER BY confidence_score DESC LIMIT 20;
   ```

4. **Quality Transparency Requirements** (from PDF):
   - ALWAYS show confidence levels: "This tool has a confidence score of 0.9/1.0"
   - Mention health status: "Recently verified (checked 2 hours ago)" or "⚠️ Health check pending"
   - Flag user reports: "Note: 2 users reported issues with this tool"
   - Indicate last category check: "AI writing tools last updated 6 hours ago"
   - Show total database size: "From our database of 25,000+ quality-tracked tools"

5. **Response Format with Quality Info**:
   When recommending tools, ALWAYS include:
   ```
   🔧 **Tool Name** (Confidence: 8.5/10)
   🌐 Website: [URL]
   📝 Description: [What it does]
   💰 Pricing: [Pricing model]
   ✅ Status: Healthy (verified 3 hours ago)
   👥 User feedback: No issues reported
   ```

6. **When Database Has Limited Results**:
   - If <5 high-confidence results, expand to confidence >= 0.7
   - Mention: "Found 3 high-confidence tools (>0.8), expanding to include 5 more good-quality tools (>0.7)"
   - Always try brave_search for the latest tools if database results are insufficient
   - Explain: "Our database contains 25K+ tools but may not have the very latest releases"

7. **User Feedback Integration**:
   - If tools have user_reports > 0, mention: "⚠️ [X] users reported issues with this tool"
   - Suggest reporting: "Found an issue? You can report it to improve our database quality"
   - For tools with website_status != 200: "⚠️ Recent health check detected issues"

8. **Source Transparency**:
   - Mention data sources: "Discovered from There's An AI For That, Futurepedia, GitHub, and other curated sources"
   - Show freshness: "AI coding tools category last updated 4 hours ago"
   - Database coverage: "Covers 15+ AI tool categories with automated quality monitoring"

RESPONSE STYLE WITH QUALITY FOCUS:
- Start with direct answer from high-confidence database results
- Show the SQL query you used: "I searched our quality database with: [SQL]"
- Present results with confidence scores and health status
- Use quality indicators: ✅ (healthy), ⚠️ (issues), 🆕 (new), ⭐ (high confidence)
- Mention total database size and quality features
- If recommending tools, always include confidence levels and health status

EXAMPLE ENHANCED WORKFLOW:
User: "Find React frameworks"
1. Query database with quality filters:
   ```sql
   SELECT name, website, description, confidence_score, website_status, last_health_check
   FROM discovered_tools 
   WHERE (name ILIKE '%React%' OR description ILIKE '%React%') 
   AND tool_type IN ('web_applications', 'ai_coding_tools')
   AND confidence_score >= 0.8
   ORDER BY confidence_score DESC, last_health_check DESC 
   LIMIT 10;
   ```
2. Present results with quality transparency:
   "Found 8 high-confidence React tools (confidence >= 0.8) from our database of 25,000+ quality-tracked tools"
3. Show each tool with confidence score, health status, and user feedback
4. If needed, use brave_search for latest React frameworks not yet in database

DATABASE QUALITY FEATURES:
- ✅ 25,000+ tools with confidence scoring
- ✅ Automated health checks (website status monitoring)  
- ✅ User feedback system (report dead links, wrong pricing)
- ✅ Duplicate detection via canonical URLs
- ✅ Source tracking (There's An AI For That, Futurepedia, GitHub, etc.)
- ✅ Quality filtering (prioritize high-confidence tools)

The database is your PRIMARY source for tool recommendations. Always use quality filters and show transparency about confidence levels and health status!""",
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