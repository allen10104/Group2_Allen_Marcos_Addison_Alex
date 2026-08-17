import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Navbar.css'

export function Navbar() {
  const { user, isAuthenticated, isLoading, logout } = useAuth()

  return (
    <header className="navbar">
      <div className="navbar__inner">
        <Link to="/" className="navbar__brand">
          The Community Cork
        </Link>

        <nav className="navbar__links">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? 'navbar__link navbar__link--active' : 'navbar__link'
            }
          >
            Notices
          </NavLink>

          {isLoading ? (
            <span className="navbar__status">Loading…</span>
          ) : isAuthenticated && user ? (
            <div className="navbar__user">
              <span className="navbar__status">
                {user.name}
                {user.is_admin ? ' (Admin)' : ''}
              </span>
              <button type="button" className="navbar__button" onClick={logout}>
                Log out
              </button>
            </div>
          ) : (
            <NavLink
              to="/login"
              className={({ isActive }) =>
                isActive
                  ? 'navbar__button navbar__button--primary navbar__link--active'
                  : 'navbar__button navbar__button--primary'
              }
            >
              Log in
            </NavLink>
          )}
        </nav>
      </div>
    </header>
  )
}
