// Navigate redirects the browser to a different route, like a programmatic
// version of clicking a link.
import { Navigate } from 'react-router-dom';

// Reads the logged-in state set up in AuthContext.jsx.
import { useAuth } from '../context/AuthContext';

// Wraps any page that should require login. If not logged in, redirect
// to /login instead of rendering the page's actual content.
export default function ProtectedRoute({ children }) {
  // Pull isAuthenticated out of the shared auth context.
  const { isAuthenticated } = useAuth();

  // Not logged in — send them to the login page instead.
  // replace means this redirect doesn't add an extra entry to browser
  // history, so the back button doesn't loop back to the blocked page.
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Logged in — render whatever page this component is wrapping.
  return children;
}