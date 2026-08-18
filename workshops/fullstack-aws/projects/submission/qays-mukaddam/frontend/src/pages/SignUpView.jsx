// useState holds form fields, mode, error, loading, and the newly
// created org code (shown once after creating an organization).
import { useState } from 'react';

import { useNavigate, Link } from 'react-router-dom';

// createOrganization and joinOrganization call the two new backend
// endpoints. loginUser is used afterward to auto-log the new account in.
import { createOrganization, joinOrganization, loginUser } from '../api/api';

import { useAuth } from '../context/AuthContext';
import Card from '../components/Card';
import Button from '../components/Button';

export default function SignUpView() {
  // "create" = becoming an ADMIN of a brand-new organization.
  // "join" = becoming a MEMBER of an existing organization via its code.
  const [mode, setMode] = useState('create');

  // Shared fields.
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Only used in "create" mode.
  const [organizationName, setOrganizationName] = useState('');
  // Only used in "join" mode.
  const [orgCode, setOrgCode] = useState('');

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Holds the org_code returned after successfully creating an
  // organization. While this is set, we show a "save this code" screen
  // INSTEAD of the form, since the code is only ever shown once.
  const [createdOrgCode, setCreatedOrgCode] = useState(null);
  // Holds the org name too, just for display on that same screen.
  const [createdOrgName, setCreatedOrgName] = useState('');

  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'create') {
        // Creates the org and registers the founding admin in one call.
        const result = await createOrganization(organizationName, username, password);
        // Don't log in yet — show the org code first, since this is
        // the only chance the user gets to see/save it.
        setCreatedOrgCode(result.org_code);
        setCreatedOrgName(result.organization_name);
      } else {
        // Joining requires an existing org's code.
        await joinOrganization(orgCode, username, password);
        // No code to show here — go straight to logging in.
        const response = await loginUser(username, password);
        login(response.access_token);
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // Called when the admin clicks "Continue" on the org-code screen,
  // after they've saved/copied the code.
  async function handleContinueAfterCreate() {
    setLoading(true);
    try {
      const response = await loginUser(username, password);
      login(response.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // Copies the org code to the clipboard with one click.
  function handleCopyCode() {
    navigator.clipboard.writeText(createdOrgCode);
  }

  // If an org was just created, show the "save this code" screen
  // instead of the normal sign-up form.
  if (createdOrgCode) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <Card className="w-full max-w-sm text-center">
          <h1 className="text-2xl font-semibold text-white mb-2">
            {createdOrgName} is ready!
          </h1>
          <p className="text-gray-400 text-sm mb-6">
            Share this code with anyone who should join your board as a
            member. Save it now — this is the only time it's shown.
          </p>

          <div className="bg-white/5 border border-accent/40 rounded-lg py-4 mb-4">
            <span className="text-3xl font-mono font-bold tracking-widest bg-gradient-to-r from-accent to-accent-2 bg-clip-text text-transparent">
              {createdOrgCode}
            </span>
          </div>

          <div className="flex gap-3">
            <Button variant="secondary" onClick={handleCopyCode}>
              Copy Code
            </Button>
            <Button onClick={handleContinueAfterCreate} disabled={loading}>
              {loading ? 'Continuing...' : 'Continue'}
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <h1 className="text-2xl font-semibold text-white mb-6 text-center">
          Create an account
        </h1>

        {/* Mode picker: two toggle buttons, same visual pattern as the
            old ADMIN/MEMBER role picker. */}
        <div className="flex gap-3 mb-6">
          <button
            type="button"
            onClick={() => setMode('create')}
            className={`flex-1 px-4 py-2 rounded-lg border text-sm transition-all ${
              mode === 'create'
                ? 'border-accent-2 bg-accent-2/10 text-accent-2'
                : 'border-white/10 text-gray-400'
            }`}
          >
            Create Organization
          </button>
          <button
            type="button"
            onClick={() => setMode('join')}
            className={`flex-1 px-4 py-2 rounded-lg border text-sm transition-all ${
              mode === 'join'
                ? 'border-accent bg-accent/10 text-accent'
                : 'border-white/10 text-gray-400'
            }`}
          >
            Join Organization
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Only shown in "create" mode. */}
          {mode === 'create' && (
            <input
              type="text"
              placeholder="Organization name"
              value={organizationName}
              onChange={(e) => setOrganizationName(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
            />
          )}

          {/* Only shown in "join" mode. */}
          {mode === 'join' && (
            <input
              type="text"
              placeholder="Organization code"
              value={orgCode}
              onChange={(e) => setOrgCode(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent"
            />
          )}

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

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <Button type="submit" disabled={loading}>
            {loading ? 'Please wait...' : mode === 'create' ? 'Create Organization' : 'Join Organization'}
          </Button>
        </form>

        <p className="text-gray-400 text-sm text-center mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}