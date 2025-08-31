// src/App.tsx
import React, { useState } from 'react';
import LoginView from './components/LoginView.tsx';
import MainLayout from './components/MainLayout.tsx';

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('accessToken'));

  const handleLoginSuccess = (newToken: string) => {
    localStorage.setItem('accessToken', newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    setToken(null);
  };

  if (!token) {
    return <LoginView onLoginSuccess={handleLoginSuccess} />;
  }

  return <MainLayout onLogout={handleLogout} />;
}

export default App;
