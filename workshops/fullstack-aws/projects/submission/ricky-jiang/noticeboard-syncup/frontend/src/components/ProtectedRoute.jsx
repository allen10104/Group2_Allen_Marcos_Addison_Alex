// This file defines a ProtectedRoute component that restricts access to certain routes based on user authentication and role.
// It uses the useAuth hook to access the current user's authentication state and role, and redirects unauthorized users to 
// the login page or home page as appropriate.

import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute({ role, children }) {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to="/" replace />;

  return children;
}