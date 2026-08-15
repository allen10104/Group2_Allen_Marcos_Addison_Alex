import { useEffect, useMemo, useState } from 'react'
import { AppNav } from '../components/AppNav'
import { useAuth, getApiErrorMessage } from '../context/AuthContext'
import { followUser, getFollowing, getUsers, unfollowUser } from '../api/users'
import type { User } from '../types/auth'

export function PeoplePage() {
  const { user, logout } = useAuth()

  const [users, setUsers] = useState<User[]>([])
  const [followingIds, setFollowingIds] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set())

  // Load who the current user already follows once, up front, so button
  // state is correct regardless of how the (separately loaded/filtered)
  // user list is sorted or searched.
  useEffect(() => {
    if (!user) return
    let cancelled = false

    getFollowing(user.user_id)
      .then((data) => {
        if (!cancelled) setFollowingIds(new Set(data.map((u) => u.user_id)))
      })
      .catch(() => {
        // Non-fatal -- follow buttons just fall back to "Follow" until a
        // retry succeeds; the user list itself still loads separately.
      })

    return () => {
      cancelled = true
    }
  }, [user])

  // Debounce the search so we're not firing a request on every keystroke.
  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    const timeout = setTimeout(() => {
      getUsers(searchQuery.trim() || undefined)
        .then((data) => {
          if (!cancelled) setUsers(data)
        })
        .catch((err) => {
          if (!cancelled) setError(getApiErrorMessage(err, 'Could not load users.'))
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false)
        })
    }, 300)

    return () => {
      cancelled = true
      clearTimeout(timeout)
    }
  }, [searchQuery])

  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => a.email.localeCompare(b.email)),
    [users],
  )

  async function handleToggleFollow(targetUserId: string, isFollowing: boolean) {
    setError(null)
    setPendingIds((prev) => new Set(prev).add(targetUserId))

    // Optimistic update -- flip the button immediately, revert on failure.
    setFollowingIds((prev) => {
      const next = new Set(prev)
      if (isFollowing) next.delete(targetUserId)
      else next.add(targetUserId)
      return next
    })

    try {
      if (isFollowing) {
        await unfollowUser(targetUserId)
      } else {
        await followUser(targetUserId)
      }
    } catch (err) {
      setFollowingIds((prev) => {
        const next = new Set(prev)
        if (isFollowing) next.add(targetUserId)
        else next.delete(targetUserId)
        return next
      })
      setError(getApiErrorMessage(err, 'Could not update follow status.'))
    } finally {
      setPendingIds((prev) => {
        const next = new Set(prev)
        next.delete(targetUserId)
        return next
      })
    }
  }

  return (
    <div className="board-page">
      <header className="board-header">
        <h1>People</h1>
        <div className="board-header-user">
          <span>{user?.email}</span>
          <button type="button" onClick={logout}>
            Log out
          </button>
        </div>
      </header>

      <AppNav />

      {error && <p className="form-error">{error}</p>}

      <div className="board-toolbar">
        <input
          type="search"
          className="board-search"
          placeholder="Search people by email..."
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
        />
      </div>

      {isLoading ? (
        <p>Loading people...</p>
      ) : sortedUsers.length === 0 ? (
        <p>No people found.</p>
      ) : (
        <ul className="people-list">
          {sortedUsers.map((person) => {
            const isFollowing = followingIds.has(person.user_id)
            const isPending = pendingIds.has(person.user_id)

            return (
              <li key={person.user_id} className="people-card">
                <span className="people-email">{person.email}</span>
                <button
                  type="button"
                  className={isFollowing ? 'notice-action-secondary' : ''}
                  disabled={isPending}
                  onClick={() => handleToggleFollow(person.user_id, isFollowing)}
                >
                  {isPending ? '...' : isFollowing ? 'Following' : 'Follow'}
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}