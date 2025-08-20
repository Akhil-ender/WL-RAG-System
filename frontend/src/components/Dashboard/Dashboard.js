import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import PDFUpload from '../Upload/PDFUpload';
import ChatInterface from '../Chat/ChatInterface';
import Text2SQL from '../Text2SQL/Text2SQL';
import CSVUpload from '../CSVUpload/CSVUpload';
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
          <button 
            className={`tab-button ${activeTab === 'text2sql' ? 'active' : ''}`}
            onClick={() => setActiveTab('text2sql')}
          >
            Text to SQL
          </button>
          {user?.role === 'ADMIN' && (
            <button 
              className={`tab-button ${activeTab === 'csv-upload' ? 'active' : ''}`}
              onClick={() => setActiveTab('csv-upload')}
            >
              CSV Upload
            </button>
          )}
        </div>
        
        <div className="tab-content">
          {activeTab === 'upload' && <PDFUpload />}
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'text2sql' && <Text2SQL />}
          {activeTab === 'csv-upload' && <CSVUpload />}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
