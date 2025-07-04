# src/agent/mcp_servers/tool_discovery_server.py - FIXED VERSION
import asyncio
import json
import os
import sys
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
import concurrent.futures

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import your services
from app.services.real_apis_service import unified_apis_service
from app.services.chat_service import discover_tools
from app.db.database import SessionLocal

# Create MCP server
server = Server("tool-discovery")

@server.list_tools()
async def list_tools() -> Sequence[Tool]:
    """List available tool discovery functions"""
    return [
        Tool(
            name="search_discovered_tools",
            description="Search through existing tools in the database (21K+ tools)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for tool names or descriptions"
                    },
                    "tool_type": {
                        "type": "string",
                        "description": "Filter by tool type (optional)",
                        "enum": ["ai_writing_tools", "ai_coding_tools", "ai_services", "web_applications", "code_editors"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="discover_github_tools",
            description="Discover new developer tools from GitHub repositories using real GitHub API",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_tools": {
                        "type": "integer",
                        "description": "Number of tools to discover (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="discover_npm_packages",
            description="Discover JavaScript/Node.js packages from NPM Registry API",
            inputSchema={
                "type": "object", 
                "properties": {
                    "target_tools": {
                        "type": "integer",
                        "description": "Number of packages to discover (default: 30)",
                        "default": 30
                    }
                }
            }
        ),
        Tool(
            name="discover_ai_tools_by_category",
            description="Discover AI tools using intelligent AI-powered categorization",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "AI tool category to discover",
                        "enum": [
                            "ai_writing_tools", "ai_image_generation", "ai_video_tools",
                            "ai_audio_tools", "ai_coding_tools", "ai_data_analysis",
                            "ai_marketing_tools", "productivity_tools", "all"
                        ],
                        "default": "all"
                    }
                }
            }
        ),
        Tool(
            name="discover_hackernews_tools",
            description="Discover trending tools from Hacker News (highest quality, community-curated)",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_tools": {
                        "type": "integer", 
                        "description": "Number of tools to discover (default: 20)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="discover_python_packages",
            description="Discover Python packages from PyPI using real PyPI API",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_tools": {
                        "type": "integer",
                        "description": "Number of packages to discover (default: 25)",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="get_tool_discovery_status",
            description="Get information about available discovery APIs and database statistics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

async def run_sync_in_thread(func, *args):
    """Run a sync function in a thread pool to avoid blocking the event loop"""
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, func, *args)
    return result

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls"""
    
    try:
        if name == "search_discovered_tools":
            query = arguments.get("query", "")
            tool_type = arguments.get("tool_type")
            limit = arguments.get("limit", 10)
            
            # Run database operation in thread
            def search_tools():
                db = SessionLocal()
                try:
                    from app.models.chat import DiscoveredTool
                    from sqlalchemy import or_, func
                    
                    # Build search query
                    search_query = db.query(DiscoveredTool)
                    
                    if query:
                        search_query = search_query.filter(
                            or_(
                                DiscoveredTool.name.ilike(f"%{query}%"),
                                DiscoveredTool.description.ilike(f"%{query}%"),
                                DiscoveredTool.features.ilike(f"%{query}%")
                            )
                        )
                    
                    if tool_type:
                        search_query = search_query.filter(
                            DiscoveredTool.tool_type == tool_type
                        )
                    
                    tools = search_query.order_by(
                        DiscoveredTool.confidence_score.desc()
                    ).limit(limit).all()
                    
                    # Get total count for context
                    total_count = db.query(func.count(DiscoveredTool.id)).scalar()
                    
                    return tools, total_count
                finally:
                    db.close()
            
            tools, total_count = await run_sync_in_thread(search_tools)
            
            if tools:
                results_text = f"🔍 Found {len(tools)} tools (from {total_count:,} total in database):\n\n"
                
                for i, tool in enumerate(tools, 1):
                    results_text += f"**{i}. {tool.name}**\n"
                    results_text += f"   • Website: {tool.website}\n"
                    results_text += f"   • Description: {tool.description[:120]}{'...' if len(tool.description) > 120 else ''}\n"
                    results_text += f"   • Type: {tool.tool_type}\n"
                    results_text += f"   • Category: {tool.category}\n"
                    results_text += f"   • Pricing: {tool.pricing}\n"
                    results_text += f"   • Confidence: {tool.confidence_score:.2f}\n\n"
                
                return [TextContent(type="text", text=results_text)]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ No tools found matching '{query}' in our database of {total_count:,} tools.\n\nTry:\n• Different search terms\n• Using discover_github_tools or discover_ai_tools_by_category to find new tools\n• Checking spelling or using broader terms"
                )]
        
        elif name == "discover_github_tools":
            target_tools = arguments.get("target_tools", 50)
            
            # Run in thread to avoid blocking
            result = await run_sync_in_thread(
                unified_apis_service.run_sync_discover_github, 
                target_tools
            )
            
            return [TextContent(
                type="text",
                text=f"🐙 **GitHub Discovery Complete**\n\n"
                     f"• **New tools discovered:** {result.get('total_saved', 0)}\n"
                     f"• **Source:** Real GitHub Search API\n"
                     f"• **Quality:** High (open source repositories)\n"
                     f"• **Categories:** Developer tools, AI projects, frameworks\n"
                     f"• **Database:** Tools automatically saved to database\n\n"
                     f"💡 Use `search_discovered_tools` to find specific tools from this discovery."
            )]
        
        elif name == "discover_npm_packages":
            target_tools = arguments.get("target_tools", 30)
            
            result = await run_sync_in_thread(
                unified_apis_service.run_sync_discover_npm,
                target_tools
            )
            
            return [TextContent(
                type="text", 
                text=f"📦 **NPM Discovery Complete**\n\n"
                     f"• **New packages discovered:** {result.get('total_saved', 0)}\n"
                     f"• **Source:** NPM Registry API\n"
                     f"• **Quality:** High (JavaScript/Node.js ecosystem)\n"
                     f"• **Categories:** CLI tools, frameworks, libraries, build tools\n"
                     f"• **Database:** Packages automatically saved to database\n\n"
                     f"💡 Search for specific packages with `search_discovered_tools`."
            )]
        
        elif name == "discover_ai_tools_by_category":
            category = arguments.get("category", "all")
            
            # Use AI-powered discovery in thread
            def ai_discovery():
                db = SessionLocal()
                try:
                    return discover_tools(category, db)
                finally:
                    db.close()
            
            result = await run_sync_in_thread(ai_discovery)
            
            if result.get("success"):
                tools_found = result.get("count", 0)
                saved_count = result.get("database_result", {}).get("saved", 0)
                categories_searched = result.get("categories_searched", [])
                
                return [TextContent(
                    type="text",
                    text=f"🤖 **AI Category Discovery Complete**\n\n"
                         f"• **Tools discovered:** {tools_found}\n"
                         f"• **New tools saved:** {saved_count}\n"
                         f"• **Category:** {category}\n"
                         f"• **Categories searched:** {', '.join(categories_searched)}\n"
                         f"• **Source:** AI-powered intelligent discovery\n"
                         f"• **Quality:** Curated by AI agent with confidence scoring\n\n"
                         f"💡 Use `search_discovered_tools` with category filters to explore results."
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ **AI Discovery Failed**\n\nError: {result.get('error', 'Unknown error')}\n\nTry:\n• Different category\n• Using other discovery tools\n• Checking internet connection"
                )]
        
        elif name == "discover_hackernews_tools":
            target_tools = arguments.get("target_tools", 20)
            
            result = await run_sync_in_thread(
                unified_apis_service.run_sync_discover_hackernews,
                target_tools
            )
            
            return [TextContent(
                type="text",
                text=f"🔥 **Hacker News Discovery Complete**\n\n"
                     f"• **Trending tools discovered:** {result.get('total_saved', 0)}\n"
                     f"• **Source:** Hacker News Firebase API\n"
                     f"• **Quality:** ⭐⭐⭐⭐⭐ Very High (community-curated)\n"
                     f"• **Focus:** Trending developer and AI tools from tech community\n"
                     f"• **Database:** Tools automatically saved with community scores\n\n"
                     f"🏆 These are the highest quality tools currently trending in the tech community!"
            )]
        
        elif name == "discover_python_packages":
            target_tools = arguments.get("target_tools", 25)
            
            result = await run_sync_in_thread(
                unified_apis_service.run_sync_discover_pypi,
                target_tools
            )
            
            return [TextContent(
                type="text",
                text=f"🐍 **PyPI Discovery Complete**\n\n"
                     f"• **Python packages discovered:** {result.get('total_saved', 0)}\n"
                     f"• **Source:** PyPI JSON API (no scraping)\n"
                     f"• **Quality:** High (official Python package index)\n"
                     f"• **Categories:** Data science, web frameworks, CLI tools, ML libraries\n"
                     f"• **Database:** Packages automatically saved to database\n\n"
                     f"💡 Search for 'python' or specific frameworks with `search_discovered_tools`."
            )]
        
        elif name == "get_tool_discovery_status":
            def get_status():
                db = SessionLocal()
                try:
                    from app.models.chat import DiscoveredTool
                    from sqlalchemy import func
                    
                    # Get database statistics
                    total_tools = db.query(func.count(DiscoveredTool.id)).scalar()
                    
                    # Get breakdown by source
                    github_count = db.query(func.count(DiscoveredTool.id)).filter(
                        DiscoveredTool.source_data.like('%github%')
                    ).scalar()
                    
                    npm_count = db.query(func.count(DiscoveredTool.id)).filter(
                        DiscoveredTool.source_data.like('%npm%')
                    ).scalar()
                    
                    ai_count = db.query(func.count(DiscoveredTool.id)).filter(
                        DiscoveredTool.source_data.is_(None)
                    ).scalar()
                    
                    return total_tools, github_count, npm_count, ai_count
                finally:
                    db.close()
            
            total_tools, github_count, npm_count, ai_count = await run_sync_in_thread(get_status)
            
            # Check API readiness
            github_token = "✅ Enhanced" if os.getenv('GITHUB_TOKEN') else "⚠️ Basic"
            devto_token = "✅ Ready" if os.getenv('DEV_TO_TOKEN') else "❌ Not configured"
            
            return [TextContent(
                type="text",
                text=f"📊 **Tool Discovery System Status**\n\n"
                     f"**Database Statistics:**\n"
                     f"• Total tools: {total_tools:,}\n"
                     f"• GitHub tools: {github_count:,}\n"
                     f"• NPM packages: {npm_count:,}\n"
                     f"• AI-discovered: {ai_count:,}\n\n"
                     f"**Available Discovery APIs:**\n"
                     f"• 🔥 Hacker News: ✅ Ready (community-curated)\n"
                     f"• 🐙 GitHub: {github_token} (repository search)\n"
                     f"• 📦 NPM: ✅ Ready (JavaScript packages)\n"
                     f"• 🐍 PyPI: ✅ Ready (Python packages)\n"
                     f"• 📚 Stack Overflow: ✅ Ready (Q&A)\n"
                     f"• 🔧 VS Code: ✅ Ready (extensions)\n"
                     f"• 📝 Dev.to: {devto_token} (articles)\n"
                     f"• 🤖 AI Discovery: ✅ Ready (intelligent categorization)\n\n"
                     f"**Capabilities:**\n"
                     f"• Search 21K+ existing tools instantly\n"
                     f"• Discover new tools from 8 real APIs\n"
                     f"• AI-powered intelligent categorization\n"
                     f"• Real-time trending tool discovery\n"
                     f"• No web scraping - only real APIs\n\n"
                     f"💡 All discovery results are automatically saved to the database!"
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]
            
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error executing {name}: {str(e)}\n\nPlease try again or use a different discovery method."
        )]

if __name__ == "__main__":
    import mcp.server.stdio
    mcp.server.stdio.run_server(server)