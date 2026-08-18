// React's dev-only wrapper that double-invokes renders/effects to surface side-effect bugs.
import { StrictMode } from 'react'
// The React 18+ root API used to mount the app into the DOM.
import { createRoot } from 'react-dom/client'
// Global styles/design tokens, applied before anything renders.
import './index.css'
// The root application component.
import App from './App.jsx'
// Provides auth state/actions (token, login, logout, etc.) to the whole app via context.
import { AuthProvider } from './context/AuthContext.jsx'

// Find the <div id="root"> from index.html and mount the React tree into it.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* Wraps App so every component underneath can call useAuth(). */}
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>,
)
