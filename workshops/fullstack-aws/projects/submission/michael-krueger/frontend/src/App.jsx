import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";

import {
  AppBar,
  Box,
  Button,
  CssBaseline,
  Toolbar,
  Typography,
} from "@mui/material";

import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import NoticeBoardPage from "./pages/NoticeBoardPage";
import SignupPage from "./pages/SignupPage";

// The bar across the top, including the logout button.
//
// A separate component rather than markup inside App because it calls
// useAuth and useNavigate, and both have to run inside the provider and the
// router. Written inline in App it would sit outside them and throw.
function Header() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();

    // AuthContext deliberately does not redirect, since it has no view of
    // the router. Doing it here keeps the context reusable and puts the
    // navigation next to the button that caused it.
    //
    // replace so the board does not stay in the history stack, where Back
    // would return to a page the user has just signed out of.
    navigate("/login", { replace: true });
  };

  return (
    <AppBar position="static">
      <Toolbar>
        {/* flexGrow pushes everything after it to the right hand end. */}
        <Typography variant="h6" component="h1" sx={{ flexGrow: 1 }}>
          Notice Board
        </Typography>

        {/* The whole block is hidden while logged out, so the login and
            signup pages show a plain header with no controls that would not
            work. */}
        {isAuthenticated && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Typography variant="body2">
              Signed in as {user.username}
            </Typography>

            <Button color="inherit" onClick={handleLogout}>
              Log out
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}

// The routes, split out for the same reason as Header: this calls nothing
// itself, but keeping it beside Header makes it obvious that both live
// inside the provider and the router set up below.
function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      {/* The board is the only protected route. ProtectedRoute sends a
          logged out visitor to /login and remembers where they were headed,
          so they land back here after signing in. */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <NoticeBoardPage />
          </ProtectedRoute>
        }
      />

      {/* Anything else goes to the board, which in turn bounces to /login if
          nobody is signed in. Without this a typo in the address bar renders
          a blank page with no explanation. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    // The nesting order matters. AuthProvider is inside BrowserRouter so
    // that anything it renders can use router hooks, and both wrap the
    // routes so every page can reach the auth state.
    //
    // CssBaseline applies MUI's own resets, which is what makes the page use
    // the theme's background and typography instead of the browser defaults.
    <BrowserRouter>
      <AuthProvider>
        <CssBaseline />

        <Header />

        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
