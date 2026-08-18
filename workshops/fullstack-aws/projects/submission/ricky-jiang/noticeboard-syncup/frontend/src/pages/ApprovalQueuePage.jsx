
// This file defines the ApprovalQueuePage component, which displays a list of notices that are pending approval. 
// It fetches the notices from the backend and allows users to approve or reject them, updating the state accordingly.
import { useEffect, useState } from "react";
import { Box, CircularProgress, Container, Typography } from "@mui/material";
import * as api from "../api";
import { NoticeCard } from "../components/NoticeCard";

export function ApprovalQueuePage() {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
    // Fetches data from backend using api.getFeed() and sets the notices state with the fetched data.
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

  //filter notices to only show pending ones for approval queue
  const pending = notices.filter((n) => n.status === "PENDING");

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography sx={{ fontWeight: 700, fontSize: 32, mb: 4 }}>Approval queue</Typography>

      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress />
        </Box>
      )}

      {!loading && pending.length === 0 && (
        <Typography sx={{ color: "text.secondary" }}>Nothing pending review.</Typography>
      )}

      {!loading && pending.map((notice) => <NoticeCard key={notice.id} notice={notice} onChange={handleChange} />)}
    </Container>
  );
}