import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

// Gate for routes that require a signed-in user.
//
// AuthProvider reads the stored token in its initial state rather than in an
// effect, so isAuthenticated is already settled by the time this first runs.
// That is what stops a signed-in user being bounced to /login for one frame
// on a hard refresh.
//
// replace rather than a normal navigate, so the protected page does not go
// into the history stack. Without it, pressing Back from /login would return
// to the page that just redirected, and bounce straight back again.
//
// The location is passed along in state so the login page can send the user
// where they were originally heading once they are signed in.
export default function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
