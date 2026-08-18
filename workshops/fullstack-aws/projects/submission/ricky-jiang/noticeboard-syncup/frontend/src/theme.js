// This files holds all the theme configuration for the SyncUp frontend application, which is built using Material-UI (MUI).
// It defines the color palette, typography, shape, and component overrides to customize the appearance of the application.

import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  // The palette property defines the color scheme for the application, including primary, secondary, success, warning,
  // and error colors, as well as background and text colors.
  palette: {
    mode: "light",
    background: {
      default: "#f5f5f7",
      paper: "#ffffff",
    },
    primary: {
      main: "#0071e3",
      contrastText: "#ffffff",
    },
    success: { main: "#34c759" },
    warning: { main: "#ff9500" },
    error: { main: "#ff3b30" },
    text: {
      primary: "#1d1d1f",
      secondary: "#6e6e73",
    },
  },
  // The typography property defines the font family and styles for various text elements in the application.
  typography: {
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, sans-serif',
    h4: { fontWeight: 700, letterSpacing: "-0.02em" },
    button: { textTransform: "none", fontWeight: 700 },
  },
  // The shape property defines the border radius for various components in the application.
  // In this case, it sets a default border radius of 12 pixels for components that use the shape property.
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          padding: "10px 24px",
          boxShadow: "none",
        },
        containedPrimary: {
          "&:hover": { boxShadow: "none" },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          boxShadow: "0 4px 16px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04)",
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: "#f0f0f2",
          borderRadius: 12,
          "& fieldset": { border: "none" },
          "&:hover fieldset": { border: "none" },
          "&.Mui-focused fieldset": { border: "2px solid #0071e3" },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          backgroundColor: "#f0f0f2",
          color: "#6e6e73",
          fontWeight: 500,
        },
      },
    },
    MuiAvatar: {
      styleOverrides: {
        root: {
          backgroundColor: "#d6e9fc",
          color: "#0071e3",
          fontWeight: 700,
        },
      },
    },
  },
});
