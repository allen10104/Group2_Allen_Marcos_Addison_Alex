import { useState } from 'react'

export default function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('')
  const [field, setField] = useState('name')

  const handleQueryChange = (e) => {
    const value = e.target.value
    setQuery(value)
    onSearch(value, field)
  }

  const handleFieldChange = (e) => {
    const value = e.target.value
    setField(value)
    onSearch(query, value)
  }

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <input
        type="text"
        placeholder="Search notices..."
        value={query}
        onChange={handleQueryChange}
        style={{ display: 'block', width: '100%', marginBottom: '0.5rem', padding: '0.5rem' }}
      />
      <div style={{ display: 'flex', gap: '1rem' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <input
            type="radio"
            name="searchField"
            value="name"
            checked={field === 'name'}
            onChange={handleFieldChange}
          />
          Name
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <input
            type="radio"
            name="searchField"
            value="message"
            checked={field === 'message'}
            onChange={handleFieldChange}
          />
          Message
        </label>
      </div>
    </div>
  )
}
