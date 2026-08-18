// This file defines the VerifyManagerPage component, which provides a user interface for
// verifying a manager account using an email and invite code.

import { useState } from "react";
import { Box, Button, Card, TextField, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import * as api from "../api";
// Normalizes backend error responses (which can be a plain string OR an array of
// validation-error objects) into a single string that's always safe to render.
import { getErrorMessage } from "../api/errors";

// The VerifyManagerPage component renders a form that allows users to enter their email and invite code to verify their manager account.
export function VerifyManagerPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false); // State variable to track if the verification process is in progress
  const [verified, setVerified] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.verifyManager(email, code);
      setVerified(true);
    } catch (err) {
      // Was: err.response?.data?.detail directly, which crashed on validation
      // errors (e.g. a missing field) since detail is an array of objects in that case.
      setError(getErrorMessage(err, "Could not verify this account."));
    } finally {
      setBusy(false);
    }
  }

  if (verified) {
    return (
      <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "background.default" }}>
        <Card sx={{ width: 380, p: 4, textAlign: "center" }}>
          <Typography sx={{ fontWeight: 700, fontSize: 18, mb: 1 }}>Account verified</Typography>
          <Typography sx={{ fontSize: 14, color: "text.secondary", mb: 3 }}>You can log in now.</Typography>
          <Button variant="contained" fullWidth onClick={() => navigate("/login")}>
            Go to login
          </Button>
        </Card>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "background.default" }}>
      <Card sx={{ width: 380, p: 4 }}>
        <Typography sx={{ fontWeight: 700, fontSize: 20, textAlign: "center" }}>Verify your account</Typography>
        <Typography sx={{ fontSize: 13, color: "text.secondary", textAlign: "center", mb: 3 }}>
          Enter the invite code your manager sent you.
        </Typography>

        <Box component="form" onSubmit={handleSubmit}>
          <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required fullWidth sx={{ mb: 2 }} />
          <TextField label="Invite code" value={code} onChange={(e) => setCode(e.target.value)} required fullWidth sx={{ mb: 2 }} />

          {error && <Typography sx={{ fontSize: 13, color: "error.main", mb: 2 }}>{error}</Typography>}

          <Button type="submit" variant="contained" disabled={busy} fullWidth>
            {busy ? "Verifying..." : "Verify account"}
          </Button>
        </Box>
      </Card>
    </Box>
  );
}