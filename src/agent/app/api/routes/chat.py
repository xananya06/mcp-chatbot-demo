# src/agent/app/api/routes/chat.py - CLEANED FOR MCP APPROACH

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.api.auth import auth

# Create a router for the chat API
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """
    Process a chat message and return a response.
    Agent now has access to tool discovery through MCP server.
    """
    response = chat_service.process_chat_request(db, current_user_id, chat_request)
    return response


@router.get("/conversations")
def get_conversations(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get all conversations for the current user"""
    from app.models.chat import Conversation

    conversations = (
        db.query(Conversation).filter(Conversation.user_id == current_user_id).all()
    )

    return conversations


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get all messages for a specific conversation"""
    from app.models.chat import Conversation, Message

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id, Conversation.user_id == current_user_id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    messages = (
        db.query(Message).filter(Message.conversation_id == conversation_id).all()
    )

    return messages


# ================================================================
# TOOL DISCOVERY MANAGEMENT (Admin interface)
# ================================================================

@router.post("/admin/discover-tools")
def admin_discover_tools(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Admin endpoint to manually trigger tool discovery"""
    
    discovery_type = request_data.get("type", "github")  # github, hackernews, npm, all
    target_tools = request_data.get("target_tools", 50)
    
    if discovery_type == "github":
        from app.services.real_apis_service import unified_apis_service
        result = unified_apis_service.run_sync_discover_github(target_tools)
        
    elif discovery_type == "hackernews":
        from app.services.real_apis_service import unified_apis_service
        result = unified_apis_service.run_sync_discover_hackernews(target_tools)
        
    elif discovery_type == "npm":
        from app.services.real_apis_service import unified_apis_service
        result = unified_apis_service.run_sync_discover_npm(target_tools)
        
    elif discovery_type == "all":
        from app.services.real_apis_service import unified_apis_service
        result = unified_apis_service.run_sync_discover_all_real_apis(target_tools)
        
    else:
        return {"error": f"Unknown discovery type: {discovery_type}"}
    
    return {
        "success": True,
        "discovery_type": discovery_type,
        "result": result,
        "note": "For normal usage, use the chat interface - agent handles discovery automatically"
    }


# ================================================================
# TOOL DISCOVERY STATUS (Keep for monitoring)
# ================================================================

@router.get("/tools/stats")
def get_tools_statistics(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get statistics about discovered tools"""
    from app.models.chat import DiscoveredTool
    from sqlalchemy import func
    
    # Count by tool type
    type_stats = db.query(
        DiscoveredTool.tool_type,
        func.count(DiscoveredTool.id).label('count')
    ).group_by(DiscoveredTool.tool_type).all()
    
    # Count by pricing
    pricing_stats = db.query(
        DiscoveredTool.pricing,
        func.count(DiscoveredTool.id).label('count')
    ).group_by(DiscoveredTool.pricing).all()
    
    # Total count
    total_count = db.query(func.count(DiscoveredTool.id)).scalar()
    
    return {
        "total_tools": total_count,
        "by_type": {stat.tool_type: stat.count for stat in type_stats},
        "by_pricing": {stat.pricing: stat.count for stat in pricing_stats},
        "note": "Tool discovery is now handled through MCP server - use the chat interface!"
    }


@router.get("/mcp-status")
def get_mcp_status(
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get MCP server integration status"""
    
    return {
        "mcp_integration": "active",
        "tool_discovery_server": "mcp-server-tool-discovery:8905",
        "available_tools": [
            "search_discovered_tools - Search 21K+ database",
            "discover_github_tools - GitHub API discovery",
            "discover_hackernews_tools - Trending tools",
            "get_tool_discovery_status - System status"
        ],
        "usage": "Use the chat interface - agent automatically accesses these tools",
        "architecture": "Agent → MCP Server → Tool Discovery APIs",
        "old_api_routes": "removed - use MCP integration instead"
    }