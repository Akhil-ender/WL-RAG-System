import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthPage from './components/Auth/AuthPage';
import Dashboard from './components/Dashboard/Dashboard';
import './App.css';

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route 
          path="/auth" 
          element={user ? <Navigate to="/dashboard" /> : <AuthPage />} 
        />
        <Route 
          path="/dashboard" 
          element={user ? <Dashboard /> : <Navigate to="/auth" />} 
        />
        <Route path="/" element={<Navigate to={user ? "/dashboard" : "/auth"} />} />
      </Routes>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
