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
import asyncio
from app.services.external_data_service import external_data_service

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

@router.post("/external/quick-boost")
def quick_external_boost(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Quick boost to add 2000-3000 tools fast"""
    
    boost_target = request_data.get("boost_target", 3000)
    
    print(f"⚡ QUICK EXTERNAL BOOST STARTED")
    print(f"🎯 Target: {boost_target} tools in under 10 minutes")
    
    # Run GitHub discovery (fastest and most reliable)
    github_result = external_data_service.run_sync_github_discovery(boost_target)
    
    return {
        "success": True,
        "message": f"Quick boost completed: {github_result['total_saved']} tools added in rapid mode",
        "results": github_result,
        "boost_mode": "github_rapid",
        "time_estimate": "5-10 minutes"
    }

@router.post("/external/massive-discovery")
def run_massive_external_discovery(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Run massive discovery from real external APIs - 10K+ tools"""
    
    target_tools = request_data.get("target_tools", 10000)
    
    print(f"🌐 Starting massive external API discovery...")
    results = external_data_service.run_sync_massive_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"Massive discovery completed: {results['total_saved']} tools added from real APIs",
        "results": results
    }

@router.post("/external/github-rapid")
def run_github_rapid_discovery(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Rapid GitHub repository discovery"""
    
    target_tools = request_data.get("target_tools", 5000)
    
    print(f"🚀 Starting rapid GitHub discovery...")
    results = external_data_service.run_sync_github_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"GitHub discovery completed: {results['total_saved']} repositories added",
        "results": results
    }

@router.get("/external/status")
def get_external_discovery_status(
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get status of external discovery capabilities"""
    
    return {
        "available_sources": {
            "github_api": {
                "description": "GitHub repository discovery via API",
                "estimated_tools": "3000-5000",
                "rate_limit": "5000 requests/hour",
                "categories": ["Open Source", "AI Tools", "Development"]
            },
            "product_hunt": {
                "description": "Product Hunt tool discovery via web scraping",
                "estimated_tools": "1000-2000", 
                "rate_limit": "Respectful scraping",
                "categories": ["Featured Tools", "AI Products", "Startup Tools"]
            },
            "ai_directories": {
                "description": "AI tool directory scraping",
                "estimated_tools": "2000-4000",
                "rate_limit": "Respectful scraping", 
                "categories": ["AI Tools", "ML Platforms", "SaaS Tools"]
            }
        },
        "discovery_modes": {
            "massive_discovery": "All sources combined (10K+ tools)",
            "quick_boost": "GitHub only (fast, 3K tools)",
            "github_rapid": "GitHub repositories (5K tools)"
        },
        "no_deduplication": "Tools are added without deduplication for maximum count",
        "estimated_total_capacity": "15,000+ tools across all sources"
    }

@router.post("/external/alternativeto")
def run_alternativeto_discovery(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """AlternativeTo tools discovery"""
    
    target_tools = request_data.get("target_tools", 3000)
    
    print(f"🔄 Starting AlternativeTo discovery...")
    results = external_data_service.run_sync_alternativeto_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"AlternativeTo discovery completed: {results['total_saved']} tools added",
        "results": results
    }

@router.post("/external/product-hunt")
def run_product_hunt_discovery(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Product Hunt tools discovery"""
    
    target_tools = request_data.get("target_tools", 2000)
    
    print(f"🏆 Starting Product Hunt discovery...")
    results = external_data_service.run_sync_product_hunt_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"Product Hunt discovery completed: {results['total_saved']} tools added",
        "results": results
    }

@router.post("/external/directory-scraping")
def run_directory_scraping_discovery(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """AI directory scraping discovery"""
    
    target_tools = request_data.get("target_tools", 3000)
    
    print(f"🕷️ Starting directory scraping discovery...")
    results = external_data_service.run_sync_directory_scraping(target_tools)
    
    return {
        "success": True,
        "message": f"Directory scraping completed: {results['total_saved']} tools added",
        "results": results
    }

@router.post("/external/chrome-extensions")
def run_chrome_extensions_discovery(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Chrome Web Store extensions discovery"""
    
    target_tools = request_data.get("target_tools", 2000)
    
    print(f"🌐 Starting Chrome extensions discovery...")
    results = external_data_service.run_sync_chrome_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"Chrome extensions discovery completed: {results['total_saved']} extensions added",
        "results": results
    }

@router.post("/external/vscode-extensions")
def run_vscode_extensions_discovery(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """VS Code Marketplace extensions discovery"""
    
    target_tools = request_data.get("target_tools", 1500)
    
    print(f"🔧 Starting VS Code extensions discovery...")
    results = external_data_service.run_sync_vscode_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"VS Code extensions discovery completed: {results['total_saved']} extensions added",
        "results": results
    }

@router.post("/external/npm-packages")
def run_npm_packages_discovery(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """NPM packages discovery"""
    
    target_tools = request_data.get("target_tools", 2000)
    
    print(f"📦 Starting NPM packages discovery...")
    results = external_data_service.run_sync_npm_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"NPM packages discovery completed: {results['total_saved']} packages added",
        "results": results
    }

@router.post("/external/pypi-packages")
def run_pypi_packages_discovery(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """PyPI packages discovery"""
    
    target_tools = request_data.get("target_tools", 1500)
    
    print(f"🐍 Starting PyPI packages discovery...")
    results = external_data_service.run_sync_pypi_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"PyPI packages discovery completed: {results['total_saved']} packages added",
        "results": results
    }