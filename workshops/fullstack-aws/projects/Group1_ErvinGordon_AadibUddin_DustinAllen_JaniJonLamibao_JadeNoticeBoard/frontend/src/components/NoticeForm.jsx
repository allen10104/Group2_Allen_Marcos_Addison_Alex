// React hook for local component state.
import { useState } from 'react';
// Supplies the auth token needed to create a notice.
import { useAuth } from '../context/AuthContext';
// API call that posts a new notice to the backend.
import { createNotice } from '../api/notices';
// Component-scoped styles for the form layout below.
import './NoticeForm.css';

// Inline form for composing a new notice. Rendered by NoticeList when the
// "+" toolbar button is toggled on; onCreated hands the saved notice back
// up so the parent can prepend it to the list and hide this form again.
export default function NoticeForm({ onCreated }) {
  // The notice text being composed.
  const [message, setMessage] = useState('');
  // Optional expiry, kept as a string since it's bound to a text/number input.
  const [expiresInDays, setExpiresInDays] = useState('');
  // True while the create request is in flight.
  const [loading, setLoading] = useState(false);
  // Holds the latest submit error message, if any.
  const [error, setError] = useState(null);
  // Auth token required by the create-notice endpoint.
  const { token } = useAuth();

  // Form submit handler: creates the notice via the API and reports the result upward.
  async function handleSubmit(event) {
    // Stop the default full-page-reload form submission.
    event.preventDefault();
    // Clear any previous error before retrying.
    setError(null);
    // Show the loading state while the request is in flight.
    setLoading(true);

    try {
      const created = await createNotice(
        {
          message,
          // New notices always start unpinned; pinning happens later via NoticeList.
          isPinned: false,
          // Empty input means "never expires" -> null; otherwise convert the string to a number.
          expiresInDays: expiresInDays ? Number(expiresInDays) : null,
        },
        token,
      );
      // Hand the newly created notice back to the parent (NoticeList), which
      // both updates its list and closes this form.
      onCreated(created);
    } catch (err) {
      setError(err.message);
    } finally {
      // Always clear loading, whether creation succeeded or failed.
      setLoading(false);
    }
  }

  return (
    // Reuses .notice-card so the form visually matches the notice cards it creates.
    <form className="notice-card notice-form" onSubmit={handleSubmit}>
      <textarea
        className="notice-form__message"
        placeholder="Write your notice..."
        // Controlled textarea: value comes from state and typing updates it.
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        required
        // Focuses the textarea as soon as the form appears, since it just opened.
        autoFocus
      />

      {/* Only rendered when there's an error message to show. */}
      {error && <p className="auth-form__error">{error}</p>}

      <div className="notice-form__footer">
        <label className="notice-form__expiry">
          Expires in
          <input
            // Numeric input; browser enforces >= 0 whole numbers via min/step.
            type="number"
            min="0"
            step="1"
            placeholder="days"
            value={expiresInDays}
            onChange={(event) => setExpiresInDays(event.target.value)}
          />
          days
        </label>
        {/* Disabled while a request is in flight; label reflects loading state. */}
        <button type="submit" disabled={loading}>
          {loading ? 'Saving...' : 'Done'}
        </button>
      </div>
    </form>
  );
}