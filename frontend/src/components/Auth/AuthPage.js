import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import Login from './Login';
import Signup from './Signup';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const { login } = useAuth();

  const handleLogin = (userData) => {
    login(userData);
  };

  const handleSignup = (userData) => {
    login(userData);
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
  };

  return (
    <>
      {isLogin ? (
        <Login onLogin={handleLogin} onToggle={toggleMode} />
      ) : (
        <Signup onSignup={handleSignup} onToggle={toggleMode} />
      )}
    </>
  );
};

export default AuthPage;
