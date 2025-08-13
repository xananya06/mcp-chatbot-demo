// App.jsx - LinkedIn APB Demo Version
import React from 'react';
import LinkedInAPBDemo from './components/LinkedInAPBDemo';
import './App.css';

function App({
  user = null,
  handleLogout = null,
  sessionToken = "DummySessionToken",
}) {
  // Using LinkedIn APB Demo interface instead of original chat
  return <LinkedInAPBDemo />;
}

export default App;