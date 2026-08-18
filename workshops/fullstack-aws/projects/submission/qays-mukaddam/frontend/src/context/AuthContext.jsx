// createContext lets us share state (the logged-in user) across the whole
// app without passing props down through every component manually.
// useContext reads that shared state. useState holds the actual values.
// useEffect runs code when the component first loads.
import { createContext, useContext, useState, useEffect } from 'react';

// useNavigate lets us redirect to /login when a token expires mid-session.
import { useNavigate } from 'react-router-dom';

// Reads the role/id out of the JWT payload.
import { decodeToken } from '../utils/decodeToken';

// Registers what should happen whenever any API call gets a 401 response.
import { setUnauthorizedHandler } from '../api/api';

// The actual context object other components will read from.
const AuthContext = createContext(null);

// A custom hook so components can just call useAuth() instead of
// importing useContext and AuthContext separately every time.
export function useAuth() {
  return useContext(AuthContext);
}

// Wraps the whole app (in main.jsx) so every page can access login state.
export function AuthProvider({ children }) {
  // Holds the raw JWT string, or null if not logged in.
  const [token, setToken] = useState(null);

  // Holds the decoded user info ({ userId, role }), or null if not
  // logged in.
  const [user, setUser] = useState(null);

  // For redirecting to /login when a token expires mid-session.
  const navigate = useNavigate();

  // On first load, check if a token was saved in localStorage from a
  // previous session, so a page refresh doesn't log the user out.
  useEffect(() => {
    const savedToken = localStorage.getItem('token');

    if (savedToken) {
      // Re-decode the saved token to restore the user's role/id.
      const payload = decodeToken(savedToken);
      setToken(savedToken);
      setUser({ userId: payload.sub, role: payload.role });
    }
    // Empty array means this only runs once, when the component mounts.
  }, []);

  // Registers the 401 handler once, when the app first loads. Kept as
  // its own effect (separate from the token-restoring one above) since
  // it's a different concern.
  useEffect(() => {
    // Pass a function that clears the session and redirects, exactly
    // what should happen the moment any request comes back 401.
    setUnauthorizedHandler(() => {
      // Clear the (now-invalid) session, same as a normal logout.
      setToken(null);
      setUser(null);
      localStorage.removeItem('token');
      // Send the user back to the login page.
      navigate('/login');
    });
    // Re-runs if navigate ever changes (it normally won't, but this
    // keeps the effect correctly dependent on everything it uses).
  }, [navigate]);

  // Called after a successful login API call. Stores the token both in
  // state (for the current session) and localStorage (so it survives a
  // page refresh).
  function login(accessToken) {
    const payload = decodeToken(accessToken);

    setToken(accessToken);
    setUser({ userId: payload.sub, role: payload.role });
    localStorage.setItem('token', accessToken);
  }

  // Clears the logged-in state, both in memory and in localStorage.
  function logout() {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  }

  // A simple boolean components can check instead of comparing token
  // to null themselves everywhere.
  const isAuthenticated = token !== null;

  // Everything inside this object becomes available to any component
  // that calls useAuth().
  const value = { token, user, isAuthenticated, login, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}