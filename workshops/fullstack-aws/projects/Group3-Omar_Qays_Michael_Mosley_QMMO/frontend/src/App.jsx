import { useEffect, useState } from 'react';
import api from './api/api';
import './App.css';

function App() {
  // Stores all notices returned from the backend
  const [notices, setNotices] = useState([]);

  // Stores the values entered into the notice form
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [priority, setPriority] = useState('Normal');

  // Controls which priority is currently being shown
  const [filter, setFilter] = useState('All');

  // Used to display an error if an API request fails
  const [error, setError] = useState('');

  // Gets all notices from the backend
  const fetchNotices = async () => {
    try {
      const response = await api.get('/notices');
      setNotices(response.data);
      setError('');
    } catch (err) {
      console.error('Error getting notices:', err);
      setError('Could not load notices.');
    }
  };

  // Loads the notice list when the page first opens
  useEffect(() => {
    fetchNotices();
  }, []);

  // Sends a new notice to the backend
  const handleSubmit = async (event) => {
    event.preventDefault();

    // Prevents empty notices from being submitted
    if (!name.trim() || !message.trim()) {
      setError('Please enter your name and a message.');
      return;
    }

    try {
      await api.post('/notices', {
        name,
        message,
        priority,
      });

      // Resets the form after the notice is created
      setName('');
      setMessage('');
      setPriority('Normal');
      setError('');

      // Reloads the notices so the new one appears immediately
      await fetchNotices();
    } catch (err) {
      console.error('Error creating notice:', err);
      setError('Could not create notice.');
    }
  };

  // Deletes the selected notice
  const handleDelete = async (noticeId) => {
    try {
      await api.delete(`/notices/${noticeId}`);
      await fetchNotices();
    } catch (err) {
      console.error('Error deleting notice:', err);
      setError('Could not delete notice.');
    }
  };

  // Only shows notices that match the selected priority filter
  const filteredNotices =
    filter === 'All'
      ? notices
      : notices.filter((notice) => notice.priority === filter);

  return (
    <div className="page">
      <header className="header">
        <h1>Group 3 Notice Board</h1>
        <p>Share updates, reminders, and important announcements.</p>
      </header>

      <main className="notice-board">
        {/* Form used to create a new notice */}
        <section className="form-card">
          <h2>Post a Notice</h2>

          <form onSubmit={handleSubmit} className="notice-form">
            <label htmlFor="name">Name</label>

            <input
              id="name"
              type="text"
              placeholder="Enter your name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />

            <label htmlFor="message">Message</label>

            <textarea
              id="message"
              placeholder="Write your notice"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
            />

            <label htmlFor="priority">Priority</label>

            <select
              id="priority"
              value={priority}
              onChange={(event) => setPriority(event.target.value)}
            >
              <option value="Normal">Normal</option>
              <option value="Important">Important</option>
              <option value="Urgent">Urgent</option>
            </select>

            <button type="submit" className="post-button">
              Post Notice
            </button>
          </form>

          {error && <p className="error">{error}</p>}
        </section>

        <section className="notices-section">
          <div className="notices-heading">
            <h2>Notices</h2>

            {/* Lets the user filter notices by priority */}
            <div className="filters">
              {['All', 'Normal', 'Important', 'Urgent'].map((option) => (
                <button
                  key={option}
                  className={filter === option ? 'filter active' : 'filter'}
                  onClick={() => setFilter(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          {filteredNotices.length === 0 ? (
            <p className="empty-message">
              No notices found for this priority.
            </p>
          ) : (
            <div className="notice-list">
              {filteredNotices.map((notice) => (
                <article className="notice-card" key={notice.id}>
                  <div className="notice-top">
                    <h3>{notice.name}</h3>

                    <span
                      className={`priority-badge ${notice.priority.toLowerCase()}`}
                    >
                      {notice.priority}
                    </span>
                  </div>

                  <p>{notice.message}</p>

                  <button
                    className="delete-button"
                    onClick={() => handleDelete(notice.id)}
                  >
                    Delete
                  </button>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;