import { useState } from "react";

const DEFAULT_BG = "#fff59d";
const DEFAULT_TEXT = "#1c1e21";

// Shared popup for both "Post Notice" (mode="create") and the
// "Edit / Delete Notice" click-through (mode="edit").
export default function NoticeModal({ mode, initial, onCancel, onSave, onDelete, saving }) {
  const [title, setTitle] = useState(initial?.title || "");
  const [content, setContent] = useState(initial?.content || "");
  const [bgColor, setBgColor] = useState(initial?.bg_color || DEFAULT_BG);
  const [textColor, setTextColor] = useState(initial?.text_color || DEFAULT_TEXT);
  const [error, setError] = useState("");

  function handleSave() {
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }
    onSave({
      title: title.trim(),
      content: content.trim(),
      bg_color: bgColor,
      text_color: textColor,
    });
  }

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h2>{mode === "create" ? "New Notice" : "Edit Notice"}</h2>

        <label className="field">
          <span>Title *</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={60}
            autoFocus
          />
        </label>

        <label className="field">
          <span>Description (optional)</span>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={4}
            maxLength={280}
          />
        </label>

        <div className="field-row">
          <label className="field">
            <span>Background color</span>
            <input type="color" value={bgColor} onChange={(e) => setBgColor(e.target.value)} />
          </label>
          <label className="field">
            <span>Text color</span>
            <input type="color" value={textColor} onChange={(e) => setTextColor(e.target.value)} />
          </label>
        </div>

        <div className="notice-preview" style={{ backgroundColor: bgColor, color: textColor }}>
          <strong>{title || "Title"}</strong>
          <p>{content || "Description preview…"}</p>
        </div>

        {error && <div className="modal-error">{error}</div>}

        <div className="modal-actions">
          {mode === "edit" && (
            <button type="button" className="danger" onClick={onDelete} disabled={saving}>
              Delete
            </button>
          )}
          <div className="modal-actions-right">
            <button type="button" className="ghost" onClick={onCancel} disabled={saving}>
              Cancel
            </button>
            <button type="button" className="primary" onClick={handleSave} disabled={saving}>
              {saving ? "Saving…" : mode === "create" ? "Post" : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}