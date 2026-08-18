// THis file contains the context for authentication, including user state and login/logout functions.

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import * as api from "../api";
import { clearTokens, setTokens } from "../api/client";

const AuthContext = createContext(null);

// Decodes a JWT token and returns its payload as a JavaScript object.
function decodeJwt(token) {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return null;
  }
}
// Loads the user information from local storage by decoding the access token.
function loadUserFromStorage() {
  const accessToken = localStorage.getItem("accessToken");
  if (!accessToken) return null;
  const payload = decodeJwt(accessToken);
  if (!payload) return null;
  return { id: payload.sub, role: payload.role };
}
// Provides the authentication context to its children components, allowing them to access user state and authentication functions.
export function AuthProvider({ children }) {
  const [user, setUser] = useState(loadUserFromStorage);

  // The JWT only ever gives us { id, role } synchronously (decoded from the token).
  // Email isn't in the token at all, so whenever we know someone's logged in but
  // don't yet have their email, fetch the full profile from /auth/me and merge it
  // into user state. The `!user.email` guard stops this from re-firing forever once
  // the email is actually loaded (merging it changes `user`, which would otherwise
  // re-trigger this effect since `user` is a dependency below).
  useEffect(() => {
    if (user && !user.email) {
      api.getMe().then((profile) => {
        setUser((prev) => (prev ? { ...prev, email: profile.email } : prev));
      });
    }
  }, [user]);

  const value = useMemo(
    () => ({
      user,
      isManager: user?.role === "MANAGER",
      isEmployee: user?.role === "EMPLOYEE",
      async login(email, password) {
        const tokens = await api.login(email, password);
        setTokens(tokens);
        setUser(loadUserFromStorage());
      },
      logout() {
        clearTokens();
        setUser(null);
      },
    }),
    [user]
  );
  // The AuthProvider component wraps its children with the AuthContext.Provider, passing down the authentication state and functions as the context value.
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
// Custom hook to access the authentication context, providing an easy way for components to use authentication state and functions.
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}