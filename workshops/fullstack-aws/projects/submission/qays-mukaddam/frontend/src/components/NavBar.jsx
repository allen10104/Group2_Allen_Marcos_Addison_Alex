// Link renders a clickable route link back to the dashboard.
import { Link } from 'react-router-dom';

// Reads the logged-in user's role and the logout function.
import { useAuth } from '../context/AuthContext';

import Button from './Button';

export default function NavBar() {
  // Pull the decoded user (has .role) and logout() from shared context.
  const { user, logout } = useAuth();

  return (
    // A thin bottom border separates the nav from the page content below.
    <nav className="flex items-center justify-between px-8 py-4 border-b border-white/10">
      {/* Clicking the logo/title always returns to the dashboard. */}
      <Link to="/dashboard" className="text-xl font-semibold text-white">
        Notice<span className="text-accent">Board</span>
      </Link>

      <div className="flex items-center gap-4">
        {/* Shows the current user's role so it's always visible which
            permissions they have (e.g. whether they can post notices). */}
        <span className="text-gray-400 text-sm">
          {user?.role === 'ADMIN' ? 'Admin' : 'Member'}
        </span>
        <Button variant="secondary" onClick={logout}>
          Log Out
        </Button>
      </div>
    </nav>
  );
}