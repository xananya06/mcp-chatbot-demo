from sqlalchemy.orm import Session
from typing import Optional

from app.models.chat import User, Conversation, Message
from app.schemas.chat import ChatRequest, MessageCreate

from app.services.agent_service import agent_service

class ChatService:
    def get_or_create_conversation(self, db: Session, user_id: int, conversation_id: Optional[int] = None) -> tuple[Conversation, bool]:
        """Get existing conversation or create a new one"""
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            if conversation:
                return conversation, False

        # Create new conversation
        new_conversation = Conversation(
            title="New Conversation",
            user_id=user_id
        )
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        return new_conversation, True

    def add_message(self, db: Session, conversation_id: int, role: str, content: str) -> Message:
        """Add a message to the conversation"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def process_chat_request(self, db: Session, user_id: int, chat_request: ChatRequest) -> dict:
        """Process a chat request and generate a response"""
        # Get or create conversation
        conversation, new = self.get_or_create_conversation(db, user_id, chat_request.conversation_id)
        if new:
            agent_service.clear()

        # Add user message to conversation
        self.add_message(db, conversation.id, "user", chat_request.message)

        # Generate response (in a real app, this might call an LLM API)
        response_text = self.generate_ai_response(chat_request.message)

        # Add assistant message to conversation
        self.add_message(db, conversation.id, "assistant", response_text)

        return {
            "message": response_text,
            "conversation_id": conversation.id
        }

    def generate_ai_response(self, user_message: str) -> str:
        """
        Generate AI response to user message.
        In a real application, this would likely call an external LLM API.
        """
        # Placeholder response generation
        return agent_service.send(user_message, block=True)

chat_service = ChatService()