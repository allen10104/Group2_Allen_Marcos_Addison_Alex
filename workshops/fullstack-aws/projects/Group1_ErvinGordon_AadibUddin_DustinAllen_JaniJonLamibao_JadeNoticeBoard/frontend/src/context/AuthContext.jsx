// React hooks for creating/reading context and managing local component state.
import { createContext, useContext, useState } from 'react';
// The auth API functions (login/register HTTP calls) this context wraps.
import * as authApi from '../api/auth';

// The context object itself; null default means "no provider mounted" (see useAuth below).
const AuthContext = createContext(null);

// Wraps the app (or a subtree) and provides auth state/actions to everything inside it.
export function AuthProvider({ children }) {

    // Auth token, initialized lazily from localStorage so a page refresh keeps the user logged in.
    const [token, setToken] = useState(() => localStorage.getItem('token'));
    // Logged-in user's email, persisted the same way as the token.
    const [email, setEmail] = useState(() => localStorage.getItem('email'));

    // Logs the user in: calls the API, then persists and stores the resulting session.
    async function login(emailInput, password) {
    // Hit the backend login endpoint via the auth API module.
    const data = await authApi.login(emailInput, password);
    // Persist so a refresh doesn't log the user out.
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('email', emailInput);
    // Update state -> React re-renders anything reading this context.
    setToken(data.access_token);
    setEmail(emailInput);
}

    // Registers a new account; doesn't log the user in or touch state/storage itself.
    async function register(emailInput, password) {

    return authApi.register(emailInput, password);
    }

    // Clears the session: wipes storage and resets state, logging the user out everywhere this context is used.
    function logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('email');
        setToken(null);
        setEmail(null);
    }

    // The object exposed to consumers via useAuth(): current session data plus the auth actions.
    const value = {
        token,
        email,
        // Derived flag: true whenever a token is present.
        isAuthenticated: Boolean(token),
        login,
        register,
        logout,
    };

    // Provide the value to all descendants; children render as normal beneath it.
    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Convenience hook so components can do `const { token, login } = useAuth()`
// instead of importing AuthContext and calling useContext directly.
// Returns null if called outside an AuthProvider, since the context default is null.
export function useAuth() {
  return useContext(AuthContext);
}
