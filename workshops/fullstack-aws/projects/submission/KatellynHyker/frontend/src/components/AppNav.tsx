/**
 * Shared top-level nav between the Board and People pages.
 */

import { NavLink } from 'react-router-dom'

export function AppNav() {
  return (
    <nav className="app-nav">
      <NavLink to="/board" className={({ isActive }) => (isActive ? 'active' : '')}>
        Board
      </NavLink>
      <NavLink to="/people" className={({ isActive }) => (isActive ? 'active' : '')}>
        People
      </NavLink>
    </nav>
  )
}