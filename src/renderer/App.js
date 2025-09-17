import React, { useState } from 'react';
import './App.css';

function App() {
  const [message, setMessage] = useState('Welcome to My Ollama Wrapper!');

  return (
    <div className="App">
      <header className="App-header">
        <h1>My Ollama Wrapper</h1>
        <p>{message}</p>
        <div className="controls">
          <button onClick={() => setMessage('Ready to connect to Ollama!')}>
            Get Started
          </button>
        </div>
      </header>
      <main className="App-main">
        <div className="chat-container">
          <h2>Ollama Chat Interface</h2>
          <p>This is where the Ollama chat interface will be implemented.</p>
          <div className="placeholder-chat">
            <div className="message user-message">
              <strong>User:</strong> Hello Ollama!
            </div>
            <div className="message ai-message">
              <strong>AI:</strong> Hello! I'm ready to help you. How can I assist you today?
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;