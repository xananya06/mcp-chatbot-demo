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
    focus: str = "all",  # "ai_services", "code_editors", "plugins", or "all"
    db: Session = Depends(get_db),
    current_user_id: int = Depends(auth.get_verified_user_id),
):
    """Discover AI tools by category - AI services, code editors, and plugins"""
    from app.models.chat import DiscoveredTool
    from app.services.agent_service import agent_service
    
    # Define search strategies for each category
    search_strategies = {
        "ai_services": [
            "AI API services 2024 developers",
            "machine learning APIs platforms",
            "AI SaaS tools developers", 
            "OpenAI alternatives API services",
            "computer vision APIs",
            "NLP APIs natural language processing"
        ],
        "code_editors": [
            "AI code editors 2024",
            "AI-powered IDEs programming",
            "GitHub Copilot alternatives",
            "AI coding assistants editors",
            "smart code completion tools",
            "AI pair programming tools"
        ],
        "plugins": [
            "VSCode AI extensions plugins",
            "Chrome AI developer extensions",
            "JetBrains AI plugins",
            "Vim AI plugins",
            "browser AI developer tools",
            "AI code review plugins"
        ]
    }
    
    if focus == "all":
        categories_to_search = ["ai_services", "code_editors", "plugins"]
    else:
        categories_to_search = [focus] if focus in search_strategies else ["ai_services", "code_editors", "plugins"]
    
    discovery_prompt = f"""
    Use sequential thinking to systematically discover AI tools on the internet.

    FOCUS ON THESE CATEGORIES: {', '.join(categories_to_search)}
    
    TOOL CATEGORIES:
    1. AI Services: APIs, platforms, SaaS tools (OpenAI, Anthropic, Hugging Face, etc.)
    2. Code Editors: AI-powered coding tools (Cursor, GitHub Copilot, Replit, etc.)
    3. Plugins: AI extensions for existing tools (VSCode extensions, browser plugins, etc.)

    SEARCH STRATEGY:
    Step 1: Plan comprehensive search across multiple sources
    Step 2: Search systematically using these queries:
    """
    
    # Add relevant search queries based on focus
    for category in categories_to_search:
        discovery_prompt += f"\n    - For {category}: {', '.join(search_strategies[category])}"
    
    discovery_prompt += """
    
    Step 3: Check these sources:
    - GitHub repositories and trending
    - ProductHunt AI tools
    - Tool directories (stackshare.io, alternativeto.net)
    - Developer blogs and forums
    - Company websites and documentation
    
    Step 4: Extract detailed information for each tool
    Step 5: Validate and categorize findings
    
    FOR EACH TOOL FOUND, EXTRACT:
    - Name (exact product name)
    - Website URL (official website)
    - Description (what it does, 1-2 sentences)
    - Tool type (ai_service, code_editor, or plugin)
    - Category (API, SaaS, VSCode Extension, Chrome Extension, IDE, etc.)
    - Pricing (Free, Paid, Freemium, Open Source)
    - Key features (main capabilities)
    
    Return ONLY a JSON array in this exact format:
    [
        {
            "name": "GitHub Copilot",
            "website": "https://github.com/features/copilot",
            "description": "AI pair programmer that suggests code and entire functions",
            "tool_type": "code_editor",
            "category": "IDE Integration",
            "pricing": "Paid",
            "features": "Code completion, function generation, chat interface",
            "confidence": 0.95
        }
    ]
    
    Focus on finding REAL, ACTIVE tools. Prioritize quality over quantity.
    Use your web search and fetch tools extensively.
    """
    
    try:
        response = agent_service.send(discovery_prompt, block=True, timeout=120)
        
        # Extract JSON from response
        json_match = re.search(r'\[.*?\]', response, re.DOTALL)
        
        if json_match:
            try:
                tools_data = json.loads(json_match.group())
                stored_tools = []
                
                for tool_data in tools_data:
                    if isinstance(tool_data, dict) and tool_data.get('name'):
                        # Validate tool_type
                        tool_type = tool_data.get('tool_type', '').lower()
                        if tool_type not in ['ai_service', 'code_editor', 'plugin']:
                            tool_type = 'ai_service'  # default
                        
                        tool = DiscoveredTool(
                            name=tool_data.get('name', ''),
                            website=tool_data.get('website', ''),
                            description=tool_data.get('description', ''),
                            tool_type=tool_type,
                            category=tool_data.get('category', ''),
                            pricing=tool_data.get('pricing', ''),
                            features=tool_data.get('features', ''),
                            confidence_score=float(tool_data.get('confidence', 0.0)),
                            source_data=json.dumps(tool_data)
                        )
                        db.add(tool)
                        stored_tools.append(tool_data)
                
                db.commit()
                
                return {
                    "success": True,
                    "tools": stored_tools,
                    "count": len(stored_tools),
                    "focus": focus,
                    "categories_searched": categories_to_search
                }
                
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Failed to parse JSON: {e}",
                    "raw_response": response[:1000] + "..." if len(response) > 1000 else response
                }
        else:
            return {
                "success": False,
                "error": "No JSON array found in response",
                "raw_response": response[:1000] + "..." if len(response) > 1000 else response
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Discovery failed: {e}",
            "tools": []
        }


@router.get("/tools")
def get_discovered_tools(
    tool_type: Optional[str] = None,  # Filter by ai_service, code_editor, plugin
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