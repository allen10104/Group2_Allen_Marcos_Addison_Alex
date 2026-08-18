// This file defines the CreateEmployeePage component, which allows managers to create new employee accounts 
// by providing an email and a password.

import { useState } from "react";
import { Box, Button, Card, Container, TextField, Typography } from "@mui/material";
import * as api from "../api";
// Normalizes backend error responses (which can be a plain string OR an array of
// validation-error objects) into a single string that's always safe to render.
import { getErrorMessage } from "../api/errors";

// The CreateEmployeePage component renders a form that allows managers to enter the email and  password for
// a new employee account.
export function CreateEmployeePage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [created, setCreated] = useState(null);
  const [busy, setBusy] = useState(false);

  // Handles the form submission for creating a new employee account, calling the createEmployee
  // function from the API and updating
  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await api.createEmployee(email, password);
      setCreated(user);
      setEmail("");
      setPassword("");
    } catch (err) {
      // Was: err.response?.data?.detail directly, which crashed on validation
      // errors (e.g. a short password) since detail is an array of objects in that case.
      setError(getErrorMessage(err, "Could not create account."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography sx={{ fontWeight: 700, fontSize: 32, mb: 1 }}>Add employee</Typography>
      <Typography sx={{ color: "text.secondary", mb: 4 }}>
        Provision an account directly — useful if you'd rather hand someone working credentials than have them self-register.
      </Typography>

      <Card sx={{ p: 4 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required fullWidth sx={{ mb: 3 }} />
          <TextField label="Temporary password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required fullWidth sx={{ mb: 2 }} />

          {error && <Typography sx={{ fontSize: 13, color: "error.main", mb: 2 }}>{error}</Typography>}

          <Button type="submit" variant="contained" disabled={busy}>
            {busy ? "Creating..." : "Create employee account"}
          </Button>
        </Box>

        {created && (
          <Typography sx={{ fontSize: 14, color: "success.main", mt: 3 }}>
            Created {created.email} — share the temporary password with them directly.
          </Typography>
        )}
      </Card>
    </Container>
  );
}