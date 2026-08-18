import { useEffect, useRef, useState } from "react";
import NoticeCard from "./components/NoticeCard.jsx";
import NoticeModal from "./components/NoticeModal.jsx";
import "./app.css";

// Injected at build time by Vite. Set in frontend/.env (local) or as a
// GitHub Actions secret VITE_API_URL (CI). Must NOT have a trailing slash.
const API_URL = import.meta.env.VITE_API_URL || "";
const MAX_NOTICES = 15;

export default function App() {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [mode, setMode] = useState("move"); // "move" (default, draggable) | "edit"
  const [showCreate, setShowCreate] = useState(false);
  const [editingNotice, setEditingNotice] = useState(null);
  const [saving, setSaving] = useState(false);
  const boardRef = useRef(null);

  async function loadNotices() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/notices`);
      if (!res.ok) throw new Error(`GET /notices failed: ${res.status}`);
      const data = await res.json();
      setNotices(Array.isArray(data) ? data : data.notices || []);
    } catch (err) {
      console.error(err);
      setError("Could not load notices. Is the API reachable?");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadNotices();
  }, []);

  function toggleEditMode() {
    setMode((current) => (current === "edit" ? "move" : "edit"));
  }

  async function handleCreate(data) {
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/notices`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `POST /notices failed: ${res.status}`);
      }
      setShowCreate(false);
      await loadNotices();
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not post the notice.");
    } finally {
      setSaving(false);
    }
  }

  async function handleEditSave(data) {
    if (!editingNotice) return;
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/notices/${editingNotice.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error(`PUT /notices failed: ${res.status}`);
      setEditingNotice(null);
      await loadNotices();
    } catch (err) {
      console.error(err);
      setError("Could not save changes.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!editingNotice) return;
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/notices/${editingNotice.id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`DELETE /notices failed: ${res.status}`);
      const deletedId = editingNotice.id;
      setEditingNotice(null);
      setNotices((prev) => prev.filter((n) => n.id !== deletedId));
    } catch (err) {
      console.error(err);
      setError("Could not delete the notice.");
    } finally {
      setSaving(false);
    }
  }

  // Optimistically move the note locally, bump it to the front (highest z),
  // then persist the new position/z to the backend.
  function handleDragEnd(id, x, y) {
    setNotices((prev) => {
      const maxZ = prev.reduce((m, n) => Math.max(m, n.z || 0), 0);
      const newZ = maxZ + 1;

      fetch(`${API_URL}/notices/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ x, y, z: newZ }),
      }).catch((err) => {
        console.error(err);
        setError("Could not save the new position.");
      });

      return prev.map((n) => (n.id === id ? { ...n, x, y, z: newZ } : n));
    });
  }

  const boardFull = notices.length >= MAX_NOTICES;

  return (
    <div className="page">
      <header className="toolbar">
        <h1>🗒 SRTRS Notice Board</h1>
        <div className="toolbar-buttons">
          <button
            className="primary"
            onClick={() => setShowCreate(true)}
            disabled={boardFull}
            title={boardFull ? `Board is full (${MAX_NOTICES}/${MAX_NOTICES})` : "Post a new notice"}
          >
            Post Notice
          </button>
          <button
            className={mode === "edit" ? "active" : ""}
            onClick={toggleEditMode}
            disabled={notices.length === 0}
          >
            Edit / Delete Notice
          </button>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}

      <div className="board-frame">
        <div className="board" ref={boardRef}>
          {loading ? (
            <p className="empty">Loading notices…</p>
          ) : (
            notices.map((notice) => (
              <NoticeCard
                key={notice.id}
                notice={notice}
                mode={mode}
                boardRef={boardRef}
                onDragEnd={handleDragEnd}
                onEditClick={setEditingNotice}
              />
            ))
          )}
        </div>
      </div>

      {showCreate && (
        <NoticeModal
          mode="create"
          saving={saving}
          onCancel={() => setShowCreate(false)}
          onSave={handleCreate}
        />
      )}

      {editingNotice && (
        <NoticeModal
          mode="edit"
          initial={editingNotice}
          saving={saving}
          onCancel={() => setEditingNotice(null)}
          onSave={handleEditSave}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}