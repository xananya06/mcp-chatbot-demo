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
