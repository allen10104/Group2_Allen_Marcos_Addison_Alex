import { useState, useEffect } from 'react';
import { CssBaseline } from '@mui/material';
import LoginForm from './features/auth/LoginForm';
import NoticeBoard from './features/notices/NoticeBoard';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Simple auth check on load
    if (localStorage.getItem('token')) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  return (
    <>
      <CssBaseline />
      {isAuthenticated ? (
        <NoticeBoard logout={handleLogout} />
      ) : (
        <LoginForm setAuth={setIsAuthenticated} />
      )}
    </>
  );
}