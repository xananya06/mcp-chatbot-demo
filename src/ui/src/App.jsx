// App.jsx - Main application component
import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';

import './App.css';

function App({
  user = null,
  handleLogout = null,
  sessionToken = "DummySessionToken",
}) {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);

  // Initialize with a welcome conversation on first load
  useEffect(() => {
    if (conversations.length === 0) {
      const initialConversation = {
        id: Date.now(),
        title: 'New chat',
        messages: [
          {
            id: 'welcome-msg',
            role: 'assistant',
            content: 'Hello! How can I assist you today?',
            timestamp: new Date().toISOString(),
          },
        ],
        createdAt: new Date().toISOString(),
      };

      setConversations([initialConversation]);
      setActiveConversation(initialConversation.id);
    }
  }, [conversations.length]);

  // Create a new conversation
  const createNewConversation = () => {
    const newConversation = {
      id: Date.now(),
      title: 'New chat',
      messages: [
        {
          id: 'welcome-msg',
          role: 'assistant',
          content: 'Hello! How can I assist you today?',
          timestamp: new Date().toISOString(),
        },
      ],
      createdAt: new Date().toISOString(),
    };

    setConversations([newConversation, ...conversations]);
    setActiveConversation(newConversation.id);
  };


  const sendMessage = async (message, onResponseReceived) => {
    if (!activeConversation) return;

    // Add user message immediately for better UX
    const userMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };

    // Update with user message first
    const updatedConversationsWithUserMessage = conversations.map(convo => {
      if (convo.id === activeConversation) {
        // Update conversation title if this is the first user message
        let updatedTitle = convo.title;
        if (convo.messages.length === 1 && convo.messages[0].id === 'welcome-msg') {
          updatedTitle = message.substring(0, 60) + (message.length > 60 ? '...' : '');
        }

        return {
          ...convo,
          title: updatedTitle,
          messages: [...convo.messages, userMessage],
        };
      }
      return convo;
    });

    setConversations(updatedConversationsWithUserMessage);

    try {
      // Call your AI backend
      const response = await fetch(process.env.REACT_APP_API_SERVER_BASE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer ' + sessionToken,
        },
        body: JSON.stringify({
          message: message,
          conversationId: activeConversation,
        }),
      });

      const data = await response.json();

      // Add the AI response
      const assistantMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toISOString(),
      };

      // Important: Use functional update to ensure latest state
      setConversations(currentConversations => {
        return currentConversations.map(convo => {
          if (convo.id === activeConversation) {
            return {
              ...convo,
              messages: [...convo.messages, assistantMessage],
            };
          }
          return convo;
        });
      });

    } catch (error) {
      console.error('Error communicating with AI service:', error);

      // Add an error message
      setConversations(currentConversations => {
        return currentConversations.map(convo => {
          if (convo.id === activeConversation) {
            const errorMessage = {
              id: `error-${Date.now()}`,
              role: 'assistant',
              content: "Sorry, I'm having trouble connecting to the server. Please try again later.",
              timestamp: new Date().toISOString(),
              isError: true
            };

            return {
              ...convo,
              messages: [...convo.messages, errorMessage],
            };
          }
          return convo;
        });
      });
    } finally {
      // Always call the callback when done, whether successful or not
      if (onResponseReceived) {
        onResponseReceived();
      }
    }
  };

  const deleteConversation = (id) => {
    const updatedConversations = conversations.filter(convo => convo.id !== id);
    setConversations(updatedConversations);

    // If the active conversation is deleted, select another one or create a new one
    if (id === activeConversation) {
      if (updatedConversations.length > 0) {
        setActiveConversation(updatedConversations[0].id);
      } else {
        createNewConversation();
      }
    }
  };

  // Get the active conversation object
  const currentConversation = conversations.find(convo => convo.id === activeConversation) || null;

  console.log(user)
  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        activeConversation={activeConversation}
        onSelectConversation={setActiveConversation}
        onNewConversation={createNewConversation}
        onDeleteConversation={deleteConversation}
        handleLogout={handleLogout}
        userName={user?.name || 'User'}
      />
      <ChatWindow
        conversation={currentConversation}
        onSendMessage={sendMessage}
      />
    </div>
  );
}

export default App;