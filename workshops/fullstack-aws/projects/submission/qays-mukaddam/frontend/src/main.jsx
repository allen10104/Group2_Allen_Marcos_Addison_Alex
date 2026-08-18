// StrictMode helps catch potential bugs during development.
import { StrictMode } from 'react'

// createRoot is how React 18+ mounts your app onto the actual HTML page.
import { createRoot } from 'react-dom/client'

// BrowserRouter enables React Router's URL-based navigation for the
// whole app.
import { BrowserRouter } from 'react-router-dom'

// Your Tailwind + custom theme styles.
import './index.css'

// The top-level component holding all your routes.
import App from './App.jsx'

// Makes login state (token, user, login/logout) available to every
// component in the app.
import { AuthProvider } from './context/AuthContext'

// Mount the app onto the <div id="root"> in index.html.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* BrowserRouter goes outside AuthProvider so routing works
        everywhere, including on the login page itself. */}
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)