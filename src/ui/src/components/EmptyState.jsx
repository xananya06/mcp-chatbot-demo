// EmptyState.jsx
import React from 'react';
import './EmptyState.css';

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-state-content">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" fill="currentColor" />
        </svg>
        <h2>No Conversation Selected</h2>
        <p>Select a conversation from the sidebar or start a new chat.</p>
      </div>
    </div>
  );
}

export default EmptyState;