// useState holds what has been typed so far, plus the in-flight and error
// state for the submit.
import { useState } from "react";

import {
  Alert,
  Box,
  Button,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { createNotice } from "../api/notices";

// The form for posting a new notice.
//
// onCreated is called only after the backend confirms the write, which is
// what tells App to refetch the list. Nothing is added to the list here:
// re-reading from the backend means the notice on screen is the notice that
// was actually stored, including the id and timestamp the database
// generated, rather than a local guess at it.
function NoticeForm({ onCreated }) {
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");

  // True while the POST is in flight. This is what disables the button, so
  // an impatient double click cannot post the same notice twice.
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Both fields trimmed, because " " is not a real notice and the backend
  // would refuse it with a 422 anyway. Checking here keeps the button
  // disabled instead of letting someone submit a request that cannot work.
  const canSubmit = name.trim() !== "" && message.trim() !== "" && !submitting;

  const handleSubmit = async (event) => {
    // A form submit reloads the page by default, which would throw away the
    // whole React app mid request.
    event.preventDefault();

    // Guard as well as disabling the button, since a form can also be
    // submitted by pressing Enter in a text field.
    if (!canSubmit) {
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      await createNotice({ name: name.trim(), message: message.trim() });

      // Cleared only on success. Leaving the text in place after a failure
      // means a backend that was momentarily down does not cost someone the
      // message they just typed.
      setName("");
      setMessage("");

      onCreated();
    } catch (err) {
      console.error(err);

      setError(err.message);
    } finally {
      // In a finally block so the form unlocks whether the post succeeded
      // or failed. Leaving it out of the catch path would leave the button
      // disabled forever after one error.
      setSubmitting(false);
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Post a notice
      </Typography>

      {/* component="form" keeps this a real form element, so Enter submits
          and browsers still treat the fields as a group. */}
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Stack spacing={2}>
          <TextField
            label="Name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            // Matches the max_length on the backend model, so the limit is
            // hit here with no round trip rather than coming back as a 422.
            slotProps={{ htmlInput: { maxLength: 100 } }}
            fullWidth
            required
          />

          <TextField
            label="Message"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            slotProps={{ htmlInput: { maxLength: 2000 } }}
            multiline
            rows={3}
            fullWidth
            required
          />

          {error && <Alert severity="error">{error}</Alert>}

          <Box>
            <Button type="submit" variant="contained" disabled={!canSubmit}>
              {submitting ? "Posting..." : "Post notice"}
            </Button>
          </Box>
        </Stack>
      </Box>
    </Paper>
  );
}

export default NoticeForm;
