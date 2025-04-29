import React, { useState } from 'react';
import Button from './Button';
import './MessageInput.css';

function MessageInput({ onSendMessage, isDisabled }) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!message.trim() || isDisabled) return;

    onSendMessage(message);
    setMessage('');
  };

  return (
    <form className="message-input-form" onSubmit={handleSubmit}>
      <textarea
        className="message-input"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder={isDisabled ? "Waiting for response..." : "Type your message here..."}
        rows={1}
        disabled={isDisabled}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
          }
        }}
      />
      <Button
        type="submit"
        variant="primary"
        disabled={!message.trim() || isDisabled}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor" />
        </svg>
      </Button>
    </form>
  );
}

export default MessageInput;