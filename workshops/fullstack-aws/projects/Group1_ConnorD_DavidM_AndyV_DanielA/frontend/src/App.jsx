import { useEffect, useState } from 'react'
import { getNotices, createNotice, deleteNotice } from './api'

export default function App() {
  const [notices, setNotices] = useState([])
  const [error, setError] = useState(null)
  const [name, setName] = useState('')
  const [message, setMessage] = useState('')
  const [priority, setPriority] = useState('')

  const loadNotices = () => {
    getNotices()
      .then((data) => setNotices(data.notices || []))
      .catch((err) => setError(err.message))
  }

  useEffect(() => {
    loadNotices()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim() || !message.trim()) return

    try {
      await createNotice({ name, message, priority: parseInt(priority, 10) })
      setName('')
      setMessage('')
      setPriority('')
      loadNotices()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteNotice(id)
      loadNotices()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div style={{ maxWidth: 600, margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <h1>Notice Board</h1>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      <form onSubmit={handleSubmit} style={{ marginBottom: '1.5rem' }}>
        <input
          type="text"
          placeholder="Your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ display: 'block', width: '100%', marginBottom: '0.5rem', padding: '0.5rem' }}
        />
        <textarea
          placeholder="Your message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          style={{ display: 'block', width: '100%', marginBottom: '0.5rem', padding: '0.5rem' }}
        />
        <input
          type="number"
          placeholder="Priority (optional)"
          style={{ display: 'block', width: '100%', marginBottom: '0.5rem', padding: '0.5rem' }}
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        />
        <button type="submit">Post Notice</button>
      </form>

      {notices.length === 0 && !error && <p>No notices yet.</p>}
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {notices.map((n) => (
          <li key={n.id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', marginBottom: '0.75rem' }}>
            <strong>{n.name}</strong>
            <p style={{ margin: '0.5rem 0 0' }}>{n.message}</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: '#555' }}>Priority: {n.priority}</p>
            <button onClick={() => handleDelete(n.id)} style={{ marginTop: '0.5rem' }}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
