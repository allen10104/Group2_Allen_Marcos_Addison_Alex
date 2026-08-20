import { useEffect, useState } from 'react'
import { getNotices, createNotice, deleteNotice, reactToNotice } from './api'

const REACTIONS = [
  { emoji: '🔥', key: 'fire' },
  { emoji: '❤️', key: 'heart' },
  { emoji: '👍', key: 'thumbsup' },
]

const MY_REACTIONS_KEY = 'noticeboard:my-reactions'

function loadMyReactions() {
  try {
    return JSON.parse(localStorage.getItem(MY_REACTIONS_KEY)) || {}
  } catch {
    return {}
  }
}

export default function App() {
  const [notices, setNotices] = useState([])
  const [error, setError] = useState(null)
  const [name, setName] = useState('')
  const [message, setMessage] = useState('')
  const [myReactions, setMyReactions] = useState(loadMyReactions)

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

  const handleReact = async (noticeId, emojiKey) => {
    const alreadyReacted = myReactions[noticeId]?.[emojiKey]
    const action = alreadyReacted ? 'remove' : 'add'
    const delta = alreadyReacted ? -1 : 1

    try {
      await reactToNotice(noticeId, emojiKey, action)

      setNotices((prev) =>
        prev.map((n) =>
          n.id === noticeId
            ? { ...n, reactions: { ...n.reactions, [emojiKey]: (n.reactions?.[emojiKey] || 0) + delta } }
            : n
        )
      )

      const updated = {
        ...myReactions,
        [noticeId]: { ...myReactions[noticeId], [emojiKey]: !alreadyReacted },
      }
      setMyReactions(updated)
      localStorage.setItem(MY_REACTIONS_KEY, JSON.stringify(updated))
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
        {notices.map((n) => (
          <li key={n.id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', marginBottom: '0.75rem' }}>
            <strong>{n.name}</strong>
            <p style={{ margin: '0.5rem 0 0' }}>{n.message}</p>
            <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              {REACTIONS.map(({ emoji, key }) => {
                const active = !!myReactions[n.id]?.[key]
                const count = n.reactions?.[key] || 0
                return (
                  <button
                    key={key}
                    onClick={() => handleReact(n.id, key)}
                    style={{
                      border: active ? '1px solid #666' : '1px solid #ddd',
                      background: active ? '#eee' : 'white',
                      borderRadius: 12,
                      padding: '0.2rem 0.6rem',
                      cursor: 'pointer',
                    }}
                  >
                    {emoji} {count}
                  </button>
                )
              })}
            </div>
            <button onClick={() => handleDelete(n.id)} style={{ marginTop: '0.5rem' }}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  )
}

