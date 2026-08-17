import { createContext, useContext, useState, useCallback } from 'react';
import * as api from '../api/client';

/**
 * Holds "who is logged in" for the whole app.
 *
 * Context instead of prop-drilling: the header needs the name, the controls need
 * can_publish, the card needs it too. Threading that through four layers is how
 * prop-drilling starts. Redux would be overkill — this is one object and two functions.
 */
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Lazy initialiser reads localStorage ONCE on first render, not on every render,
  // so a page refresh doesn't log the user out.
  const [user, setUser] = useState(() => api.tokenStore.getUser());
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const signIn = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      setUser(await api.login(username, password));
      return true;
    } catch (e) {
      // The backend deliberately returns the same message for unknown-user and
      // wrong-password. Showing it verbatim preserves that; "improving" it
      // client-side would undo the anti-enumeration work.
      setError(e.message || 'Login failed');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const signOut = useCallback(() => {
    api.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, error, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Throwing here catches the classic mistake of using this outside the provider —
 *  a clear message beats "cannot destructure property 'user' of null". */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
