#!/usr/bin/env python3
"""
Tool Discovery MCP Server - SSE Transport Implementation
Implements MCP over Server-Sent Events for reliable communication
"""

import asyncio
import json
import os
import sys
import uuid
import logging
from typing import Dict, Any, List
from datetime import datetime
import concurrent.futures

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from app.services.real_apis_service import unified_apis_service
    from app.services.chat_service import discover_tools
    from app.db.database import SessionLocal
    from app.models.chat import DiscoveredTool
    from sqlalchemy import or_, func
    print("✅ Successfully imported app modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """FastAPI SSE-based MCP server for tool discovery"""
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    app = FastAPI(
        title="Tool Discovery MCP Server (SSE)", 
        description="MCP protocol over Server-Sent Events",
        version="2.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store active connections
    active_connections = {}
    
    @app.get("/")
    def root():
        return {
            "name": "tool-discovery-mcp",
            "version": "2.0.0", 
            "protocol": "MCP over SSE",
            "status": "running",
            "capabilities": [
                "search_discovered_tools",
                "discover_github_tools", 
                "discover_hackernews_tools",
                "discover_npm_packages",
                "discover_python_packages",
                "discover_ai_tools_by_category",
                "get_tool_discovery_status",
                "discover_all_apis_quick"
            ]
        }
    
    @app.get("/health")
    def health():
        try:
            db = SessionLocal()
            try:
                total = db.query(func.count(DiscoveredTool.id)).scalar()
                return {
                    "status": "healthy",
                    "tools_in_db": total,
                    "active_connections": len(active_connections),
                    "mcp_protocol": "2024-11-05"
                }
            finally:
                db.close()
        except Exception as e:
            return {"status": "partial", "error": str(e)}
    
    @app.get("/sse")
    async def sse_endpoint(request: Request):
        """MCP over SSE endpoint - proper protocol implementation"""
        
        connection_id = str(uuid.uuid4())
        logger.info(f"🔗 New MCP SSE connection: {connection_id}")
        
        async def mcp_event_stream():
            try:
                # Store connection
                active_connections[connection_id] = {"created": datetime.utcnow()}
                
                # 1. Send MCP initialization message
                init_message = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {
                                "listChanged": True
                            },
                            "resources": {},
                            "prompts": {},
                            "logging": {}
                        },
                        "serverInfo": {
                            "name": "tool-discovery-mcp",
                            "version": "2.0.0"
                        }
                    }
                }
                yield f"event: initialize\ndata: {json.dumps(init_message)}\n\n"
                
                # 2. Send tools list
                tools_list = {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "result": {
                        "tools": [
                            {
                                "name": "search_discovered_tools",
                                "description": "Search through existing tools in database (21K+ tools)",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "Search query for tool names, descriptions, or features"
                                        },
                                        "tool_type": {
                                            "type": "string", 
                                            "description": "Filter by tool type (optional)",
                                            "enum": ["ai_writing_tools", "ai_coding_tools", "web_applications", "code_editors"]
                                        },
                                        "limit": {
                                            "type": "integer",
                                            "description": "Maximum results (default: 10, max: 50)",
                                            "default": 10,
                                            "maximum": 50
                                        }
                                    },
                                    "required": ["query"]
                                }
                            },
                            {
                                "name": "discover_github_tools",
                                "description": "Discover developer tools from GitHub repositories",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "target_tools": {
                                            "type": "integer",
                                            "description": "Number of tools to discover (default: 50, max: 200)",
                                            "default": 50,
                                            "maximum": 200
                                        }
                                    }
                                }
                            },
                            {
                                "name": "discover_hackernews_tools",
                                "description": "Discover trending tools from Hacker News (highest quality)",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "target_tools": {
                                            "type": "integer",
                                            "description": "Number of tools to discover (default: 25, max: 100)", 
                                            "default": 25,
                                            "maximum": 100
                                        }
                                    }
                                }
                            },
                            {
                                "name": "discover_npm_packages",
                                "description": "Discover JavaScript/Node.js packages from NPM",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "target_tools": {
                                            "type": "integer",
                                            "description": "Number of packages (default: 30, max: 100)",
                                            "default": 30,
                                            "maximum": 100
                                        }
                                    }
                                }
                            },
                            {
                                "name": "discover_python_packages", 
                                "description": "Discover Python packages from PyPI",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "target_tools": {
                                            "type": "integer",
                                            "description": "Number of packages (default: 25, max: 100)",
                                            "default": 25,
                                            "maximum": 100
                                        }
                                    }
                                }
                            },
                            {
                                "name": "discover_ai_tools_by_category",
                                "description": "AI-powered tool discovery by category",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "category": {
                                            "type": "string",
                                            "description": "AI tool category",
                                            "enum": [
                                                "ai_writing_tools", "ai_image_generation", "ai_video_tools",
                                                "ai_coding_tools", "ai_data_analysis", "productivity_tools", "all"
                                            ],
                                            "default": "all"
                                        }
                                    }
                                }
                            },
                            {
                                "name": "get_tool_discovery_status",
                                "description": "Get system status and database statistics",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "discover_all_apis_quick",
                                "description": "Quick discovery from multiple APIs simultaneously",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "total_target": {
                                            "type": "integer",
                                            "description": "Total tools across all APIs (default: 100, max: 500)",
                                            "default": 100,
                                            "maximum": 500
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
                yield f"event: tools/list\ndata: {json.dumps(tools_list)}\n\n"
                
                # 3. Send ready notification
                ready_message = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {
                        "serverInfo": {
                            "name": "tool-discovery-mcp",
                            "version": "2.0.0"
                        }
                    }
                }
                yield f"event: initialized\ndata: {json.dumps(ready_message)}\n\n"
                
                logger.info(f"✅ MCP SSE connection {connection_id} initialized successfully")
                
                # 4. Keep connection alive with heartbeats
                heartbeat_counter = 0
                while True:
                    heartbeat_counter += 1
                    heartbeat = {
                        "jsonrpc": "2.0",
                        "method": "notifications/heartbeat",
                        "params": {
                            "sequence": heartbeat_counter,
                            "timestamp": datetime.utcnow().isoformat(),
                            "connection_id": connection_id
                        }
                    }
                    yield f"event: heartbeat\ndata: {json.dumps(heartbeat)}\n\n"
                    await asyncio.sleep(30)  # Heartbeat every 30 seconds
                    
            except asyncio.CancelledError:
                logger.info(f"🔌 MCP SSE connection cancelled: {connection_id}")
            except Exception as e:
                logger.error(f"❌ MCP SSE connection error {connection_id}: {e}")
                error_message = {
                    "jsonrpc": "2.0",
                    "method": "notifications/error", 
                    "params": {
                        "error": str(e),
                        "connection_id": connection_id
                    }
                }
                yield f"event: error\ndata: {json.dumps(error_message)}\n\n"
            finally:
                # Clean up connection
                if connection_id in active_connections:
                    del active_connections[connection_id]
                logger.info(f"🧹 Cleaned up MCP SSE connection: {connection_id}")
        
        return StreamingResponse(
            mcp_event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive", 
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "X-Accel-Buffering": "no",
                "X-Connection-ID": connection_id
            }
        )
    
    @app.post("/call_tool")
    async def call_tool_endpoint(request: dict):
        """MCP tool calling endpoint"""
        try:
            tool_name = request.get("name")
            arguments = request.get("arguments", {})
            
            if not tool_name:
                raise HTTPException(status_code=400, detail="Missing 'name' parameter")
            
            logger.info(f"🔧 MCP Tool call: {tool_name} with args: {arguments}")
            
            # Route to handler
            result = await handle_mcp_tool_call(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ MCP Tool call failed: {str(e)}")
            return {
                "jsonrpc": "2.0", 
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    @app.get("/connections")
    def get_connections():
        """Get active connections (debug endpoint)"""
        return {
            "active_connections": len(active_connections),
            "connections": {
                conn_id: {
                    "created": info["created"].isoformat(),
                    "duration_seconds": (datetime.utcnow() - info["created"]).total_seconds()
                }
                for conn_id, info in active_connections.items()
            }
        }
    
    async def handle_mcp_tool_call(name: str, arguments: Dict[str, Any]) -> str:
        """Handle MCP tool calls with proper async execution"""
        
        # Use the same handlers as the stdio version but in async context
        if name == "search_discovered_tools":
            query = arguments.get("query", "")
            tool_type = arguments.get("tool_type")
            limit = min(arguments.get("limit", 10), 50)
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, sync_search_tools, query, tool_type, limit
                )
            return result
        
        elif name == "discover_github_tools":
            target_tools = min(arguments.get("target_tools", 50), 200)
            
            loop = asyncio.get_event_loop() 
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    unified_apis_service.run_sync_discover_github,
                    target_tools
                )
            
            saved = result.get('total_saved', 0)
            return f"🐙 **GitHub Discovery Complete**\n\n• New tools: {saved}\n• Source: GitHub API\n• Quality: ⭐⭐⭐⭐ High\n\nUse search_discovered_tools to explore results!"
        
        elif name == "discover_hackernews_tools":
            target_tools = min(arguments.get("target_tools", 25), 100)
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    unified_apis_service.run_sync_discover_hackernews,
                    target_tools
                )
            
            saved = result.get('total_saved', 0)
            return f"🔥 **Hacker News Discovery Complete**\n\n• Trending tools: {saved}\n• Quality: ⭐⭐⭐⭐⭐ Very High\n• Source: Community-curated\n\nThese are the highest quality tools!"
        
        elif name == "discover_npm_packages":
            target_tools = min(arguments.get("target_tools", 30), 100)
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    unified_apis_service.run_sync_discover_npm,
                    target_tools
                )
            
            saved = result.get('total_saved', 0)
            return f"📦 **NPM Discovery Complete**\n\n• New packages: {saved}\n• Source: NPM Registry\n• Ecosystem: JavaScript/Node.js\n\nSearch for CLI tools, frameworks, libraries!"
        
        elif name == "discover_python_packages":
            target_tools = min(arguments.get("target_tools", 25), 100)
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    unified_apis_service.run_sync_discover_pypi,
                    target_tools
                )
            
            saved = result.get('total_saved', 0)
            return f"🐍 **PyPI Discovery Complete**\n\n• Python packages: {saved}\n• Source: Official PyPI\n• Categories: Data science, web, ML\n\nSearch for pandas, django, tensorflow!"
        
        elif name == "discover_ai_tools_by_category":
            category = arguments.get("category", "all")
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, sync_ai_discovery, category
                )
            
            if result.get("success"):
                saved = result.get("database_result", {}).get("saved", 0)
                return f"🤖 **AI Discovery Complete**\n\n• Category: {category}\n• New tools: {saved}\n• Method: AI-powered categorization\n• Quality: ⭐⭐⭐⭐⭐ Curated\n\nIntelligently discovered and categorized!"
            else:
                return f"❌ AI discovery failed: {result.get('error', 'Unknown error')}"
        
        elif name == "get_tool_discovery_status":
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, sync_get_status_simple)
            return result
        
        elif name == "discover_all_apis_quick":
            total_target = min(arguments.get("total_target", 100), 500)
            
            # Quick multi-API discovery
            github_target = total_target // 3
            hn_target = total_target // 4
            npm_target = total_target // 3
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                tasks = [
                    loop.run_in_executor(executor, unified_apis_service.run_sync_discover_github, github_target),
                    loop.run_in_executor(executor, unified_apis_service.run_sync_discover_hackernews, hn_target),
                    loop.run_in_executor(executor, unified_apis_service.run_sync_discover_npm, npm_target)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                total_saved = 0
                for result in results:
                    if not isinstance(result, Exception):
                        total_saved += result.get('total_saved', 0)
                
                return f"🚀 **Multi-API Discovery Complete**\n\n• Total new tools: {total_saved}\n• APIs: GitHub, Hacker News, NPM\n• Processing: Parallel execution\n\nComprehensive tool discovery across ecosystems!"
        
        else:
            return f"❌ Unknown tool: {name}\n\nAvailable tools: search_discovered_tools, discover_github_tools, discover_hackernews_tools, discover_npm_packages, discover_python_packages, discover_ai_tools_by_category, get_tool_discovery_status, discover_all_apis_quick"
    
    # Include the sync helper functions here (same as stdio version)
    def sync_search_tools(query: str, tool_type: str, limit: int) -> str:
        """Search tools synchronously"""
        try:
            db = SessionLocal()
            try:
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
                    search_query = search_query.filter(DiscoveredTool.tool_type == tool_type)
                
                tools = search_query.order_by(
                    DiscoveredTool.confidence_score.desc()
                ).limit(limit).all()
                
                total_count = db.query(func.count(DiscoveredTool.id)).scalar()
                
                if tools:
                    result = f"🔍 Found {len(tools)} tools (from {total_count:,} total):\n\n"
                    for i, tool in enumerate(tools, 1):
                        result += f"**{i}. {tool.name}**\n"
                        result += f"   • {tool.website}\n"
                        result += f"   • {tool.description[:120]}...\n"
                        result += f"   • Type: {tool.tool_type}\n\n"
                    return result
                else:
                    return f"❌ No tools found for '{query}' in {total_count:,} tools.\n\nTry: discover_github_tools, discover_hackernews_tools"
            finally:
                db.close()
        except Exception as e:
            return f"❌ Search error: {str(e)}"
    
    def sync_ai_discovery(category: str) -> dict:
        """AI discovery synchronously"""
        db = SessionLocal()
        try:
            return discover_tools(category, db)
        finally:
            db.close()
    
    def sync_get_status_simple() -> str:
        """Simple status check"""
        try:
            db = SessionLocal()
            try:
                total = db.query(func.count(DiscoveredTool.id)).scalar()
                github_count = db.query(func.count(DiscoveredTool.id)).filter(
                    DiscoveredTool.source_data.like('%github%')
                ).scalar() or 0
                
                return f"""📊 **Tool Discovery Status**

• **Total tools:** {total:,}
• **GitHub tools:** {github_count:,}
• **System:** ✅ Operational
• **APIs:** 8+ real APIs available
• **MCP Protocol:** ✅ Active (SSE transport)

**Available APIs:**
🔥 Hacker News, 🐙 GitHub, 📦 NPM, 🐍 PyPI, 🤖 AI Discovery

All discovery results automatically saved to database!"""
            finally:
                db.close()
        except Exception as e:
            return f"❌ Status error: {str(e)}"
    
    logger.info("🚀 Starting Tool Discovery MCP Server (SSE)")
    logger.info("📡 SSE endpoint: /sse")
    logger.info("🔧 Tool calls: /call_tool")
    logger.info("💚 Health: /health")
    logger.info("🌐 CORS: Enabled for all origins")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()