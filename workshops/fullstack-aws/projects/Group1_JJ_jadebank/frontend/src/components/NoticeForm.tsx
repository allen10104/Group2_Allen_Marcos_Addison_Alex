import { useState } from "react";
import type { FormEvent } from "react";

interface NoticeFormProps {
  onAddNotice: (name: string, message: string) => Promise<void>;
}

function NoticeForm({ onAddNotice }: NoticeFormProps) {
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    if (!name.trim() || !message.trim()) {
      return;
    }

    try {
      setSubmitting(true);

      await onAddNotice(
        name.trim(),
        message.trim()
      );

      setName("");
      setMessage("");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="notice-form" onSubmit={handleSubmit}>
      <h2>Create Notice</h2>

      <label htmlFor="name">Name</label>

      <input
        id="name"
        type="text"
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="Your name"
      />

      <label htmlFor="message">Message</label>

      <textarea
        id="message"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="Write your notice..."
        rows={4}
      />

      <button
        type="submit"
        disabled={submitting}
      >
        {submitting ? "Posting..." : "Post Notice"}
      </button>
    </form>
  );
}

export default NoticeForm;