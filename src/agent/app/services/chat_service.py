# Complete enhanced chat_service.py file
# REPLACE your entire src/agent/app/services/chat_service.py with this content

import json
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.chat import DiscoveredTool
from app.core.config import settings
from app.services.agent_service import agent_service
from app.schemas.chat import ChatRequest

def get_categories_to_search(focus: str) -> List[str]:
    """Get categories to search based on focus parameter - ENHANCED VERSION"""
    
    # Enhanced focus mapping with more AI-specific categories
    focus_mapping = {
        # New AI-specific categories
        "ai_writing_tools": ["ai_writing_tools"],
        "ai_image_generation": ["ai_image_generation"], 
        "ai_video_tools": ["ai_video_tools"],
        "ai_audio_tools": ["ai_audio_tools"],
        "ai_coding_tools": ["ai_coding_tools"],
        "ai_data_analysis": ["ai_data_analysis"],
        "ai_marketing_tools": ["ai_marketing_tools"],
        "ai_customer_service": ["ai_customer_service"],
        "ai_hr_tools": ["ai_hr_tools"],
        "ai_finance_tools": ["ai_finance_tools"],
        "ai_education_tools": ["ai_education_tools"],
        "ai_research_tools": ["ai_research_tools"],
        "ai_3d_modeling": ["ai_3d_modeling"],
        "ai_gaming_tools": ["ai_gaming_tools"],
        
        # Keep existing categories for backward compatibility
        "desktop_applications": ["desktop_applications"],
        "browser_extensions": ["browser_extensions"], 
        "mobile_apps": ["mobile_apps"],
        "web_applications": ["web_applications"],
        "ai_services": ["ai_services"],
        "code_editors": ["code_editors"],
        "plugins": ["plugins"],
        "creative_tools": ["creative_tools"],
        "business_tools": ["business_tools"],
        "productivity_tools": ["productivity_tools"],
        
        # Enhanced "all" with new categories
        "all": [
            "ai_writing_tools", "ai_image_generation", "ai_video_tools", "ai_audio_tools",
            "ai_coding_tools", "ai_data_analysis", "ai_marketing_tools", "ai_customer_service",
            "ai_hr_tools", "ai_finance_tools", "ai_education_tools", "ai_research_tools",
            "ai_3d_modeling", "ai_gaming_tools", "desktop_applications", "browser_extensions",
            "mobile_apps", "web_applications", "ai_services", "code_editors", 
            "plugins", "creative_tools", "business_tools", "productivity_tools"
        ]
    }
    
    return focus_mapping.get(focus, focus_mapping["all"])


def create_focused_discovery_prompt(categories: List[str], max_tools_per_category: int = 12) -> str:
    """Create enhanced prompts with better AI targeting"""
    
    # Enhanced category descriptions
    category_descriptions = {
        "ai_writing_tools": "AI writing assistants, content creators, copywriting tools, blog writers, grammar checkers",
        "ai_image_generation": "AI image generators, art creation tools, logo makers, photo editors, design assistants",
        "ai_video_tools": "AI video creators, editors, animation tools, deepfake, video enhancement, subtitle generators",
        "ai_audio_tools": "AI music generators, voice synthesis, audio editing, transcription tools, podcast enhancers",
        "ai_coding_tools": "AI coding assistants, code completion, debugging tools, documentation generators, code reviewers",
        "ai_data_analysis": "AI data visualization, analytics platforms, business intelligence tools, statistical analysis",
        "ai_marketing_tools": "AI marketing automation, social media tools, SEO assistants, ad creators, email marketing",
        "ai_customer_service": "AI chatbots, customer support tools, help desk automation, sentiment analysis",
        "ai_hr_tools": "AI recruitment tools, resume screening, HR automation, talent management, interview assistants",
        "ai_finance_tools": "AI trading platforms, financial analysis, accounting automation, fraud detection",
        "ai_education_tools": "AI tutoring platforms, online learning tools, educational assistants, course creators",
        "ai_research_tools": "AI research assistants, literature review tools, academic helpers, citation managers",
        "ai_3d_modeling": "AI 3D generators, CAD tools, architecture design, VR/AR creators, modeling assistants",
        "ai_gaming_tools": "AI game development tools, procedural generation, NPC AI, game testing, level design",
        "desktop_applications": "Desktop software with AI features",
        "browser_extensions": "Browser extensions and add-ons with AI capabilities", 
        "mobile_apps": "Mobile applications with AI/ML features",
        "web_applications": "Web-based AI tools and SaaS platforms",
        "ai_services": "AI APIs and cloud services for developers",
        "code_editors": "AI-powered IDEs and development environments",
        "plugins": "IDE plugins and development tool extensions",
        "creative_tools": "AI tools for creative work, design, art creation",
        "business_tools": "AI business automation, CRM, enterprise tools",
        "productivity_tools": "AI productivity apps, task management, note-taking"
    }
    
    BASE_INSTRUCTION = """CRITICAL: You must return ONLY a valid JSON array. No explanations, no text before or after.

Each tool must be REAL and CURRENTLY AVAILABLE (not hypothetical or future tools).
Include only tools you are certain exist with working websites.

"""
    
    if len(categories) == 1:
        category = categories[0]
        category_desc = category_descriptions.get(category, category.replace('_', ' ').title())
        
        prompt = f"""{BASE_INSTRUCTION}Find {max_tools_per_category} popular AI tools in this category:

**{category.replace('_', ' ').title()}**: {category_desc}

Requirements:
- Must be real, existing tools (not examples or hypothetical)
- Must have AI/ML as a core feature
- Must have a working website
- Include both popular and lesser-known tools
- Mix of pricing models (free, freemium, paid)

Return as JSON array with this exact format:
[
  {{
    "name": "Actual Tool Name",
    "website": "https://real-website.com",
    "description": "Detailed description of what this tool actually does",
    "tool_type": "{category}",
    "category": "Specific Subcategory",
    "pricing": "Free|Freemium|Paid|Enterprise",
    "features": "Feature1, Feature2, Feature3",
    "confidence": 0.9
  }}
]"""
    else:
        # Multiple categories - fewer tools per category to avoid token limits
        category_list = []
        for cat in categories[:5]:  # Limit to 5 categories to avoid overwhelming
            desc = category_descriptions.get(cat, cat.replace('_', ' ').title())
            category_list.append(f"- {cat}: {desc}")
        
        prompt = f"""{BASE_INSTRUCTION}Find 8-10 AI tools in EACH category:

{chr(10).join(category_list)}

Return ONLY a JSON array. Maximum 50 tools total."""
    
    return prompt


def enhance_pricing_info(tools: List[dict]) -> List[dict]:
    """Enhance tools with detailed pricing information"""
    
    # Define detailed pricing for known tools
    pricing_database = {
        'grammarly': "Free: Basic writing suggestions (150 limit/month) | Premium: $12/month or $144/year | Business: $15/member/month | Enterprise: Custom pricing",
        'otter.ai': "Free: 300 minutes/month | Pro: $10/user/month | Business: $20/user/month | Enterprise: Contact sales",
        'otter': "Free: 300 minutes/month | Pro: $10/user/month | Business: $20/user/month | Enterprise: Contact sales",
        'notion': "Free: Personal use | Plus: $8/month | Business: $15/user/month | Enterprise: Custom pricing",
        'merlin': "Free: 102 queries/day | Pro: $19/month (unlimited) | Team: Contact sales",
        'bardeen': "Free: Unlimited non-premium actions | Pro: $10/month | Business: $15/user/month",
        'compose ai': "Free: 1,250 words/month | Premium: $9.99/month (25,000 words) | Ultimate: $29.99/month (unlimited)",
        'compose': "Free: 1,250 words/month | Premium: $9.99/month (25,000 words) | Ultimate: $29.99/month (unlimited)",
        'liner': "Free: 3 highlights/day | Essential: $8.83/month | Professional: $14.92/month",
        'toucan': "Free: Limited translations | Plus: $11.99/month | Family: $19.99/month (6 accounts)",
        'chatgpt': "Free: Unlimited use with GPT-3.5",
        'writesonic': "Free: 10,000 words/month | Pro: $12/month | Enterprise: Custom pricing"
    }
    
    # For each tool with simple pricing, try to get detailed pricing
    for tool in tools:
        current_pricing = tool.get('pricing', '')
        tool_name_lower = tool.get('name', '').lower()
        
        # Check if we have detailed pricing for this tool
        detailed_pricing = None
        for key, pricing in pricing_database.items():
            if key in tool_name_lower:
                detailed_pricing = pricing
                break
        
        # If we found detailed pricing, use it
        if detailed_pricing:
            tool['pricing'] = detailed_pricing
        # Otherwise, enhance generic pricing types
        elif current_pricing in ['Free', 'Paid', 'Freemium', 'Open Source']:
            if current_pricing == 'Freemium':
                tool['pricing'] = "Free: Limited features | Premium: Check website for current pricing | Enterprise: Contact sales"
            elif current_pricing == 'Free':
                tool['pricing'] = "Free: Full access (may have usage limits - check website)"
            elif current_pricing == 'Paid':
                tool['pricing'] = "Paid: Check website for current pricing tiers and plans"
            elif current_pricing == 'Open Source':
                tool['pricing'] = "Open Source: Free to use (self-hosted or community version available)"
    
    return tools


def parse_tools_from_response(response: str) -> List[dict]:
    """Parse tools from AI response with improved error handling"""
    
    # Try to find JSON array in the response
    json_patterns = [
        r'\[[\s\S]*\]',  # Find array from [ to ]
        r'```json\s*(\[[\s\S]*?\])\s*```',  # JSON in code blocks
        r'```\s*(\[[\s\S]*?\])\s*```',  # Array in code blocks
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        for match in matches:
            try:
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                    
                # Clean up the JSON
                cleaned_json = match.strip()
                if cleaned_json.startswith('[') and cleaned_json.endswith(']'):
                    tools = json.loads(cleaned_json)
                    if isinstance(tools, list) and len(tools) > 0:
                        # Validate each tool has required fields
                        valid_tools = []
                        for tool in tools:
                            if (isinstance(tool, dict) and 
                                tool.get('name') and 
                                tool.get('website') and 
                                tool.get('tool_type')):
                                valid_tools.append(tool)
                        return valid_tools
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                continue
    
    print(f"Could not parse JSON from response: {response[:500]}...")
    return []


def check_for_existing_tool(db: Session, tool_data: dict) -> DiscoveredTool:
    """Check if tool already exists by website or name+type"""
    
    website = tool_data.get('website', '').strip()
    name = tool_data.get('name', '').strip()
    tool_type = tool_data.get('tool_type', '').strip()
    
    # First check by website (most reliable)
    if website:
        existing = db.query(DiscoveredTool).filter(
            DiscoveredTool.website == website
        ).first()
        if existing:
            return existing
    
    # Then check by name + tool_type combination
    if name and tool_type:
        existing = db.query(DiscoveredTool).filter(
            DiscoveredTool.name == name,
            DiscoveredTool.tool_type == tool_type
        ).first()
        if existing:
            return existing
    
    return None


def merge_tool_data(existing_tool: DiscoveredTool, new_data: dict) -> bool:
    """Merge new tool data with existing tool, return True if updated"""
    
    updated = False
    
    # Update if new confidence is higher
    new_confidence = new_data.get('confidence', 0)
    if new_confidence > existing_tool.confidence_score:
        existing_tool.confidence_score = new_confidence
        updated = True
    
    # Update pricing if new one is more detailed
    new_pricing = new_data.get('pricing', '').strip()
    if new_pricing and len(new_pricing) > len(existing_tool.pricing or ''):
        existing_tool.pricing = new_pricing
        updated = True
    
    # Merge features (combine old + new)
    existing_features = set(existing_tool.features.split(', ') if existing_tool.features else [])
    new_features = set(new_data.get('features', '').split(', ') if new_data.get('features') else [])
    combined_features = existing_features.union(new_features)
    
    if len(combined_features) > len(existing_features):
        existing_tool.features = ', '.join(sorted(combined_features))
        updated = True
    
    # Update description if new one is longer/better
    new_desc = new_data.get('description', '').strip()
    if len(new_desc) > len(existing_tool.description or ''):
        existing_tool.description = new_desc
        updated = True
    
    # Update category if more specific
    new_category = new_data.get('category', '').strip()
    if new_category and len(new_category) > len(existing_tool.category or ''):
        existing_tool.category = new_category
        updated = True
    
    if updated:
        existing_tool.updated_at = datetime.utcnow()
    
    return updated


def save_discovered_tools_with_deduplication(db: Session, tools: List[dict]) -> Dict[str, Any]:
    """Save tools while handling duplicates"""
    
    saved_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []
    
    for tool_data in tools:
        try:
            existing_tool = check_for_existing_tool(db, tool_data)
            
            if existing_tool:
                # Update existing tool
                was_updated = merge_tool_data(existing_tool, tool_data)
                if was_updated:
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                # Create new tool
                new_tool = DiscoveredTool(
                    name=tool_data.get('name', '').strip(),
                    website=tool_data.get('website', '').strip(),
                    description=tool_data.get('description', '').strip(),
                    tool_type=tool_data.get('tool_type', '').strip(),
                    category=tool_data.get('category', '').strip(),
                    pricing=tool_data.get('pricing', '').strip(),
                    features=tool_data.get('features', '').strip(),
                    confidence_score=tool_data.get('confidence', 0.0)
                )
                db.add(new_tool)
                saved_count += 1
                
        except Exception as e:
            errors.append(f"Error processing {tool_data.get('name', 'unknown')}: {str(e)}")
    
    try:
        db.commit()
        return {
            "success": True,
            "saved": saved_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "errors": errors
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Database commit failed: {str(e)}",
            "saved": 0,
            "updated": 0,
            "skipped": 0
        }

def discover_tools(focus: str, db: Session) -> Dict[str, Any]:
    """Enhanced discover tools function with improved categories and discovery"""
    
    try:
        # Get categories to search based on focus (now with enhanced categories)
        categories_to_search = get_categories_to_search(focus)
        
        # Limit categories for better performance and results
        if focus == "all":
            categories_to_search = categories_to_search[:6]  # Process 6 categories at a time
        
        print(f"Enhanced discovery starting for: {categories_to_search}")
        
        # Create enhanced prompt
        prompt = create_focused_discovery_prompt(categories_to_search)
        
        # Call AI service with reasonable timeout
        ai_response = agent_service.send(prompt, block=True, timeout=150)        
        
        # Parse tools from response
        discovered_tools = parse_tools_from_response(ai_response)
        
        if not discovered_tools:
            return {
                "success": False,
                "error": "No tools could be parsed from AI response",
                "tools": [],
                "count": 0,
                "focus": focus,
                "categories_searched": categories_to_search,
                "raw_response": ai_response[:500] + "..." if len(ai_response) > 500 else ai_response
            }
        
        print(f"Found {len(discovered_tools)} tools")
        
        # Enhance pricing information
        discovered_tools = enhance_pricing_info(discovered_tools)
        
        # Save with deduplication
        save_result = save_discovered_tools_with_deduplication(db, discovered_tools)
        
        print(f"Save result: {save_result}")
        
        return {
            "success": save_result["success"],
            "tools": discovered_tools,
            "count": len(discovered_tools),
            "focus": focus,
            "categories_searched": categories_to_search,
            "database_result": save_result
        }
        
    except Exception as e:
        error_msg = f"Enhanced discovery failed: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "tools": [],
            "count": 0,
            "focus": focus,
            "categories_searched": []
        }


# Create the chat_service instance that the routes expect
class ChatService:
    def get_or_create_conversation(self, db: Session, user_id: int, conversation_id: Optional[int] = None):
        from app.models.chat import Conversation
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            if conversation:
                return conversation, False
        
        new_conversation = Conversation(title='New Conversation', user_id=user_id)
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        return new_conversation, True

    def add_message(self, db: Session, conversation_id: int, role: str, content: str):
        from app.models.chat import Message
        message = Message(conversation_id=conversation_id, role=role, content=content)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def process_chat_request(self, db: Session, user_id: int, chat_request: ChatRequest):
        conversation, new = self.get_or_create_conversation(db, user_id, chat_request.conversation_id)
        if new:
            agent_service.clear()
        
        self.add_message(db, conversation.id, 'user', chat_request.message)
        response_text = agent_service.send(chat_request.message, block=True)
        self.add_message(db, conversation.id, 'assistant', response_text)
        
        return {'message': response_text, 'conversation_id': conversation.id}

chat_service = ChatService()