from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# User schemas
class UserBase(BaseModel):
    username: str
    email: str  # Changed from EmailStr to str to simplify dependencies

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class User(UserInDB):
    pass

# Message schemas
class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Conversation schemas
class ConversationBase(BaseModel):
    title: str

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[Message] = []

    model_config = ConfigDict(from_attributes=True)

# Chat specific schemas
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: int