import os
import sys
import asyncio
import threading

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

        # Run this service once and process multiple requests
        self.agent = None
        self.running = True

        # FIX: Save and clear sys.argv to prevent argument parsing conflicts
        original_argv = sys.argv.copy()
        sys.argv = ['fastagent']  # Provide minimal args
        
        try:
            self.fast_agent = FastAgent(
                "Acuvity Agent",
                config_path=self.config,
            )
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

        server_keys = {}
        try:
            server_keys = self.fast_agent.config.get("mcp").get("servers").keys()
        except Exception as e:
            self.logger.error(f"Error getting server keys: {e}")

        @self.fast_agent.agent(
            name="acuvity",
            instruction="""You are an AI assistant with access to specialized tools AND comprehensive tool discovery capabilities.

IMPORTANT RULES:
1. Always think step-by-step before using tools
2. Explain what you're doing: "I'll search for..." or "Let me discover..."
3. If unsure, ask for clarification instead of guessing
4. After getting results, summarize the key findings clearly

STANDARD TOOLS:
- Use brave_search for current information and facts
- Use fetch for reading specific web pages
- Use sequential_thinking for complex problems requiring multiple steps
- Use memory to remember important context from our conversation
- Use github for exploring code repositories

TOOL DISCOVERY CAPABILITIES:
You have access to a comprehensive tool discovery system with 21,000+ tools and real-time discovery from 8 APIs.

**When users ask about tools, software, or applications:**

1. **Search Existing Database First** (21K+ tools):
   - Use search_discovered_tools for instant results
   - Example: "Find React tools" → search_discovered_tools(query="React", limit=10)

2. **Discover New Tools** when needed:
   - discover_github_tools: Open source repositories from GitHub API
   - discover_npm_packages: JavaScript/Node.js packages from NPM API  
   - discover_python_packages: Python packages from PyPI API
   - discover_hackernews_tools: Trending community-curated tools
   - discover_ai_tools_by_category: AI-powered intelligent categorization

3. **Get System Status**:
   - get_tool_discovery_status: Check database stats and API availability

DISCOVERY WORKFLOW:
1. **User asks about specific tools** → search_discovered_tools first
2. **No results or need more current tools** → use appropriate discovery tool
3. **For AI tools** → use discover_ai_tools_by_category
4. **For trending tools** → use discover_hackernews_tools  
5. **For development tools** → use discover_github_tools or discover_npm_packages

TOOL DISCOVERY EXAMPLES:

**AI Tools:**
- "Find AI writing tools" → discover_ai_tools_by_category(category="ai_writing_tools")
- "AI image generators?" → discover_ai_tools_by_category(category="ai_image_generation")

**Development Tools:**
- "React frameworks?" → search_discovered_tools("React") + discover_npm_packages()
- "Python ML libraries?" → search_discovered_tools("machine learning Python") + discover_python_packages()
- "What's trending in development?" → discover_hackernews_tools() + discover_github_tools()

**General Tools:**
- "Project management tools?" → search_discovered_tools("project management")
- "Design tools?" → search_discovered_tools("design") + discover_ai_tools_by_category("creative_tools")

RESPONSE STYLE:
- Start with direct answer
- Show discovery process: "Let me search our database and discover current tools..."
- Present results clearly with tool names, descriptions, websites
- Use bullet points and clear formatting
- Suggest related categories or follow-up searches
- Always mention if tools are from database vs. newly discovered

SMART COMBINATIONS:
- Combine database search + new discovery for comprehensive results
- Use multiple discovery methods for thorough coverage
- Prioritize by relevance and quality (Hacker News = highest quality)

IMPORTANT: You have access to both historical tools (21K+ database) AND real-time discovery. Use both to provide the most comprehensive and current recommendations!""",
            servers=server_keys,
            request_params=RequestParams(
                use_history=True, 
                max_iterations=10000
            ),
        )
        async def dummy(self):
            # This function is needed for the decorator but not used directly
            pass

        async with self.fast_agent.run() as agent:
            self.agent = agent
            while self.running:
                await asyncio.sleep(3600)  # Keep alive

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
            response = await self.agent.acuvity.generate(
                multipart_messages=prompts,
                request_params=RequestParams(use_history=self.history, max_iterations=10000),
            )

            # Use history until explicitly cleared
            self.history = True

            # Format the response
            response_text = "Sorry, I couldn't find any information on that."
            for content in response.content:
                response_text = get_text(content)
            return response_text
        except Exception as e:
            # Handle errors - could put them on the output queue too
            response = f"error: {e}, original_message: {message}"
        return response

    def send(self, message, block=True, timeout=None) -> str:
        """Send a message in the background loop"""
        fut = asyncio.run_coroutine_threadsafe(self.process_message(message), self.loop)
        return fut.result(timeout=timeout) if block else None

    def clear(self) -> str:
        """Clear the agentic history in the same loop"""
        self.logger.info("history clearing...")
        self.history = False
        return "clear"

agent_service = AgentService()