// React hook for local component state (used for the login/register toggle).
import { useState } from 'react'
// Hook for reading session state (isAuthenticated, email) and the logout action.
import { useAuth } from './context/AuthContext'
// Form shown when the user is logging into an existing account.
import LoginForm from './components/LoginForm'
// Form shown when the user is creating a new account.
import RegisterForm from './components/RegisterForm'
// Component-scoped styles for the header/layout below.
import './App.css'

// The public notice board, shown to everyone regardless of auth state.
import NoticeList from './components/NoticeList'
// Root component: renders the header and the notice list, then one of three
// views below depending on auth state and whether the user has chosen to
// register instead of log in.
function App() {
  // Pull what this component needs out of the auth context.
  const { isAuthenticated, email, logout } = useAuth()

  // A simple boolean flag: are we showing the register form instead of login?
  const [showRegister, setShowRegister] = useState(false)

  return (
    <div className="app">
      {/* Static branding header, shown regardless of auth state. */}
      <header className="app-header">
        <span className="app-header__badge" />
        <div className="app-header__text">
          <h1>
            RED-<span>E</span>-LERT
          </h1>
          <p>Stay in the loop. Or don't. We'll notice.</p>
        </div>
      </header>
      {/* Notices are public: rendered for logged-in and logged-out visitors alike. */}
      <NoticeList />
      {/* Nested ternary: three real states -- logged in, showing register,
          or showing login. Read it top to bottom: "if X, show A, else if Y,
          show B, else show C." */}
      {isAuthenticated ? (
        // Logged-in view: greet the user by email and offer a logout button.
        <div>
          <p>Logged in as {email}</p>
          {/* Calls logout() from AuthContext, which clears storage/state and re-renders this view. */}
          <button onClick={logout}>Log Out</button>
        </div>
      ) : showRegister ? (
        // <>...</> is a "Fragment" -- lets you return two sibling elements
        // (the form + the toggle text) without wrapping them in an extra <div>
        // that would just add unwanted spacing/structure.
        <>
          {/* onSuccess flips showRegister back to false, switching to the login form
              once the account is created (registering doesn't log the user in). */}
          <RegisterForm onSuccess={() => setShowRegister(false)} />
          <p className="auth-toggle">
            Already have an account?{' '}
            {/* type="button" so this doesn't trigger any surrounding form's submit. */}
            <button type="button" onClick={() => setShowRegister(false)}>
              Log in
            </button>
          </p>
        </>
      ) : (
        // Default view: login form plus a toggle to switch to registering.
        <>
          <LoginForm />
          <p className="auth-toggle">
            Need an account?{' '}
            <button type="button" onClick={() => setShowRegister(true)}>
              Register
            </button>
          </p>
        </>
      )}
    </div>
  )
}

export default App