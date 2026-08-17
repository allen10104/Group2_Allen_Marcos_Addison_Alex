// React hook for local component state.
import { useState } from 'react';
// Pulls the login action (and session state) out of AuthContext.
import { useAuth } from '../context/AuthContext';

// Shared styles for auth forms (login/register look the same).
import './AuthForm.css';
// A self-contained login form: owns its own input/loading/error state
// and delegates the actual authentication to AuthContext's login().
export default function LoginForm() {
    // Controlled-input state for the email field.
    const [email, setEmail] = useState('');
    // Controlled-input state for the password field.
    const [password, setPassword] = useState('');

    // Tracks whether a login request is in flight, to disable the button and show feedback.
    const [loading, setLoading] = useState(false);
    // Holds the latest login error message, if any, for display.
    const [error, setError] = useState(null);

    // Grab just the login function from the auth context; token/email aren't needed here.
    const { login } = useAuth();
    // Form submit handler: performs the login request and manages loading/error UI state.
    async function handleSubmit(event) {
        // Stop the browser's default full-page-reload form submission.
        event.preventDefault();

        // Clear any previous error before retrying.
        setError(null);
        // Show the loading state while the request is in flight.
        setLoading(true);

        try {
            // Delegate to AuthContext, which calls the API and persists the session on success.
            await login(email, password);
        } catch (err) {
            // Show the backend's error message if available, otherwise a generic fallback.
            setError(err.message || 'Failed to login');
        } finally {
            // Always clear the loading state, whether login succeeded or failed.
            setLoading(false);
        }
    }
    return (
    // Wire the form's submit event to handleSubmit.
    <form onSubmit={handleSubmit} className="auth-form">
      <label>
        Email
        <input
          type="email"
          // Controlled input: value comes from state...
          value={email}
          // ...and typing updates that state, keeping React and the DOM in sync.
          onChange={(event) => setEmail(event.target.value)}
          // Browser-native required-field validation.
          required
        />
      </label>

      <label>
        Password
        <input
          // Masks the input characters.
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
      </label>

      {/* Only rendered when there's an error message to show. */}
      {error && <p className="auth-form__error">{error}</p>}

      {/* Disabled while a request is in flight, so the user can't double-submit; label reflects loading state. */}
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Log In'}
      </button>
    </form>
  );
}