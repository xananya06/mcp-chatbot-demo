// index.js - Entry point for the React application
import React from 'react';
import ReactDOM from 'react-dom/client';
import { AuthProvider } from '@descope/react-sdk';
import Login from './Login';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
const projectId = process.env.REACT_APP_DESCOPE_PROJECT_ID;
console.log('ProjectID:', projectId);

root.render(
  <React.StrictMode>
    {projectId ? (
    <AuthProvider projectId={projectId}>
      <Login />
    </AuthProvider>
    ) : (
      <App />
    )
    }
  </React.StrictMode>
);