// Shared two-panel layout for the login/register screens: a wide branded
// panel on the left (65%) describing the app for managers and employees, and
// a plain panel on the right (35%) holding whatever form the page passes in
// as children. Below the md breakpoint the left panel drops out — there's no
// room for it on a phone — and the form goes full-width.

import { Box, Typography } from "@mui/material";
import CampaignRoundedIcon from "@mui/icons-material/CampaignRounded";
import AdminPanelSettingsRoundedIcon from "@mui/icons-material/AdminPanelSettingsRounded";
import GroupsRoundedIcon from "@mui/icons-material/GroupsRounded";

const FEATURES = [
  {
    icon: AdminPanelSettingsRoundedIcon,
    title: "For managers",
    body: "Post notices, approve or reject employee submissions, and see exactly who's read each one.",
  },
  {
    icon: GroupsRoundedIcon,
    title: "For employees",
    body: "Stay in the loop, submit your own notices for approval, and acknowledge the ones that matter.",
  },
];

export function AuthLayout({ children }) {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: { xs: "1fr", md: "65% 35%" },
      }}
    >
      <Box
        sx={{
          display: { xs: "none", md: "flex" },
          flexDirection: "column",
          justifyContent: "space-between",
          position: "relative",
          overflow: "hidden",
          px: { md: 6, lg: 10 },
          py: 6,
          color: "#fff",
          background: "linear-gradient(150deg, #071226 0%, #0b1f3f 38%, #0a1730 100%)",
        }}
      >
        {/* Blurred color blobs for depth */}
        <Box
          sx={{
            position: "absolute",
            top: -120,
            left: -100,
            width: 420,
            height: 420,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(0,113,227,0.55) 0%, transparent 70%)",
            filter: "blur(10px)",
          }}
        />
        <Box
          sx={{
            position: "absolute",
            bottom: -160,
            left: "30%",
            width: 480,
            height: 480,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(94,58,255,0.35) 0%, transparent 70%)",
            filter: "blur(10px)",
          }}
        />
        <Box
          sx={{
            position: "absolute",
            top: "20%",
            right: -140,
            width: 360,
            height: 360,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(52,199,89,0.25) 0%, transparent 70%)",
            filter: "blur(10px)",
          }}
        />
        <Box
          sx={{
            position: "absolute",
            inset: 0,
            opacity: 0.12,
            backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.7) 1px, transparent 1px)",
            backgroundSize: "26px 26px",
          }}
        />

        <Box
          sx={{
            position: "relative",
            display: "flex",
            alignItems: "center",
            gap: 1,
            width: "fit-content",
            px: 1.5,
            py: 0.75,
            borderRadius: 999,
            bgcolor: "rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.14)",
          }}
        >
          <CampaignRoundedIcon sx={{ fontSize: 20 }} />
          <Typography sx={{ fontWeight: 700, fontSize: 15 }}>SyncUp</Typography>
        </Box>

        <Box sx={{ position: "relative" }}>
          <Typography
            sx={{
              fontWeight: 800,
              fontSize: { md: 46, lg: 60 },
              lineHeight: 1.05,
              letterSpacing: "-0.03em",
              mb: 3,
              background: "linear-gradient(120deg, #ffffff 0%, #cfe3ff 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            The notice ledger
          </Typography>
          <Typography sx={{ fontSize: 17, lineHeight: 1.65, color: "rgba(255,255,255,0.72)", maxWidth: 460, mb: 5 }}>
            Post, approve, and track company notices in one place — with a
            live read-receipt on who's actually seen what.
          </Typography>

          <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5, maxWidth: 460 }}>
            {FEATURES.map(({ icon: Icon, title, body }) => (
              <Box
                key={title}
                sx={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 1.75,
                  p: 2,
                  borderRadius: 4,
                  bgcolor: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  backdropFilter: "blur(6px)",
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    width: 36,
                    height: 36,
                    flexShrink: 0,
                    borderRadius: "50%",
                    bgcolor: "rgba(0,113,227,0.35)",
                  }}
                >
                  <Icon sx={{ fontSize: 19 }} />
                </Box>
                <Box>
                  <Typography sx={{ fontWeight: 700, fontSize: 14.5 }}>{title}</Typography>
                  <Typography sx={{ fontSize: 13.5, lineHeight: 1.5, color: "rgba(255,255,255,0.68)" }}>
                    {body}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Box>

        <Typography sx={{ position: "relative", fontSize: 13, color: "rgba(255,255,255,0.45)" }}>
          © 2026 SyncUp
        </Typography>
      </Box>

      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          bgcolor: "background.paper",
          p: 3,
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
