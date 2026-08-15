import { useEffect, useState } from "react";
import NoticeForm from "./components/NoticeForm";
import NoticeList from "./components/NoticeList";
import "./App.css";

export interface Notice {
  id: number;
  name: string;
  message: string;
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchNotices = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(`${API_URL}/notices`);

      if (!response.ok) {
        throw new Error("Failed to fetch notices");
      }

      const data = await response.json();
      setNotices(data);
    } catch (error) {
      console.error(error);
      setError("Unable to load notices.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotices();
  }, []);

  const addNotice = async (name: string, message: string) => {
    try {
      const response = await fetch(`${API_URL}/notices`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          message,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create notice");
      }

      const newNotice = await response.json();

      setNotices((currentNotices) => [
        ...currentNotices,
        newNotice,
      ]);
    } catch (error) {
      console.error(error);
      setError("Unable to create notice.");
    }
  };

  const deleteNotice = async (id: number) => {
    try {
      const response = await fetch(`${API_URL}/notices/${id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete notice");
      }

      setNotices((currentNotices) =>
        currentNotices.filter((notice) => notice.id !== id)
      );
    } catch (error) {
      console.error(error);
      setError("Unable to delete notice.");
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Notice Board</h1>
        <p>Share important announcements and updates.</p>
      </header>

      <main className="main-content">
        <NoticeForm onAddNotice={addNotice} />

        {error && <p className="error-message">{error}</p>}

        {loading ? (
          <p className="loading-message">Loading notices...</p>
        ) : (
          <NoticeList
            notices={notices}
            onDeleteNotice={deleteNotice}
          />
        )}
      </main>
    </div>
  );
}

export default App;