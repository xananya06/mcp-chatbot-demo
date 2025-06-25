from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.api.auth import auth
import json
import re
from typing import List, Optional

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
    If conversation_id is provided, it adds to existing conversation.
    If not, it creates a new conversation.
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


# AI Tools Discovery Endpoints


@router.post("/discover-tools")
def discover_ai_tools(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Discover AI tools using the new focused discovery system"""
    from app.services.chat_service import discover_tools
    
    # Extract focus from request data
    focus = request_data.get("focus", "all")
    
    # Create a simple request object
    class FocusRequest:
        def __init__(self, focus):
            self.focus = focus
    
    request = FocusRequest(focus)
    result = discover_tools(request, db)
    return result
@router.get("/tools")
def get_discovered_tools(
    tool_type: Optional[str] = None,  # Filter by any tool type
    category: Optional[str] = None,   # Filter by category
    pricing: Optional[str] = None,    # Filter by pricing model
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get discovered AI tools with optional filtering"""
    from app.models.chat import DiscoveredTool
    
    query = db.query(DiscoveredTool)
    
    # Apply filters
    if tool_type:
        query = query.filter(DiscoveredTool.tool_type == tool_type.lower())
    if category:
        query = query.filter(DiscoveredTool.category.ilike(f"%{category}%"))
    if pricing:
        query = query.filter(DiscoveredTool.pricing.ilike(f"%{pricing}%"))
    
    tools = query.order_by(
        DiscoveredTool.confidence_score.desc(),
        DiscoveredTool.created_at.desc()
    ).limit(limit).all()
    
    return {
        "tools": [
            {
                "id": tool.id,
                "name": tool.name,
                "website": tool.website,
                "description": tool.description,
                "tool_type": tool.tool_type,
                "category": tool.category,
                "pricing": tool.pricing,
                "features": tool.features,
                "confidence_score": tool.confidence_score,
                "created_at": tool.created_at
            }
            for tool in tools
        ],
        "count": len(tools),
        "filters": {
            "tool_type": tool_type,
            "category": category, 
            "pricing": pricing
        }
    }


@router.get("/tools/categories")
def get_tool_categories(
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get all available tool categories for discovery"""
    categories = {
        "desktop_applications": "Desktop software and applications",
        "browser_extensions": "Browser extensions and add-ons", 
        "mobile_apps": "Mobile applications for iOS and Android",
        "web_applications": "Web-based tools and SaaS platforms",
        "ai_services": "APIs and cloud AI services",
        "code_editors": "AI-powered IDEs and code editors",
        "plugins": "IDE plugins and editor extensions",
        "creative_tools": "AI tools for art, music, video creation",
        "business_tools": "CRM, marketing, and enterprise tools",
        "productivity_tools": "Task management and productivity apps"
    }
    
    return {
        "categories": categories,
        "total_categories": len(categories),
        "usage": "Use any category name as the 'focus' parameter in /discover-tools"
    }


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
        "by_pricing": {stat.pricing: stat.count for stat in pricing_stats}
    }
