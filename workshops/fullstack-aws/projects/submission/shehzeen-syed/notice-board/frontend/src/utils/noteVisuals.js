const NOTE_COLORS = ['yellow', 'pink', 'blue', 'green']

// Derived purely from the notice's id (and pinned state) so a note's
// color/rotation/fastener stay fixed across re-renders instead of
// reshuffling every time state updates (e.g. after an edit or a pin toggle).
export function noteVisuals(notice) {
  const id = notice.id
  return {
    color: NOTE_COLORS[id % NOTE_COLORS.length],
    rotation: ((id * 53) % 9) - 4, // -4deg..4deg
    fastener: notice.pinned ? 'tack' : id % 2 === 0 ? 'tack' : 'tape',
  }
}
