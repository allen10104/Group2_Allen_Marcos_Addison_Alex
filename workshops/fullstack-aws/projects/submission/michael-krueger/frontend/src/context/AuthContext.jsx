import { createContext, useCallback, useContext, useEffect, useState } from "react";

import {
  UNAUTHORIZED_EVENT,
  clearToken,
  getToken,
  setToken,
} from "../api/client";
import * as authApi from "../api/auth";
import { userFromToken } from "../utils/decodeToken";

const AuthContext = createContext(null);

// Holds the signed-in user for the whole app.
//
// The token is the single source of truth and the only thing persisted. The
// user object is derived from it by decoding the claims rather than stored
// separately, so the two can never drift apart: there is no way to end up
// with a username from one account and a token from another.
export function AuthProvider({ children }) {
  // Read straight from storage in the initial state rather than in an effect.
  //
  // An effect would run after the first render, so on a hard refresh the app
  // would paint one frame as logged out, and ProtectedRoute would bounce a
  // signed-in user to /login before the token had been read. Doing it here
  // means isAuthenticated is already correct on the very first render.
  //
  // useState takes a function so this runs once on mount rather than on
  // every render.
  const [token, setTokenState] = useState(() => {
    const stored = getToken();

    // userFromToken returns null for an expired or malformed token. Clearing
    // it here rather than keeping it means a stale token from a previous
    // session cannot make the app look signed in while every request fails.
    if (stored && userFromToken(stored) === null) {
      clearToken();
      return null;
    }

    return stored;
  });

  const user = userFromToken(token);

  // The response interceptor throws the token away when the backend answers
  // 401 on a normal request, which happens when it expires mid-session. That
  // code runs outside React and cannot call setState, so it fires an event
  // and this listener brings the React state back in line.
  //
  // Without this the app would keep rendering as signed in against a token
  // that storage no longer has.
  useEffect(() => {
    const handleUnauthorized = () => setTokenState(null);

    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);

    return () => {
      window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    };
  }, []);

  // Logs in and keeps the token.
  //
  // Lets the error through rather than swallowing it, so the page that
  // called this can show what went wrong. A failed login leaves any existing
  // token untouched, which matters when someone re-enters their password on
  // a session that is still valid.
  const login = useCallback(async (username, password) => {
    const accessToken = await authApi.login(username, password);

    setToken(accessToken);
    setTokenState(accessToken);

    return accessToken;
  }, []);

  // Creates an account and signs straight into it.
  //
  // The backend deliberately issues no token at signup, so this makes the
  // follow-up login call itself. Doing it here rather than in the page means
  // a caller cannot forget, and the user lands on the board already signed
  // in instead of being asked to type the same details twice.
  const signup = useCallback(
    async (username, password) => {
      const created = await authApi.signup(username, password);

      await login(username, password);

      return created;
    },
    [login]
  );

  // Clears the token everywhere. Redirecting afterwards is the caller's job,
  // since this has no view of the router.
  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
  }, []);

  const value = {
    token,
    user,
    isAuthenticated: user !== null,
    login,
    signup,
    logout,
  };

  return <AuthContext value={value}>{children}</AuthContext>;
}

// Small hook so components read the context by calling useAuth() instead of
// importing the context object and remembering to pass it to useContext.
//
// The throw turns a missing provider into a clear message at the point of
// use, rather than a confusing "cannot read property of null" further down.
export function useAuth() {
  const context = useContext(AuthContext);

  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
