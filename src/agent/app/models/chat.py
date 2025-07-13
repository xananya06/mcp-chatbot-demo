from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Integer, default=1)
    conversations = relationship("Conversation", back_populates="user")
    tool_reports = relationship("ToolReport", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")

class DiscoveredTool(Base):
    __tablename__ = "discovered_tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    website = Column(String)
    description = Column(Text)
    tool_type = Column(String, nullable=False, index=True)
    category = Column(String)
    pricing = Column(Text)
    features = Column(Text)
    confidence_score = Column(Float, index=True)
    source_data = Column(Text)
    
    # Quality tracking fields (existing)
    last_health_check = Column(DateTime(timezone=True))
    website_status = Column(Integer, index=True)  # HTTP status codes (200, 404, 500, etc.)
    user_reports = Column(Integer, default=0, nullable=False)  # Count of user-reported issues
    canonical_url = Column(String, index=True)  # Clean version for duplicate detection
    company_name = Column(String)  # To catch same company with multiple tool names
    
    # NEW: Unified activity tracking fields
    tool_type_detected = Column(String)  # github_repo, npm_package, web_app, etc.
    activity_score = Column(Float, index=True)  # 0.0-1.0 unified score
    last_activity_check = Column(DateTime(timezone=True))  # replaces last_health_check
    
    # NEW: Source-specific metrics
    github_stars = Column(Integer)
    github_last_commit = Column(DateTime(timezone=True))
    github_contributors = Column(Integer)
    
    npm_weekly_downloads = Column(Integer)
    npm_last_version = Column(String)
    npm_last_update = Column(DateTime(timezone=True))
    
    pypi_downloads = Column(Integer)
    pypi_last_release = Column(DateTime(timezone=True))
    
    # NEW: Quality indicators
    is_actively_maintained = Column(Boolean, default=False)
    community_size_score = Column(Float)
    usage_popularity_score = Column(Float)
    maintenance_quality_score = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    reports = relationship("ToolReport", back_populates="tool")

class SourceTracking(Base):
    """Track which sources we monitor for tool discovery"""
    __tablename__ = "source_tracking"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String, nullable=False, unique=True, index=True)
    source_url = Column(String)
    last_checked = Column(DateTime(timezone=True))
    last_modified = Column(DateTime(timezone=True))
    new_tools_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ToolReport(Base):
    """User feedback system for tool quality"""
    __tablename__ = "tool_reports"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("discovered_tools.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    report_type = Column(String, nullable=False)  # 'dead_link', 'wrong_pricing', 'wrong_category', 'outdated_info'
    description = Column(Text)
    status = Column(String, default='pending', nullable=False)  # 'pending', 'resolved', 'rejected'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    tool = relationship("DiscoveredTool", back_populates="reports")
    user = relationship("User", back_populates="tool_reports")