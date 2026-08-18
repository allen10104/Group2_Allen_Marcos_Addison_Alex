// useState holds the form's input values and error/loading state.
import { useState } from 'react';

// useNavigate redirects after a successful login. Link renders a
// clickable route link (to the sign-up page).
import { useNavigate, Link } from 'react-router-dom';

// The API function that actually calls POST /login.
import { loginUser } from '../api/api';

// login() from AuthContext stores the token once we have it.
import { useAuth } from '../context/AuthContext';

// Reusable glass-panel container.
import Card from '../components/Card';

// Reusable gradient button.
import Button from '../components/Button';

// A plain data array instead of hardcoding six near-identical blocks of
// JSX — keeps the FAQ content and its markup separate, so adding or
// editing a question is a one-line change, not a copy-pasted block.
const faqItems = [
  {
    // Emoji shown next to this FAQ card.
    icon: '📌',
    // The question text.
    question: 'What is Post Its?',
    // The answer text.
    answer: 'A modern, role-based notice board built for your organization — announcements go up instantly and everyone sees them in real time, no more missed emails or paper flyers.',
  },
  {
    icon: '🛡️',
    question: 'Who can post notices?',
    answer: 'Only your organization\'s admins can post official notices. That keeps the board trustworthy and free of clutter, while every member can still engage with what\'s posted.',
  },
  {
    icon: '💬',
    question: 'Can I comment and engage?',
    answer: 'Yes — every member can comment on any notice, and like both notices and comments. It\'s not just a board, it\'s a conversation.',
  },
  {
    icon: '🔒',
    question: 'Is it secure?',
    answer: 'Built with JWT-based authentication and role-based access control, so only the right people can post, delete, or moderate — your account and data stay protected.',
  },
  {
    icon: '📊',
    question: 'What makes it stand out?',
    answer: 'Live view counts and like counts show you exactly what\'s resonating with your organization — something a static bulletin board or group chat can\'t give you.',
  },
  {
    icon: '⚡',
    question: 'How do I get started?',
    answer: 'Sign up above as either an Organization Admin or Member, and you\'re in — no setup, no waiting, no paperwork.',
  },
  // Closes the faqItems array.
];

export default function LoginView() {
  // Controlled inputs — React state is the single source of truth for
  // what's typed in each field.
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Holds an error message to show if login fails.
  const [error, setError] = useState('');

  // Disables the button and shows "Signing in..." while the request runs.
  const [loading, setLoading] = useState(false);

  // Pull login() out of the shared auth context.
  const { login } = useAuth();

  // For redirecting to the dashboard after a successful login.
  const navigate = useNavigate();

  // Runs when the form is submitted.
  async function handleSubmit(e) {
    // Stops the browser's default full-page-reload form submission.
    e.preventDefault();
    // Clear any previous error before trying again.
    setError('');
    setLoading(true);

    try {
      // Call the backend's /login endpoint.
      const response = await loginUser(username, password);
      // Store the returned JWT in context + localStorage.
      login(response.access_token);
      // Send the user to the dashboard now that they're logged in.
      navigate('/dashboard');
    } catch (err) {
      // authenticate_user failures come through here (wrong username/password).
      setError(err.message);
    } finally {
      // Runs whether it succeeded or failed, to always re-enable the button.
      setLoading(false);
    }
  }

  return (
    // No min-h-screen flex-centering wrapper around the WHOLE page
    // anymore — that would trap everything to exactly one screen's
    // height. Instead, only the hero section below gets that treatment,
    // so the FAQ section can flow naturally beneath it and the page scrolls.
    <div>
      {/* Fixed to the top-right corner of the viewport at all times,
          even while scrolling down into the FAQ section. z-10 keeps it
          above the content stacking beneath it. */}
      <div className="fixed top-6 right-6 flex items-center gap-2 z-10">
        {/* Placeholder icon standing in for a logo image. */}
        <span className="text-2xl">📌</span>
        {/* bg-clip-text + text-transparent makes the text itself display
            the gradient, matching the button color scheme. */}
        <span className="text-xl font-bold bg-gradient-to-r from-accent to-accent-2 bg-clip-text text-transparent">
          POST ITS
        </span>
      </div>

      {/* Hero section: takes up exactly one screen's height (min-h-screen)
          and centers the login card inside it both ways (flex items-center
          justify-center). */}
      <div className="min-h-screen flex items-center justify-center px-4">
        <Card className="w-full max-w-sm">
          <h1 className="text-2xl font-semibold text-white mb-6 text-center">
            Sign in to the Notice Board
          </h1>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {/* Controlled input: value comes from state, onChange updates it. */}
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
            />

            {/* Only renders if there's actually an error message to show. */}
            {error && <p className="text-red-400 text-sm">{error}</p>}

            <Button type="submit" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <p className="text-gray-400 text-sm text-center mt-4">
            Don't have an account?{' '}
            <Link to="/signup" className="text-accent hover:underline">
              Sign up
            </Link>
          </p>
        </Card>
      </div>

      {/* FAQ / features section, sitting below the hero in normal page
          flow — the page scrolls down to reach it. max-w-4xl + mx-auto
          keeps it centered and readable on wide screens. */}
      <div className="max-w-4xl mx-auto px-4 pb-20">
        <h2 className="text-3xl font-semibold text-white text-center mb-2">
          Why Post Its?
        </h2>
        <p className="text-gray-400 text-center mb-10">
          Everything you need to keep your organization in the loop.
        </p>

        {/* Responsive grid: 1 column on small screens (grid-cols-1), 2
            columns on medium screens and up (md:grid-cols-2). */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* .map turns each object in faqItems into one Card, so adding
              a 7th question later needs zero new markup, just a new
              object in the array above. key={item.question} helps React
              track each card efficiently across re-renders. */}
          {faqItems.map((item) => (
            <Card key={item.question} className="text-left">
              <div className="flex items-start gap-4">
                <span className="text-3xl">{item.icon}</span>
                <div>
                  <h3 className="text-white font-semibold mb-1">{item.question}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">{item.answer}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}