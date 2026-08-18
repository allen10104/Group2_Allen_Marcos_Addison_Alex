// THis file defines the FeedPage component, which displays a feed of notices fetched from the backend, with role-based filtering for managers and employees.
import { useEffect, useState } from "react";
import { Box, CircularProgress, Container, Typography } from "@mui/material";
import * as api from "../api";
import { NoticeCard } from "../components/NoticeCard";
import { useAuth } from "../context/AuthContext";

export function FeedPage() {
  const { isManager } = useAuth();
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetches data from backend using api.getFeed() and sets the notices state with the fetched data.
  // Once the data is loaded, it sets the loading state to false.
  useEffect(() => {
    api.getFeed().then((data) => {
      setNotices(data);
      setLoading(false);
    });
  }, []);

  // Updates the notices state when a notice is changed (e.g., approved or rejected) by mapping through the existing notices and replacing the updated notice with the new data.
  function handleChange(updated) {
    setNotices((prev) => prev.map((n) => (n.id === updated.id ? updated : n)));
  }

  // role based filtering of notices. Managers only see approved notices, while employees see all notices.
  const visible = isManager
    ? notices.filter((n) => n.status === "APPROVED")
    : notices;

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography sx={{ fontWeight: 700, fontSize: 32, mb: 4 }}>
        Notice feed
      </Typography>

      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress />
        </Box>
      )}

      {!loading && visible.length === 0 && (
        <Typography sx={{ color: "text.secondary" }}>
          No notices yet.
        </Typography>
      )}

      {!loading &&
        visible.map((notice) => (
          <NoticeCard key={notice.id} notice={notice} onChange={handleChange} />
        ))}
    </Container>
  );
}
