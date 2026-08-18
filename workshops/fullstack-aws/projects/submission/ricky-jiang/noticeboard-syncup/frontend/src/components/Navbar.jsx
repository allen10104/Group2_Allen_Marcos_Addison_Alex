// This file defines the Navbar component, which renders a navigation bar with links based on the user's role.

import {
  AppBar,
  Box,
  IconButton,
  Toolbar,
  Typography,
} from "@mui/material";
import LogoutIcon from "@mui/icons-material/Logout";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/logo.png";

// role specific links for the navigation bar, each with a label, route, and allowed roles.
const LINKS = [
  { label: "Notice feed", to: "/", roles: ["MANAGER", "EMPLOYEE"] },
  { label: "Submit notice", to: "/submit", roles: ["MANAGER", "EMPLOYEE"] },
  { label: "Approval queue", to: "/approvals", roles: ["MANAGER"] },
  { label: "Add employee", to: "/employees", roles: ["MANAGER"] },
  { label: "Invite codes", to: "/invite-codes", roles: ["MANAGER"] },
];

// The Navbar component renders a navigation bar with links based on the user's role.
// It also includes a logout button and displays the logged-in user's email.
export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const visibleLinks = LINKS.filter((link) => link.roles.includes(user.role));

  return (
    // MUI standard navigation bar component , sticky pins it at the top
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        bgcolor: "rgba(255,255,255,0.72)",
        backdropFilter: "blur(20px)",
        color: "text.primary",
        borderBottom: "1px solid rgba(0,0,0,0.06)",
      }}
    >
      <Toolbar sx={{ gap: 1 }}>
        <Box
          component="img"
          src={logo}
          alt="SyncUp logo"
          sx={{ width: 32, height: 32, borderRadius: "22%", mr: 1, objectFit: "cover" }}
        />
        <Typography variant="h6" sx={{ fontWeight: 700, mr: 4 }}>
          SyncUp
        </Typography>

        <Box sx={{ display: "flex", gap: 1, flexGrow: 1 }}>
          {/* Visible links are mapped to Typography components that act as navigation links using NavLink from react-router-dom. */}
          {visibleLinks.map((link) => (
            <Typography
              key={link.to}
              component={NavLink}
              to={link.to}
              end={link.to === "/"}
              sx={{
                px: 2,
                py: 0.75,
                borderRadius: 999,
                fontSize: 14,
                fontWeight: 600,
                textDecoration: "none",
                color: "text.primary",
                "&.active": {
                  bgcolor: "rgba(0,113,227,0.12)",
                  color: "primary.main",
                },
              }}
            >
              {link.label}
            </Typography>
          ))}
        </Box>

        {/* user.email arrives a moment after login/page-load, once AuthContext's
            effect finishes fetching /auth/me (the JWT itself only has id + role).
            Nothing renders here until it resolves, rather than showing a placeholder. */}
        {user.email && (
          <Typography sx={{ fontSize: 14, fontWeight: 600, color: "text.primary", mr: 2 }}>
            {user.email}
          </Typography>
        )}
        <IconButton
          onClick={() => {
            logout();
            navigate("/login");
          }}
          aria-label="Log out"
        >
          <LogoutIcon fontSize="small" />
        </IconButton>
      </Toolbar>
    </AppBar>
  );
}
