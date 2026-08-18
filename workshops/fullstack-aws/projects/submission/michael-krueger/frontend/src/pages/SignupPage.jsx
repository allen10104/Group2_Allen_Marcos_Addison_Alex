import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import {
  Alert,
  Box,
  Button,
  Container,
  Link,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { useAuth } from "../context/AuthContext";

// Matches the min_length on UserCreate in the backend's app/models/user.py.
// Checking here means the mismatch is caught before a request goes out, and
// the message can say what the rule is rather than echoing a validation
// error. The backend still enforces it, since nothing stops a caller from
// skipping this form entirely.
const MIN_PASSWORD_LENGTH = 8;

function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Only shown once the user has typed something into the confirm box, so
  // the form does not accuse them of a mismatch before they have had a
  // chance to fill it in.
  const passwordsMismatch =
    confirmPassword !== "" && password !== confirmPassword;

  const passwordTooShort =
    password !== "" && password.length < MIN_PASSWORD_LENGTH;

  const canSubmit =
    username.trim() !== "" &&
    password.length >= MIN_PASSWORD_LENGTH &&
    password === confirmPassword &&
    !submitting;

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      // AuthContext.signup creates the account and logs straight into it,
      // because the backend issues no token at signup. So by the time this
      // resolves there is a token and the board is reachable.
      await signup(username.trim(), password);

      navigate("/", { replace: true });
    } catch (err) {
      console.error(err);

      // Covers a taken username (409) and a password the backend rejects,
      // both of which arrive with a message worth showing as it is.
      setError(err.message);

      // Both password fields are cleared but the username is kept, since a
      // taken username is the likeliest failure and the user is about to
      // edit it rather than retype it.
      setPassword("");
      setConfirmPassword("");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Container maxWidth="xs" sx={{ py: 6 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" component="h1" gutterBottom>
          Sign up
        </Typography>

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <Stack spacing={2}>
            <TextField
              label="Username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              // Matches the max_length on the backend model, so the limit is
              // hit here with no round trip rather than coming back as a 422.
              slotProps={{ htmlInput: { maxLength: 50 } }}
              autoComplete="username"
              autoFocus
              fullWidth
              required
            />

            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              // bcrypt cannot hash more than 72 bytes, which the backend
              // enforces and explains. Capping it here keeps the form from
              // offering something that cannot work.
              slotProps={{ htmlInput: { maxLength: 72 } }}
              // new-password is what tells a password manager to offer to
              // generate one rather than filling in an existing password.
              autoComplete="new-password"
              error={passwordTooShort}
              helperText={
                passwordTooShort
                  ? `Use at least ${MIN_PASSWORD_LENGTH} characters`
                  : " "
              }
              fullWidth
              required
            />

            <TextField
              label="Confirm password"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              slotProps={{ htmlInput: { maxLength: 72 } }}
              autoComplete="new-password"
              error={passwordsMismatch}
              // A single space keeps the helper text row present even when
              // there is nothing to say, so the button below does not jump
              // up and down as the message appears and disappears.
              helperText={passwordsMismatch ? "Passwords do not match" : " "}
              fullWidth
              required
            />

            {error && <Alert severity="error">{error}</Alert>}

            <Button type="submit" variant="contained" disabled={!canSubmit}>
              {submitting ? "Creating account..." : "Sign up"}
            </Button>

            <Typography variant="body2" align="center">
              Already have an account?{" "}
              <Link component={RouterLink} to="/login">
                Log in
              </Link>
            </Typography>
          </Stack>
        </Box>
      </Paper>
    </Container>
  );
}

export default SignupPage;
