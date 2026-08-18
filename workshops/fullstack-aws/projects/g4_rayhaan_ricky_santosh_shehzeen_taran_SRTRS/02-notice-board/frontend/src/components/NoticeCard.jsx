import { useRef } from "react";

// A single sticky note on the board. Behavior depends on the board's
// current mode:
//   "move" -> draggable via pointer events, reports the new position (as a
//             percentage of the board) back to the parent on release
//   "edit" -> clicking opens the edit/delete popup
//   "view" -> inert, just displayed
export default function NoticeCard({ notice, mode, boardRef, onDragEnd, onEditClick }) {
  const cardRef = useRef(null);
  const dragState = useRef(null);

  function handlePointerDown(e) {
    if (mode !== "move") return;
    const board = boardRef.current;
    const card = cardRef.current;
    if (!board || !card) return;

    card.setPointerCapture(e.pointerId);
    const boardRect = board.getBoundingClientRect();
    const cardRect = card.getBoundingClientRect();
    dragState.current = {
      offsetX: e.clientX - cardRect.left,
      offsetY: e.clientY - cardRect.top,
      boardRect,
    };
    card.classList.add("dragging");
  }

  function handlePointerMove(e) {
    if (mode !== "move" || !dragState.current) return;
    const { offsetX, offsetY, boardRect } = dragState.current;
    let xPct = ((e.clientX - boardRect.left - offsetX) / boardRect.width) * 100;
    let yPct = ((e.clientY - boardRect.top - offsetY) / boardRect.height) * 100;
    xPct = Math.max(0, Math.min(90, xPct));
    yPct = Math.max(0, Math.min(88, yPct));
    cardRef.current.style.left = `${xPct}%`;
    cardRef.current.style.top = `${yPct}%`;
    dragState.current.lastX = xPct;
    dragState.current.lastY = yPct;
  }

  function handlePointerUp(e) {
    if (mode !== "move" || !dragState.current) return;
    cardRef.current.releasePointerCapture(e.pointerId);
    cardRef.current.classList.remove("dragging");
    const { lastX, lastY } = dragState.current;
    dragState.current = null;
    if (lastX !== undefined) {
      onDragEnd(notice.id, lastX, lastY);
    }
  }

  return (
    <div
      ref={cardRef}
      className={`notice-card${mode === "move" ? " movable" : ""}${mode === "edit" ? " editable" : ""}`}
      style={{
        left: `${notice.x ?? 4}%`,
        top: `${notice.y ?? 4}%`,
        zIndex: notice.z ?? 1,
        backgroundColor: notice.bg_color || "#fff59d",
        color: notice.text_color || "#1c1e21",
      }}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onClick={() => mode === "edit" && onEditClick(notice)}
    >
      <span className="pin" aria-hidden="true">
        📌
      </span>
      <h3>{notice.title}</h3>
      {notice.content && <p>{notice.content}</p>}
    </div>
  );
}