// React hook for local component state.
import { useState } from 'react';
// Pulls the register action out of AuthContext.
import { useAuth } from '../context/AuthContext';
// Shared styles for auth forms (login/register look the same).
import './AuthForm.css';

// A self-contained registration form. Note that, unlike login, a successful
// registration does NOT log the user in — it just reports success and lets
// the caller (via onSuccess) decide what to do next, e.g. switch to the login form.
export default function RegisterForm({ onSuccess }) {
  // Controlled-input state for the email field.
  const [email, setEmail] = useState('');
  // Controlled-input state for the password field.
  const [password, setPassword] = useState('');
  // Tracks whether a register request is in flight.
  const [loading, setLoading] = useState(false);
  // Holds the latest registration error message, if any.
  const [error, setError] = useState(null);
  // Flips to true once registration succeeds, to swap the form out for a success message.
  const [success, setSuccess] = useState(false);

  // Grab just the register function from the auth context.
  const { register } = useAuth();

  // Form submit handler: calls register(), then reports success or captures the error.
  async function handleSubmit(event) {
    // Stop the default full-page-reload form submission.
    event.preventDefault();
    // Clear any previous error before retrying.
    setError(null);
    // Show the loading state while the request is in flight.
    setLoading(true);

    try {
      // Create the account via the API; this does not establish a session.
      await register(email, password);
      // Switch the UI to the success message below.
      setSuccess(true);

      // Notify the parent component, if it passed a callback, so it can e.g. redirect to login.
      onSuccess?.(email);
    } catch (err) {
      // Surface the backend's error message directly.
      setError(err.message);
    } finally {
      // Always clear loading, whether registration succeeded or failed.
      setLoading(false);
    }
  }

  // Once registered, replace the form entirely with a confirmation message.
  if (success) {
    return <p className="auth-form__success">Account created — you can log in now.</p>;
  }

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <label>
        Email
        <input
          type="email"
          // Controlled input: value comes from state and changes flow back into it.
          value={email}
          onChange={(event) => setEmail(event.target.value)}
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

      {/* Disabled while a request is in flight; label reflects loading state. */}
      <button type="submit" disabled={loading}>
        {loading ? 'Creating account...' : 'Register'}
      </button>
    </form>
  );
}