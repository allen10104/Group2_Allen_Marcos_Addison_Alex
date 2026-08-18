// THis file defines the RegisterPage component, which provides a user interface for creating a new account with email, password, role selection, and optional invite code.
import { useState } from "react";
import { Box, Button, TextField, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import { Link, useNavigate } from "react-router-dom";
import * as api from "../api";
// Normalizes backend error responses (which can be a plain string OR an array of
// validation-error objects) into a single string that's always safe to render.
import { getErrorMessage } from "../api/errors";
import { AuthLayout } from "../components/AuthLayout";

// The RegisterPage component renders a registration form that allows users to enter their email, password, select their role (Employee or Manager),
// and optionally provide an invite code for manager accounts.
export function RegisterPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("EMPLOYEE");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  // Handles the form submission for creating a new account, calling the register function from the API and updating the component state based on the response.
  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await api.register(email, password, role, inviteCode);
      setResult(user);
    } catch (err) {
      // Was: err.response?.data?.detail directly, which crashed on validation
      // errors (e.g. a short password) since detail is an array of objects in that case.
      setError(getErrorMessage(err, "Could not create account."));
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    const isPendingManager = result.role === "MANAGER" && result.status === "PENDING";

    return (
      <AuthLayout>
        <Box sx={{ width: "100%", maxWidth: 400, textAlign: "center" }}>
          <Typography sx={{ fontWeight: 700, fontSize: 22, mb: 1 }}>Account created</Typography>
          <Typography sx={{ fontSize: 14, color: "text.secondary", mb: 3 }}>
            {isPendingManager
              ? "Your account is pending verification. Ask an existing manager for an invite code, then verify on the next screen."
              : "You're all set — sign in now."}
          </Typography>
          <Button variant="contained" fullWidth onClick={() => navigate(isPendingManager ? "/verify-manager" : "/login")}>
            {isPendingManager ? "Verify account" : "Go to sign in"}
          </Button>
        </Box>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <Box sx={{ width: "100%", maxWidth: 400 }}>
        <Typography sx={{ fontWeight: 700, fontSize: 26 }}>Sign up</Typography>
        <Typography sx={{ fontSize: 14, color: "text.secondary", mb: 3 }}>
          Create an account to get started.
        </Typography>

        <Box component="form" onSubmit={handleSubmit}>
          <ToggleButtonGroup
            value={role}
            exclusive
            onChange={(e, value) => value && setRole(value)}
            fullWidth
            sx={{ mb: 2 }}
          >
            <ToggleButton value="EMPLOYEE">Employee</ToggleButton>
            <ToggleButton value="MANAGER">Manager</ToggleButton>
          </ToggleButtonGroup>

          <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required fullWidth sx={{ mb: 2 }} />
          <TextField label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required fullWidth sx={{ mb: 2 }} />

          {role === "MANAGER" && (
            <TextField
              label="Invite code (optional)"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value)}
              fullWidth
              helperText="Have a code from an existing manager? Enter it now — otherwise your account will need verification."
              sx={{ mb: 2 }}
            />
          )}

          {error && <Typography sx={{ fontSize: 13, color: "error.main", mb: 2 }}>{error}</Typography>}

          <Button type="submit" variant="contained" disabled={busy} fullWidth sx={{ mb: 2 }}>
            {busy ? "Creating account..." : "Create account"}
          </Button>

          <Typography sx={{ fontSize: 14, color: "text.secondary", textAlign: "center" }}>
            Already have an account? <Link to="/login">Sign in</Link>
          </Typography>
        </Box>
      </Box>
    </AuthLayout>
  );
}
