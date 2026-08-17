import { useState } from 'react';

const CATEGORIES = ['COMPLIANCE', 'SECURITY_ALERT', 'OPERATIONS', 'IT_SYSTEMS', 'HR', 'GENERAL'];
const PRIORITIES = ['LOW', 'NORMAL', 'HIGH', 'URGENT'];

/**
 * Create-notice form.
 *
 * There is no author field — the server takes the author from the JWT. Even if a user
 * added author_employee_id in DevTools, NoticeCreate has no such field and Pydantic
 * discards it. Designed out, not validated away.
 */
export default function NoticeForm({ onCreate, onCancel }) {
  const [form, setForm] = useState({
    title: '', body: '', category: 'GENERAL', priority: 'NORMAL', department: '',
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // One handler for every input, keyed by the name attribute. Beats five near-
  // identical onChange functions.
  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setFieldErrors({});
    try {
      await onCreate({
        ...form,
        // Empty string means bank-wide; the API expects null, not "".
        department: form.department.trim() || null,
      });
      setForm({ title: '', body: '', category: 'GENERAL', priority: 'NORMAL', department: '' });
    } catch (err) {
      // The payoff from the Phase 2 exception handlers: field_errors keyed by field
      // name, so we highlight the exact input that's wrong.
      if (err.fieldErrors) setFieldErrors(err.fieldErrors);
      else if (err.status === 403) setError('Your role does not permit publishing notices.');
      else setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="card notice-form" onSubmit={handleSubmit}>
      <h3>Post a notice</h3>

      <label htmlFor="title">Title</label>
      <input id="title" name="title" value={form.title} maxLength={140}
             onChange={handleChange} required />
      {fieldErrors.title && <span className="field-error">{fieldErrors.title}</span>}

      <label htmlFor="body">Details</label>
      <textarea id="body" name="body" rows={4} value={form.body}
                onChange={handleChange} required />
      {fieldErrors.body && <span className="field-error">{fieldErrors.body}</span>}

      <div className="row">
        <div>
          <label htmlFor="category">Category</label>
          <select id="category" name="category" value={form.category} onChange={handleChange}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="priority">Priority</label>
          <select id="priority" name="priority" value={form.priority} onChange={handleChange}>
            {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="department">Department (blank = bank-wide)</label>
          <input id="department" name="department" value={form.department}
                 onChange={handleChange} placeholder="RETAIL_BANKING" />
        </div>
      </div>

      {error && <div className="alert error">{error}</div>}

      <div className="actions">
        <button type="submit" disabled={submitting}>
          {submitting ? 'Posting…' : 'Post notice'}
        </button>
        <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}
