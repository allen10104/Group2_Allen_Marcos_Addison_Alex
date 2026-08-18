// Routes/Route define your app's URL structure — each Route maps a URL
// path to a component. Navigate redirects programmatically (used below
// for the bare "/" path).
import { Routes, Route, Navigate } from 'react-router-dom';

// The login page.
import LoginView from './pages/LoginView';

// The sign-up page (choosing ADMIN or MEMBER).
import SignUpView from './pages/SignUpView';

// The main notice board page (list + admin post form).
import Dashboard from './pages/Dashboard';

// The single-notice page with comments.
import NoticeDetail from './pages/NoticeDetail';

// Wraps any route that should require login, redirecting to /login
// otherwise.
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    // Routes looks at the current URL and renders whichever Route
    // below matches it.
    <Routes>
      {/* Public routes — reachable without being logged in. */}
      <Route path="/login" element={<LoginView />} />
      <Route path="/signup" element={<SignUpView />} />

      {/* Protected route — ProtectedRoute checks isAuthenticated first.
          If not logged in, it redirects to /login instead of ever
          rendering Dashboard. */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      {/* Single-notice view with comments. The :noticeId part is a URL
          parameter — useParams() inside NoticeDetail reads it out, e.g.
          visiting /notices/5 makes noticeId equal "5". Also protected,
          since viewing requires login just like the dashboard does. */}
      <Route
        path="/notices/:noticeId"
        element={
          <ProtectedRoute>
            <NoticeDetail />
          </ProtectedRoute>
        }
      />

      {/* Visiting the bare root URL ("/") just forwards to /dashboard,
          which then either shows the dashboard (if logged in) or
          bounces to /login (if not), via ProtectedRoute. */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;