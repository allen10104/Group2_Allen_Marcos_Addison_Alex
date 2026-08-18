import { useState } from "react";
import { Link as RouterLink, useLocation, useNavigate } from "react-router-dom";

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

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Where to go once signed in.
  //
  // ProtectedRoute puts the page the user was originally after into location
  // state, so someone who followed a link to the board while logged out ends
  // up there rather than always at "/".
  const destination = location.state?.from?.pathname || "/";

  // A signup that redirected here rather than auto-logging in would leave a
  // message for the user. Nothing does that today, since AuthContext.signup
  // logs straight in, but reading it costs a line and means the signup page
  // can change its mind without this page needing an edit.
  const notice = location.state?.message || "";

  const canSubmit = username.trim() !== "" && password !== "" && !submitting;

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
      await login(username.trim(), password);

      // replace so the login page is not left in the history stack. Without
      // it, pressing Back from the board would land on a login form for a
      // session that is already signed in.
      navigate(destination, { replace: true });
    } catch (err) {
      console.error(err);

      // The backend answers a wrong username and a wrong password with the
      // same deliberately vague message, and it is shown as it is rather
      // than being second guessed here.
      setError(err.message);

      // Only the password is cleared. Making someone retype a username they
      // probably got right is irritating, and it is not the secret.
      setPassword("");
    } finally {
      // In a finally block so the form unlocks whether the login succeeded
      // or failed. Leaving it out of the catch path would leave the button
      // disabled forever after one wrong password.
      setSubmitting(false);
    }
  };

  return (
    <Container maxWidth="xs" sx={{ py: 6 }}>
      <Paper sx={{ p: 3 }}>
        {/* The welcome block. Someone arriving at a bare login form has no
            way of knowing what they are logging in to, and this is the
            first page a logged out visitor sees, because ProtectedRoute
            sends them here from the board.

            This carries the h1 now, and "Log in" below has become the h2.
            A page has one top level heading, and on this page it is what
            the page is about rather than what the form does. */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" component="h1" gutterBottom>
            Welcome to Notice Board
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Read what everyone has posted, and log in to add a notice of your
            own.
          </Typography>
        </Box>

        <Typography variant="h6" component="h2" gutterBottom>
          Log in
        </Typography>

        {notice && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {notice}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <Stack spacing={2}>
            <TextField
              label="Username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              // Tells a password manager which field is which, and puts the
              // cursor here on load so the form can be filled without
              // reaching for the mouse.
              autoComplete="username"
              autoFocus
              fullWidth
              required
            />

            <TextField
              label="Password"
              // type password is what masks the input and keeps it out of
              // the browser's autofill history for ordinary text fields.
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              fullWidth
              required
            />

            {error && <Alert severity="error">{error}</Alert>}

            <Button type="submit" variant="contained" disabled={!canSubmit}>
              {submitting ? "Logging in..." : "Log in"}
            </Button>

            <Typography variant="body2" align="center">
              {/* RouterLink rather than a plain anchor, so navigation stays
                  inside the app instead of triggering a full page reload
                  that would throw away React state. */}
              No account yet?{" "}
              <Link component={RouterLink} to="/signup">
                Sign up
              </Link>
            </Typography>
          </Stack>
        </Box>
      </Paper>
    </Container>
  );
}

export default LoginPage;
