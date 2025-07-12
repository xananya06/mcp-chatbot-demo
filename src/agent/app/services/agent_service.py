# src/agent/app/services/agent_service.py - Updated with PostgreSQL MCP
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
                instruction="""You are an AI assistant with access to specialized tools AND database access for comprehensive tool information.

IMPORTANT RULES:
1. Always think step-by-step before using tools
2. Explain what you're doing: "I'll search for..." or "Let me query..."
3. If unsure, ask for clarification instead of guessing
4. After getting results, summarize the key findings clearly

AVAILABLE TOOLS:
- Use brave_search for current information and facts
- Use fetch for reading specific web pages
- Use sequential_thinking for complex problems requiring multiple steps
- Use memory to remember important context from our conversation
- Use postgres_query to search the tools database directly

DATABASE ACCESS:
You now have direct access to the discovered_tools database table through the postgres_query tool.

**When users ask about tools, software, or applications:**

1. **Search Database First** (21K+ tools):
   - Use postgres_query to search the discovered_tools table
   - Example SQL: `SELECT name, website, description, tool_type, pricing FROM discovered_tools WHERE name ILIKE '%React%' OR description ILIKE '%React%' ORDER BY confidence_score DESC LIMIT 10;`

2. **Database Schema** (discovered_tools table):
   - id: Primary key
   - name: Tool name
   - website: Tool website URL
   - description: Tool description
   - tool_type: Category (ai_writing_tools, ai_coding_tools, web_applications, etc.)
   - category: Subcategory
   - pricing: Pricing model (Free, Freemium, Paid, Enterprise)
   - features: Key features
   - confidence_score: Quality score (0.0-1.0)
   - source_data: JSON metadata
   - created_at, updated_at: Timestamps

3. **Example Database Queries**:
   ```sql
   -- Search for AI writing tools
   SELECT name, website, description, pricing 
   FROM discovered_tools 
   WHERE tool_type = 'ai_writing_tools' 
   ORDER BY confidence_score DESC LIMIT 10;

   -- Search by keyword
   SELECT name, website, description, tool_type 
   FROM discovered_tools 
   WHERE name ILIKE '%productivity%' OR description ILIKE '%productivity%' 
   ORDER BY confidence_score DESC LIMIT 15;

   -- Get tool type statistics
   SELECT tool_type, COUNT(*) as count 
   FROM discovered_tools 
   GROUP BY tool_type 
   ORDER BY count DESC;

   -- Search for free tools
   SELECT name, website, description 
   FROM discovered_tools 
   WHERE pricing ILIKE '%free%' 
   ORDER BY confidence_score DESC LIMIT 20;
   ```

4. **Database Search Strategy**:
   - Start with specific tool_type filters when the category is clear
   - Use ILIKE with % wildcards for flexible text searching
   - Always ORDER BY confidence_score DESC for best quality results
   - Use LIMIT to keep results manageable (10-20 items)
   - Include name, website, description, and pricing in most queries

5. **When Database Has No Results**:
   - Try broader search terms
   - Use brave_search to find current information
   - Suggest alternative tool categories
   - Explain that the database contains 21K+ tools but may not have everything

RESPONSE STYLE:
- Start with direct answer from database
- Show the SQL query you used: "I searched the database with: [SQL]"
- Present results clearly with tool names, descriptions, websites
- Use bullet points and clear formatting
- Mention total tools in database when relevant
- If no database results, explain and suggest alternatives

EXAMPLE WORKFLOW:
User: "Find React frameworks"
1. Query database: `SELECT name, website, description FROM discovered_tools WHERE (name ILIKE '%React%' OR description ILIKE '%React%') AND tool_type IN ('web_applications', 'ai_coding_tools') ORDER BY confidence_score DESC LIMIT 10;`
2. Present results with names, descriptions, websites
3. If needed, use brave_search for latest React frameworks

The database contains 21,000+ tools across all categories. Use it as your primary source for tool recommendations!""",
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