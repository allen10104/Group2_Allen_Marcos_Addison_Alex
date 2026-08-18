import { useEffect, useState } from 'react'
import { getNotices, createNotice, deleteNotice, addReaction } from './api'

const REACTIONS = [
  { key: 'thumbs_up', emoji: '👍', label: 'Thumbs up' },
  { key: 'heart', emoji: '❤️', label: 'Heart' },
  { key: 'smile', emoji: '😊', label: 'Smile' },
  { key: 'fire', emoji: '🔥', label: 'Fire' },
]

export default function App() {
  const [notices, setNotices] = useState([])
  const [error, setError] = useState(null)
  const [name, setName] = useState('')
  const [message, setMessage] = useState('')
  const [openReactionPicker, setOpenReactionPicker] = useState(null)

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

  const handleReaction = async (id, reaction) => {
    try {
      const data = await addReaction(id, reaction)
      setNotices((current) => current.map((notice) => (
        notice.id === id ? { ...notice, reactions: data.reactions } : notice
      )))
      setOpenReactionPicker(null)
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
        <button type="submit">Post Notice</button>
      </form>

      {notices.length === 0 && !error && <p>No notices yet.</p>}
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {notices.map((n) => {
          const activeReactions = REACTIONS.filter(({ key }) => (n.reactions?.[key] || 0) > 0)

          return (
            <li key={n.id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', marginBottom: '0.75rem' }}>
              <strong>{n.name}</strong>
              <p style={{ margin: '0.5rem 0 0' }}>{n.message}</p>

              <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.75rem' }}>
                {activeReactions.map(({ key, emoji, label }) => (
                  <button
                    key={key}
                    type="button"
                    aria-label={`Add ${label} reaction`}
                    title={`Add ${label} reaction`}
                    onClick={() => handleReaction(n.id, key)}
                  >
                    {emoji} {n.reactions[key]}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => setOpenReactionPicker((current) => current === n.id ? null : n.id)}
                >
                  React +
                </button>
              </div>

              {openReactionPicker === n.id && (
                <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.5rem' }}>
                  {REACTIONS.map(({ key, emoji, label }) => (
                    <button
                      key={key}
                      type="button"
                      aria-label={`Add ${label} reaction`}
                      title={label}
                      onClick={() => handleReaction(n.id, key)}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              )}

              <button onClick={() => handleDelete(n.id)} style={{ marginTop: '0.75rem' }}>Delete</button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
