import React, { useState, useRef, useEffect } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import EmptyState from './EmptyState';
import './ChatWindow.css';

function ChatWindow({ conversation, onSendMessage }) {
  // Add state to track when waiting for a response
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages]);

  const handleSendMessage = (message) => {
    if (!message.trim() || isWaitingForResponse) return;

    // Set waiting state to true before sending
    setIsWaitingForResponse(true);

    // Pass a callback to onSendMessage that will be called when the response is received
    onSendMessage(message, () => {
      setIsWaitingForResponse(false);
    });
  };

  if (!conversation) {
    return <EmptyState />;
  }

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>{conversation.title}</h2>
      </div>

      <div className="chat-messages">
        <MessageList messages={conversation.messages} />

        {isWaitingForResponse && (
          <div className="typing-indicator">
            <div className="typing-indicator-text">
              <span>Thinking</span>
              <div className="typing-dots">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <MessageInput
          onSendMessage={handleSendMessage}
          isDisabled={isWaitingForResponse}
        />
      </div>
    </div>
  );
}

export default ChatWindow;