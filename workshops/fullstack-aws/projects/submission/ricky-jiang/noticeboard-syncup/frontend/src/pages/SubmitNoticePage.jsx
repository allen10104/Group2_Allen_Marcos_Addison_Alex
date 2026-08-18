// This file defines the SubmitNoticePage component, which allows users to submit a new notice.
// It provides a form for entering the notice title, category, and body, and handles the 
// submission process by calling the backend API.
import { useState } from "react";
import { Box, Button, Card, Container, TextField, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import * as api from "../api";
import { useAuth } from "../context/AuthContext";

// The SubmitNoticePage component renders a form that allows users to enter the title, category, and body of a notice.
// Upon submission, it calls the submitNotice function from the API and updates the component state based on the response.
export function SubmitNoticePage() {
  const navigate = useNavigate();
  const { isManager } = useAuth();
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  // Handles the form submission for creating a new notice, calling the submitNotice function from the API and updating 
  // the component state based on the response.
  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.submitNotice(title, body, category || "general");
      setSubmitted(true);
    } finally {
      setBusy(false);
    }
  }

  // If the notice has been successfully submitted, the component displays a confirmation message and a button to navigate back to the feed.
  if (submitted) {
    return (
      <Container maxWidth="md" sx={{ py: 6 }}>
        <Typography sx={{ fontWeight: 700, fontSize: 32, mb: 2 }}>Notice submitted</Typography>
        <Typography sx={{ color: "text.secondary", mb: 3 }}>
          {isManager ? "Your notice is live on the feed." : "Your notice will need manager approval before it appears."}
        </Typography>
        <Button variant="contained" onClick={() => navigate("/")}>Back to feed</Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography sx={{ fontWeight: 700, fontSize: 32, mb: 4 }}>Submit a notice</Typography>

      <Card sx={{ p: 4 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <TextField label="Title" placeholder="A short, clear headline" value={title} onChange={(e) => setTitle(e.target.value)} required fullWidth sx={{ mb: 3 }} />
          <TextField label="Category" placeholder="e.g. Policy, Ops, Events" value={category} onChange={(e) => setCategory(e.target.value)} fullWidth sx={{ mb: 3 }} />
          <TextField label="Body" placeholder="Write the full notice here" value={body} onChange={(e) => setBody(e.target.value)} required multiline rows={6} fullWidth sx={{ mb: 2 }} />

          <Typography sx={{ fontSize: 13, color: "text.secondary", mb: 2 }}>
            {isManager ? "Your notice goes live immediately." : "Your notice will need manager approval before it appears."}
          </Typography>

          <Button type="submit" variant="contained" disabled={busy}>
            {busy ? "Publishing..." : "Publish notice"}
          </Button>
        </Box>
      </Card>
    </Container>
  );
}