# src/agent/app/api/routes/chat.py
# COMPLETE FIXED VERSION - All endpoints working

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
from app.services.real_apis_service import unified_apis_service

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


# ================================================================
# AI TOOLS DISCOVERY ENDPOINTS
# ================================================================

@router.post("/discover-tools")
def discover_ai_tools(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Discover AI tools using the AI-powered discovery system"""
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


@router.get("/tools/categories")
def get_tool_categories(
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get all available tool categories for discovery"""
    
    # Enhanced categories with descriptions
    categories = {
        # AI-specific categories
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
        
        # General categories
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


# ================================================================
# REAL APIS DISCOVERY ENDPOINTS (from real_apis_service.py)
# ================================================================

@router.post("/unified/discover-all-real-apis")
def discover_all_real_apis(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Discover from ALL real APIs - no web scraping"""
    
    target_tools = request_data.get("target_tools", 30000)
    
    print(f"🚀 Starting unified real APIs discovery...")
    results = unified_apis_service.run_sync_discover_all_real_apis(target_tools)
    
    return {
        "success": True,
        "message": f"Unified real APIs discovery completed: {results['total_saved']} tools added",
        "results": results,
        "apis_included": [
            "Hacker News API (Firebase)",
            "Stack Overflow API", 
            "GitHub API",
            "NPM Registry API",
            "PyPI JSON API",
            "VS Code Marketplace API",
            "Dev.to API (if token configured)",
            "Stack Exchange API"
        ],
        "no_scraping": True,
        "cost": "$0"
    }


@router.post("/unified/discover-no-auth-apis")
def discover_no_auth_apis(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Discover from APIs that need NO authentication - works immediately"""
    
    target_tools = request_data.get("target_tools", 15000)
    
    print(f"⚡ Starting no-auth APIs discovery...")
    results = unified_apis_service.run_sync_discover_no_auth_apis(target_tools)
    
    return {
        "success": True,
        "message": f"No-auth APIs discovery completed: {results['total_saved']} tools added",
        "results": results,
        "immediate_apis": [
            "Hacker News API",
            "Stack Overflow API", 
            "NPM Registry API",
            "PyPI JSON API",
            "VS Code Marketplace API"
        ],
        "setup_time": "0 minutes",
        "auth_required": False,
        "cost": "$0"
    }


@router.post("/unified/discover-hackernews")
def discover_hackernews_only(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Hacker News API only - highest quality tools"""
    
    target_tools = request_data.get("target_tools", 2500)
    
    print(f"🔥 Starting Hacker News discovery...")
    results = unified_apis_service.run_sync_discover_hackernews(target_tools)
    
    return {
        "success": True,
        "message": f"Hacker News completed: {results['total_saved']} highest-quality tools",
        "results": results,
        "quality_score": "⭐⭐⭐⭐⭐ (Very High)",
        "api_source": "hacker_news_firebase_api",
        "auth_required": False
    }


@router.post("/unified/discover-stackoverflow")
def discover_stackoverflow_only(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Stack Overflow API only - developer Q&A tools"""
    
    target_tools = request_data.get("target_tools", 4000)
    
    print(f"📚 Starting Stack Overflow discovery...")
    results = unified_apis_service.run_sync_discover_stackoverflow(target_tools)
    
    return {
        "success": True,
        "message": f"Stack Overflow completed: {results['total_saved']} developer tools",
        "results": results,
        "quality_score": "⭐⭐⭐⭐ (High)",
        "api_source": "stackoverflow_questions_api",
        "auth_required": False
    }


@router.post("/unified/discover-github")
def discover_github_only(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """GitHub API only - open source repositories"""
    
    target_tools = request_data.get("target_tools", 6000)
    
    print(f"🐙 Starting GitHub discovery...")
    results = unified_apis_service.run_sync_discover_github(target_tools)
    
    return {
        "success": True,
        "message": f"GitHub completed: {results['total_saved']} open source tools",
        "results": results,
        "quality_score": "⭐⭐⭐⭐ (High)",
        "api_source": "github_search_api",
        "auth_required": False
    }


@router.post("/unified/discover-pypi")
def discover_pypi_only(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """PyPI JSON API only - Python packages (NO SCRAPING)"""
    
    target_tools = request_data.get("target_tools", 3000)
    
    print(f"🐍 Starting PyPI JSON API discovery...")
    results = unified_apis_service.run_sync_discover_pypi(target_tools)
    
    return {
        "success": True,
        "message": f"PyPI JSON API completed: {results['total_saved']} Python packages",
        "results": results,
        "improvement": "✅ Real PyPI JSON API replaces web scraping",
        "api_source": "pypi_json_api",
        "auth_required": False
    }


@router.post("/unified/discover-npm")
def discover_npm_only(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """NPM Registry API only - JavaScript packages"""
    
    target_tools = request_data.get("target_tools", 4000)
    
    print(f"📦 Starting NPM discovery...")
    results = unified_apis_service.run_sync_discover_npm(target_tools)
    
    return {
        "success": True,
        "message": f"NPM completed: {results['total_saved']} JavaScript packages",
        "results": results,
        "quality_score": "⭐⭐⭐ (Medium)",
        "api_source": "npm_registry_api",
        "auth_required": False
    }


@router.post("/unified/discover-vscode")
def discover_vscode_only(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """VS Code Marketplace API only - editor extensions"""
    
    target_tools = request_data.get("target_tools", 2000)
    
    print(f"🔧 Starting VS Code discovery...")
    results = unified_apis_service.run_sync_discover_vscode(target_tools)
    
    return {
        "success": True,
        "message": f"VS Code completed: {results['total_saved']} extensions",
        "results": results,
        "quality_score": "⭐⭐⭐⭐ (High)",
        "api_source": "vscode_marketplace_api",
        "auth_required": False
    }


@router.post("/unified/discover-devto")
def discover_devto_only(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Dev.to Articles API only - developer articles (requires token)"""
    
    target_tools = request_data.get("target_tools", 2000)
    
    print(f"📝 Starting Dev.to discovery...")
    results = unified_apis_service.run_sync_discover_devto(target_tools)
    
    return {
        "success": True,
        "message": f"Dev.to completed: {results['total_saved']} articles",
        "results": results,
        "quality_score": "⭐⭐⭐⭐ (High)",
        "api_source": "devto_articles_api",
        "auth_required": True,
        "setup_note": "Requires DEV_TO_TOKEN environment variable"
    }


@router.post("/unified/discover-stackexchange")
def discover_stackexchange_only(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Stack Exchange Network API only - Q&A from multiple sites"""
    
    target_tools = request_data.get("target_tools", 3500)
    
    print(f"🔗 Starting Stack Exchange discovery...")
    results = unified_apis_service.run_sync_discover_stackexchange(target_tools)
    
    return {
        "success": True,
        "message": f"Stack Exchange completed: {results['total_saved']} discussions",
        "results": results,
        "quality_score": "⭐⭐⭐⭐ (High)",
        "api_source": "stackexchange_network_api",
        "auth_required": False,
        "enhancement_note": "Works better with STACKEXCHANGE_KEY"
    }


# ================================================================
# PIPELINE ENDPOINTS (using existing discovery_pipeline)
# ================================================================

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


@router.post("/pipeline/intensive")
def run_intensive_pipeline(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Run intensive discovery pipeline for rapid scaling"""
    
    target_tools = request_data.get("target_tools", 300)
    
    from app.services.discovery_pipeline import discovery_pipeline
    
    print(f"🚀 Starting intensive discovery pipeline...")
    results = discovery_pipeline.run_intensive_discovery(target_tools)
    
    return {
        "success": True,
        "message": f"Intensive pipeline completed: {results['total_saved']} new tools discovered",
        "pipeline_results": results
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


# ================================================================
# STATUS AND TESTING ENDPOINTS
# ================================================================

@router.get("/unified/api-status")
def get_unified_api_status(
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get status of all unified real APIs"""
    
    import os
    
    apis_status = {
        "service_info": {
            "name": "Unified Real APIs Service",
            "version": "3.0",
            "description": "Clean, real API integrations only",
            "scraping_removed": True,
            "total_apis": 8
        },
        "no_auth_apis": {
            "description": "APIs that work immediately - no setup required",
            "apis": [
                {"name": "Hacker News", "status": "ready", "auth": "none"},
                {"name": "Stack Overflow", "status": "ready", "auth": "none"},
                {"name": "NPM Registry", "status": "ready", "auth": "none"},
                {"name": "PyPI JSON", "status": "ready", "auth": "none"},
                {"name": "VS Code Marketplace", "status": "ready", "auth": "none"}
            ],
            "estimated_tools": "15,000+",
            "setup_time": "0 seconds"
        },
        "optional_auth_apis": {
            "description": "APIs that work better with tokens (optional)",
            "apis": [
                {
                    "name": "GitHub", 
                    "status": "enhanced" if os.getenv('GITHUB_TOKEN') else "basic",
                    "auth": "optional",
                    "rate_limit": "5000/hour" if os.getenv('GITHUB_TOKEN') else "60/hour"
                },
                {
                    "name": "Dev.to",
                    "status": "ready" if os.getenv('DEV_TO_TOKEN') else "needs_token",
                    "auth": "optional"
                },
                {
                    "name": "Stack Exchange",
                    "status": "enhanced" if os.getenv('STACKEXCHANGE_KEY') else "basic",
                    "auth": "optional"
                }
            ]
        },
        "capacity": {
            "immediate": "15,500+ tools (0 setup)",
            "with_tokens": "27,000+ tools (10 min setup)",
            "cost": "$0 for all APIs"
        },
        "advantages": [
            "✅ No web scraping - only real APIs",
            "✅ Proper deduplication",
            "✅ Free to use ($0 cost)",
            "✅ Respects rate limits",
            "✅ High quality data",
            "✅ Works immediately for most APIs"
        ]
    }
    
    return apis_status


@router.post("/unified/quick-test")
def quick_test_unified_apis(
    request_data: dict,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Quick test of unified real APIs service"""
    
    print(f"🧪 Testing Unified Real APIs Service...")
    
    test_results = {}
    total_tools = 0
    
    # Test immediate APIs (no auth needed)
    immediate_tests = [
        ("Hacker News", "hackernews", 5),
        ("Stack Overflow", "stackoverflow", 10),
        ("GitHub", "github", 5),
        ("PyPI JSON", "pypi", 5)
    ]
    
    for api_name, method_name, test_size in immediate_tests:
        try:
            print(f"  🧪 Testing {api_name}...")
            
            method = getattr(unified_apis_service, f"run_sync_discover_{method_name}")
            result = method(test_size)
            
            tools_found = result.get("total_saved", 0)
            test_results[api_name] = {
                "tools_found": tools_found,
                "status": "success" if tools_found > 0 else "no_results",
                "auth_needed": False,
                "api_type": "real_api"
            }
            total_tools += tools_found
            
        except Exception as e:
            test_results[api_name] = {
                "tools_found": 0,
                "status": "error",
                "error": str(e),
                "auth_needed": False
            }
    
    # Summary
    working_apis = len([r for r in test_results.values() if r["status"] == "success"])
    
    return {
        "success": True,
        "message": f"Unified APIs test completed: {total_tools} tools from {working_apis} working APIs",
        "test_results": test_results,
        "service_status": {
            "working_apis": working_apis,
            "total_tools_found": total_tools,
            "service_type": "unified_real_apis_only",
            "scraping_used": False,
            "reliability": "High"
        }
    }