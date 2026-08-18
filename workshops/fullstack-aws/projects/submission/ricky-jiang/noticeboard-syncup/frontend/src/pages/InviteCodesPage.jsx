// This file defines the InviteCodesPage component, which allows managers to generate one-time invite codes
//  for new users.
import { useState } from "react";
import { Box, Button, Card, Container, TextField, Typography } from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import * as api from "../api";
// Normalizes backend error responses (which can be a plain string OR an array of
// validation-error objects) into a single string that's always safe to render.
import { getErrorMessage } from "../api/errors";

// The InviteCodesPage component renders a form that allows managers to enter the email of a 
// new user and generate a one-time invite code for them.
export function InviteCodesPage() {
  const [targetEmail, setTargetEmail] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [generated, setGenerated] = useState(null);
  const [copied, setCopied] = useState(false);

  // Handles the form submission for generating a new invite code, calling the createInviteCode 
  // function from the API and updating the component state based on the response.
  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const code = await api.createInviteCode(targetEmail);
      setGenerated(code);
      setCopied(false);
      setTargetEmail("");
    } catch (err) {
      // Was: err.response?.data?.detail directly, which crashed on validation
      // errors (e.g. an invalid email) since detail is an array of objects in that case.
      setError(getErrorMessage(err, "Could not generate a code."));
    } finally {
      setBusy(false);
    }
  }

  // Handles copying the generated invite code to the clipboard and updates the 
  // component state to indicate that the code has been copied.
  function handleCopy() {
    navigator.clipboard.writeText(generated.code);
    setCopied(true);
  }

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography sx={{ fontWeight: 700, fontSize: 32, mb: 1 }}>Invite codes</Typography>
      <Typography sx={{ color: "text.secondary", mb: 4 }}>
        Generate a one-time code for someone you want to become a manager. They'll enter it when registering, or later to verify a pending account.
      </Typography>

      <Card sx={{ p: 4 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <TextField label="Their email" type="email" value={targetEmail} onChange={(e) => setTargetEmail(e.target.value)} required fullWidth sx={{ mb: 2 }} />

          {error && <Typography sx={{ fontSize: 13, color: "error.main", mb: 2 }}>{error}</Typography>}

          <Button type="submit" variant="contained" disabled={busy}>
            {busy ? "Generating..." : "Generate code"}
          </Button>
        </Box>

        {generated && (
          <Box sx={{ mt: 3, p: 2, bgcolor: "background.default", borderRadius: 2, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <Box>
              <Typography sx={{ fontFamily: "monospace", fontSize: 18, fontWeight: 700 }}>{generated.code}</Typography>
              <Typography sx={{ fontSize: 13, color: "text.secondary" }}>
                For {generated.target_email} — share this with them directly.
              </Typography>
            </Box>
            <Button startIcon={<ContentCopyIcon fontSize="small" />} onClick={handleCopy}>
              {copied ? "Copied" : "Copy"}
            </Button>
          </Box>
        )}
      </Card>
    </Container>
  );
}