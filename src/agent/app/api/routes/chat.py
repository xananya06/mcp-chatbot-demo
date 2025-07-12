# src/agent/app/api/routes/chat.py - Updated for PostgreSQL MCP Integration

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
    Agent now has direct database access through PostgreSQL MCP server.
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
# TOOL DISCOVERY ENDPOINTS (Keep existing functionality)
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
        
    elif discovery_type == "ai_category":
        category = request_data.get("category", "all")
        from app.services.chat_service import discover_tools
        result = discover_tools(category, db)
        
    elif discovery_type == "turbo":
        from app.services.discovery_pipeline import discovery_pipeline
        result = discovery_pipeline.run_turbo_discovery(target_tools)
        
    elif discovery_type == "intensive":
        from app.services.discovery_pipeline import discovery_pipeline
        result = discovery_pipeline.run_intensive_discovery(target_tools)
        
    elif discovery_type == "all":
        from app.services.real_apis_service import unified_apis_service
        result = unified_apis_service.run_sync_discover_all_real_apis(target_tools)
        
    else:
        return {"error": f"Unknown discovery type: {discovery_type}"}
    
    return {
        "success": True,
        "discovery_type": discovery_type,
        "result": result,
        "note": "Discovery runs independently - agent accesses database through PostgreSQL MCP"
    }


@router.get("/system-status")
def get_system_status(
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get system and integration status"""
    
    return {
        "database_integration": "✅ PostgreSQL MCP Server",
        "agent_access": "✅ Direct database queries via MCP",
        "discovery_apis": {
            "github": "✅ Ready",
            "hackernews": "✅ Ready", 
            "npm": "✅ Ready",
            "pypi": "✅ Ready",
            "stackoverflow": "✅ Ready",
            "vscode": "✅ Ready"
        },
        "discovery_methods": [
            "admin/discover-tools (API)",
            "standalone_discovery_service.py (CLI)",
            "chat interface (agent auto-queries database)"
        ],
        "architecture": "Agent → PostgreSQL MCP → Database",
        "usage": {
            "chat": "Ask agent about tools - queries database automatically",
            "api": "POST /admin/discover-tools with type and target_tools",
            "cli": "python standalone_discovery_service.py [command]"
        }
    }


# ================================================================
# DATABASE STATISTICS (Keep for monitoring)  
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
        "note": "Agent now accesses database directly through PostgreSQL MCP server!"
    }


@router.get("/database-status")
def get_database_status(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get database and system status"""
    from app.models.chat import DiscoveredTool
    from sqlalchemy import func
    
    try:
        # Get database statistics
        total_tools = db.query(func.count(DiscoveredTool.id)).scalar()
        
        # Count by source
        github_count = db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.source_data.like('%github%')
        ).scalar() or 0
        
        npm_count = db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.source_data.like('%npm%')
        ).scalar() or 0
        
        return {
            "database_integration": "direct_postgresql_mcp",
            "total_tools": total_tools,
            "github_tools": github_count,
            "npm_packages": npm_count,
            "agent_access": "✅ Agent can query database directly",
            "discovery_service": "✅ Standalone service available",
            "architecture": "Agent → PostgreSQL MCP Server → Database",
            "usage": "Ask agent about tools - it will query database automatically",
            "discovery_command": "Use standalone_discovery_service.py for tool discovery"
        }
    except Exception as e:
        return {
            "error": f"Database connection failed: {str(e)}",
            "status": "❌ Database not accessible"
        }