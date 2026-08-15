import type { Notice } from "../App";

interface NoticeListProps {
  notices: Notice[];
  onDeleteNotice: (id: number) => Promise<void>;
}

function NoticeList({
  notices,
  onDeleteNotice,
}: NoticeListProps) {
  if (notices.length === 0) {
    return (
      <section className="notice-list">
        <h2>Notices</h2>
        <p className="empty-message">
          No notices have been posted yet.
        </p>
      </section>
    );
  }

  return (
    <section className="notice-list">
      <h2>Notices</h2>

      {notices.map((notice) => (
        <article
          className="notice-card"
          key={notice.id}
        >
          <div className="notice-content">
            <h3>{notice.name}</h3>
            <p>{notice.message}</p>
          </div>

          <button
            className="delete-button"
            onClick={() => onDeleteNotice(notice.id)}
          >
            Delete
          </button>
        </article>
      ))}
    </section>
  );
}

export default NoticeList;