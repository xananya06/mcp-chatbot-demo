// ConversationItem.jsx
import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import './ConversationItem.css';

function ConversationItem({ conversation, isActive, onClick, onDelete }) {
  const formattedDate = formatDistanceToNow(new Date(conversation.createdAt), { addSuffix: true });

  // Handle delete click without triggering the conversation selection
  const handleDeleteClick = (e) => {
    e.stopPropagation();
    onDelete();
  };

  return (
    <div
      className={`conversation-item ${isActive ? 'active' : ''}`}
      onClick={onClick}
    >
      <div className="conversation-details">
        <div className="conversation-title">{conversation.title}</div>
        <div className="conversation-date">{formattedDate}</div>
      </div>

      <button
        className="delete-button"
        onClick={handleDeleteClick}
        aria-label="Delete conversation"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" fill="currentColor" />
        </svg>
      </button>
    </div>
  );
}

export default ConversationItem;