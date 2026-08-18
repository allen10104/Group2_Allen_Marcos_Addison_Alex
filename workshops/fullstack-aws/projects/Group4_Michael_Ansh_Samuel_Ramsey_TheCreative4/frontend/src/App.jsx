import { useEffect, useState } from 'react'
import { getNotices, createNotice, deleteNotice } from './api'

export default function App() {
  const [notices, setNotices] = useState([])
  const [error, setError] = useState(null)
  const [name, setName] = useState('')
  const [message, setMessage] = useState('')

  const loadNotices = () => {
    getNotices()
      .then((data) => setNotices(data.notices || []))
      .catch((err) => setError(err.message))
  }

  useEffect(() => {
    loadNotices()
  }, [])

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault()
    if (!name.trim() || !message.trim()) return

    try {
      await createNotice({ name, message })
      setName('')
      setMessage('')
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
      <h2>Group4 Michael Ansh Samuel Ramsey The Creative4</h2>
      
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      
      <div style={{ marginBottom: '1.5rem' }}>
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
        <button type="button" onClick={handleSubmit}>Post Notice</button>
      </div>

      {notices.length === 0 && !error && <p>No notices yet.</p>}
      
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {notices.map((n) => (
          <li key={n.id} style={{ 
  border: '1px solid #ddd', 
  borderRadius: 8, 
  padding: '1rem', 
  marginBottom: '0.75rem',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center'
}}>
  <div>
    <strong>{n.name}</strong>
    <p style={{ margin: '0.5rem 0 0' }}>{n.message}</p>
    <span style={{ display: 'block', fontSize: '0.8rem', color: '#666', marginTop: '0.5rem' }}>
      {new Date(n.created_at).toLocaleString()}
    </span>
  </div>

  <button onClick={() => handleDelete(n.id)} style={{ marginLeft: '1rem' }}>
    Delete
  </button>
</li>

        ))}
      </ul>
    </div>
  )
}
