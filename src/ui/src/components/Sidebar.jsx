// Sidebar.jsx
import React from 'react';
import ConversationItem from './ConversationItem';
import Button from './Button';
import './Sidebar.css';


function Sidebar({
  conversations,
  activeConversation,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  handleLogout,
  userName,
}) {

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1 className="logo">Acuvity AI Chat</h1>
        <Button variant="primary" onClick={onNewConversation} fullWidth>
          New chat
        </Button>
      </div>

      <div className="conversations-list">
        {conversations.map(conversation => (
          <ConversationItem
            key={conversation.id}
            conversation={conversation}
            isActive={conversation.id === activeConversation}
            onClick={() => onSelectConversation(conversation.id)}
            onDelete={() => onDeleteConversation(conversation.id)}
          />
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="avatar">U</div>
          <div className="user-info">
            <span className="username">{ userName }</span>
          </div>
        </div>
        {handleLogout ? (
        <div className="user-info" style={{ marginTop: '10px', marginBottom: '10px' }}>
          <Button variant="primary" onClick={handleLogout} fullWidth>
            Logout
          </Button>
        </div>
        ) : null}
      </div>
    </div>
  );
}

export default Sidebar;