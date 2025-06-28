from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.api.auth import auth
import json
import re
from typing import List, Optional
import time
from datetime import datetime

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
    
    # Call discover_tools with just the focus string
    result = discover_tools(focus, db)
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


# REPLACE the existing @router.get("/tools/categories") endpoint in your chat.py with this:

@router.get("/tools/categories")
def get_tool_categories(
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get all available tool categories for discovery - ENHANCED VERSION"""
    
    # Enhanced categories with descriptions
    categories = {
        # New AI-specific categories
        "ai_writing_tools": "AI writing assistants and content creation tools",
        "ai_image_generation": "AI image and art generation tools", 
        "ai_video_tools": "AI video creation and editing tools",
        "ai_audio_tools": "AI audio and music generation tools",
        "ai_coding_tools": "AI coding assistants and development tools",
        "ai_data_analysis": "AI data analysis and visualization tools",
        "ai_marketing_tools": "AI marketing and advertising tools",
        "ai_customer_service": "AI customer support and chatbot tools",
        "ai_hr_tools": "AI human resources and recruitment tools",
        "ai_finance_tools": "AI finance and trading tools",
        "ai_education_tools": "AI education and learning tools",
        "ai_research_tools": "AI research and academic tools",
        "ai_3d_modeling": "AI 3D modeling and design tools",
        "ai_gaming_tools": "AI gaming and entertainment tools",
        
        # Keep existing categories
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
        "new_categories": [
            "ai_writing_tools", "ai_image_generation", "ai_video_tools", "ai_audio_tools",
            "ai_coding_tools", "ai_data_analysis", "ai_marketing_tools", "ai_customer_service",
            "ai_hr_tools", "ai_finance_tools", "ai_education_tools", "ai_research_tools",
            "ai_3d_modeling", "ai_gaming_tools"
        ],
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

@router.post("/pipeline/intensive")
def run_intensive_pipeline(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Run intensive discovery pipeline for rapid scaling"""
    
    target_tools = request_data.get("target_tools", 300)
    
    # Import and run the pipeline
    from app.services.discovery_pipeline import discovery_pipeline
    
    print(f"🚀 Starting intensive discovery pipeline...")
    results = discovery_pipeline.run_intensive_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"Intensive pipeline completed: {results['total_saved']} new tools discovered",
        "pipeline_results": results
    }
@router.post("/discover-tools/batch")
def batch_discover_tools(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Fast batch discovery across multiple categories"""
    
    categories = request_data.get("categories", [
        "ai_marketing_tools", "ai_hr_tools", "ai_finance_tools"
    ])
    delay_seconds = request_data.get("delay_seconds", 3)
    
    results = {
        "batch_id": f"batch_{int(time.time())}",
        "total_saved": 0,
        "total_updated": 0,
        "categories_processed": 0,
        "category_results": []
    }
    
    print(f"🔄 Fast batch starting for {len(categories)} categories...")
    
    for i, category in enumerate(categories):
        print(f"Processing {i+1}/{len(categories)}: {category}")
        
        try:
            from app.services.chat_service import discover_tools
            result = discover_tools(category, db)
            
            if result.get("success"):
                saved = result.get("database_result", {}).get("saved", 0)
                updated = result.get("database_result", {}).get("updated", 0)
                
                results["total_saved"] += saved
                results["total_updated"] += updated
                results["categories_processed"] += 1
                
                print(f"  ✅ {category}: {saved} saved, {updated} updated")
                
                results["category_results"].append({
                    "category": category,
                    "tools_saved": saved,
                    "tools_updated": updated
                })
            else:
                print(f"  ❌ {category}: {result.get('error', 'Failed')}")
            
            if i < len(categories) - 1:
                time.sleep(delay_seconds)
                
        except Exception as e:
            print(f"  💥 {category}: {str(e)}")
    
    return {
        "success": True,
        "message": f"Batch completed: {results['total_saved']} new tools",
        "results": results
    }
@router.post("/pipeline/mega")
def run_mega_pipeline(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Run mega scaling pipeline for 1000s of tools"""
    
    target = request_data.get("target_tools", 2000)
    
    from app.services.discovery_pipeline import discovery_pipeline
    
    print(f"🚀 Starting mega scaling pipeline...")
    results = discovery_pipeline.run_mega_scaling_pipeline(target)
    
    return {
        "success": True,
        "message": f"Mega pipeline completed: {results['total_saved']} tools added",
        "results": results
    }

@router.post("/pipeline/turbo")
def run_turbo_pipeline(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Turbo discovery pipeline with parallel processing"""
    
    target_tools = request_data.get("target_tools", 2000)
    
    from app.services.discovery_pipeline import discovery_pipeline
    
    print(f"🚀 Starting turbo discovery pipeline...")
    results = discovery_pipeline.run_turbo_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"Turbo pipeline completed: {results['total_saved']} new tools discovered in {results.get('total_processing_time', 0):.1f}s",
        "results": results
    }

@router.post("/pipeline/external")
def run_external_integration(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """External data integration pipeline for rapid tool discovery"""
    
    target_tools = request_data.get("target_tools", 1500)
    
    from app.services.external_data_service import external_data_service
    
    print(f"🌐 Starting external data integration...")
    results = external_data_service.integrate_external_sources(target_tools)
    
    return {
        "success": True,
        "message": f"External integration completed: {results['total_saved']} tools added in {len(results['sources_processed'])} sources",
        "results": results
    }