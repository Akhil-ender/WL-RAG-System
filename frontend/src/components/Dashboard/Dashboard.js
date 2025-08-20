import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import PDFUpload from '../Upload/PDFUpload';
import ChatInterface from '../Chat/ChatInterface';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('upload');

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1 className="dashboard-title">PDF Chat Assistant</h1>
        <div className="user-info">
          <div className="user-details">
            <p className="user-name">{user?.username}</p>
            <p className="user-role">{user?.role}</p>
          </div>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </header>
      
      <main className="dashboard-content">
        <div className="dashboard-tabs">
          <button 
            className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            Upload PDF
          </button>
          <button 
            className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
        </div>
        
        <div className="tab-content">
          {activeTab === 'upload' && <PDFUpload />}
          {activeTab === 'chat' && <ChatInterface />}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
