# Fixed API routes - simplified to work with unified activity service
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import Optional, List
from datetime import datetime, timedelta

from app.db.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.api.auth import auth
from app.models.chat import DiscoveredTool, ToolReport, SourceTracking
from app.services.unified_activity_service import unified_activity_service

# Create a router for the chat API
router = APIRouter()

# ================================================================
# EXISTING CHAT ENDPOINTS (Keep unchanged)
# ================================================================

@router.post("/chat", response_model=ChatResponse)
def chat(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Process a chat message and return a response"""
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
# NEW UNIFIED ACTIVITY ENDPOINTS
# ================================================================

@router.get("/ai-tools/high-activity")
def get_high_activity_tools(
    activity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum activity score"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of tools to return"),
    tool_type: Optional[str] = Query(None, description="Filter by detected tool type"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get only tools with high activity scores (>0.7 by default)"""
    
    query = db.query(DiscoveredTool).filter(
        DiscoveredTool.activity_score >= activity_threshold
    )
    
    if tool_type:
        query = query.filter(DiscoveredTool.tool_type_detected == tool_type)
    
    tools = query.order_by(desc(DiscoveredTool.activity_score)).limit(limit).all()
    
    return {
        "tools": [
            {
                "name": tool.name,
                "website": tool.website,
                "description": tool.description,
                "tool_type_detected": tool.tool_type_detected,
                "activity_score": tool.activity_score,
                "github_stars": tool.github_stars,
                "npm_weekly_downloads": tool.npm_weekly_downloads,
                "is_actively_maintained": tool.is_actively_maintained,
                "last_activity_check": tool.last_activity_check
            }
            for tool in tools
        ],
        "count": len(tools),
        "activity_threshold": activity_threshold,
        "note": "High-activity tools using unified assessment system"
    }

@router.post("/admin/activity-assessment/run")
def run_activity_assessment(
    batch_size: int = Query(100, ge=10, le=500),
    max_tools: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Run unified activity assessment on tools"""
    
    try:
        result = unified_activity_service.sync_assess_tools_batch(batch_size, max_tools)
        
        return {
            "success": True,
            "assessment_results": result,
            "note": "Unified activity assessment completed"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Activity assessment failed: {str(e)}"
        )

@router.get("/admin/activity-status")
def get_activity_status(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get activity status overview"""
    
    # Tools by activity level
    total_tools = db.query(func.count(DiscoveredTool.id)).scalar()
    
    highly_active = db.query(func.count(DiscoveredTool.id)).filter(
        DiscoveredTool.activity_score >= 0.8
    ).scalar()
    
    moderately_active = db.query(func.count(DiscoveredTool.id)).filter(
        and_(
            DiscoveredTool.activity_score >= 0.5,
            DiscoveredTool.activity_score < 0.8
        )
    ).scalar()
    
    low_activity = db.query(func.count(DiscoveredTool.id)).filter(
        DiscoveredTool.activity_score < 0.5
    ).scalar()
    
    never_assessed = db.query(func.count(DiscoveredTool.id)).filter(
        DiscoveredTool.last_activity_check.is_(None)
    ).scalar()
    
    # Activity by tool type
    activity_by_type = db.query(
        DiscoveredTool.tool_type_detected,
        func.avg(DiscoveredTool.activity_score).label('avg_activity'),
        func.count(DiscoveredTool.id).label('count')
    ).filter(
        DiscoveredTool.tool_type_detected.isnot(None)
    ).group_by(DiscoveredTool.tool_type_detected).all()
    
    return {
        "activity_overview": {
            "total_tools": total_tools,
            "highly_active": highly_active,
            "moderately_active": moderately_active,
            "low_activity": low_activity,
            "never_assessed": never_assessed,
            "high_activity_percentage": round((highly_active / total_tools) * 100, 1) if total_tools > 0 else 0
        },
        "activity_by_tool_type": {
            f"{item.tool_type_detected}": {
                "avg_activity_score": round(float(item.avg_activity), 2) if item.avg_activity else 0,
                "tool_count": item.count
            }
            for item in activity_by_type
        },
        "note": "Unified activity metrics across all tool types"
    }

@router.get("/test-unified-activity")
def test_unified_activity(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Test the unified activity system"""
    
    # Get a few tools to test
    tools = db.query(DiscoveredTool).limit(5).all()
    
    if not tools:
        return {"message": "No tools found in database"}
    
    # Test tool type detection
    results = []
    for tool in tools:
        tool_type = unified_activity_service.detect_tool_type(tool)
        results.append({
            "name": tool.name,
            "website": tool.website,
            "detected_type": tool_type,
            "current_activity_score": tool.activity_score,
            "current_tool_type": tool.tool_type_detected
        })
    
    return {
        "test_results": results,
        "message": "Unified activity service is working!",
        "note": "This tests tool type detection from the unified service"
    }

# ================================================================
# SIMPLIFIED TOOL ENDPOINTS
# ================================================================

@router.get("/tools/stats")
def get_tools_statistics(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get basic statistics about discovered tools"""
    
    # Basic counts
    total_count = db.query(func.count(DiscoveredTool.id)).scalar()
    
    # Count by detected tool type
    type_stats = db.query(
        DiscoveredTool.tool_type_detected,
        func.count(DiscoveredTool.id).label('count')
    ).filter(
        DiscoveredTool.tool_type_detected.isnot(None)
    ).group_by(DiscoveredTool.tool_type_detected).all()
    
    # Activity metrics
    high_activity = db.query(func.count(DiscoveredTool.id)).filter(
        DiscoveredTool.activity_score >= 0.7
    ).scalar()
    
    activity_checked = db.query(func.count(DiscoveredTool.id)).filter(
        DiscoveredTool.last_activity_check.isnot(None)
    ).scalar()
    
    actively_maintained = db.query(func.count(DiscoveredTool.id)).filter(
        DiscoveredTool.is_actively_maintained == True
    ).scalar()
    
    return {
        "total_tools": total_count,
        "by_detected_type": {stat.tool_type_detected: stat.count for stat in type_stats},
        "activity_metrics": {
            "high_activity_tools": high_activity,
            "activity_checked_tools": activity_checked,
            "actively_maintained_tools": actively_maintained,
            "activity_coverage": round((activity_checked / total_count) * 100, 1) if total_count > 0 else 0
        },
        "note": "Statistics using unified activity assessment system"
    }

@router.get("/system-status")
def get_system_status(
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get simplified system status"""
    
    return {
        "database_integration": "✅ PostgreSQL with Unified Activity Tracking",
        "agent_access": "✅ Direct database queries via MCP with activity filtering",
        "unified_features": {
            "activity_assessment": "✅ GitHub, NPM, PyPI, and web app assessment",
            "tool_type_detection": "✅ Automatic detection of tool platforms",
            "unified_scoring": "✅ Single activity score across all tool types",
            "source_specific_metrics": "✅ Stars, downloads, releases, etc."
        },
        "new_endpoints": [
            "/ai-tools/high-activity",
            "/admin/activity-assessment/run",
            "/admin/activity-status",
            "/test-unified-activity"
        ],
        "architecture": "Agent → PostgreSQL MCP → Unified Activity Assessment",
        "improvement": "✅ Replaced separate health checkers with unified system"
    }

# Add these new endpoints to your existing chat.py file

@router.post("/admin/discovery/enhanced")
def run_enhanced_discovery(
    strategy: str = Query("standard", description="Discovery strategy"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Run enhanced discovery with APIs + Web Scraping"""
    try:
        from enhanced_discovery_service import enhanced_discovery_service
        result = enhanced_discovery_service.sync_discover_from_all_sources(
            target_tools=200 if strategy == "standard" else 500
        )
        return {
            "success": True,
            "strategy": strategy,
            "discovery_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced discovery failed: {str(e)}")

@router.get("/admin/discovery/sources")
def get_discovery_sources(
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Get available discovery sources"""
    return {
        "api_sources": [
            "GitHub API", "NPM Registry", "PyPI JSON API", 
            "Stack Overflow API", "Hacker News API"
        ],
        "scraping_sources": [
            "Product Hunt", "AI Tools FYI", "There's An AI For That",
            "Futurepedia", "Toolify", "GPT Hunter"
        ],
        "total_sources": 11,
        "capabilities": "APIs + Web Scraping for maximum AI tool coverage"
    }