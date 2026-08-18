// This file defines the NoticeCard component, which displays a notice with its details and actions based on the user's role and the notice's status.

import { useState } from "react";
import { Box, Button, Card, CardContent, Chip, Divider, LinearProgress, Typography } from "@mui/material";
import * as api from "../api";
import { useAuth } from "../context/AuthContext";

// Maps notice statuses to their corresponding color codes for display purposes.
const STATUS_COLOR = {
  PENDING: "warning.main",
  APPROVED: "success.main",
  REJECTED: "error.main",
};

// Converts a date string into a human-readable "time ago" format, such as "2 days ago" or "just now".
function timeAgo(dateString) {
  const seconds = Math.floor((Date.now() - new Date(dateString)) / 1000);
  const units = [
    ["year", 31536000],
    ["month", 2592000],
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];
  for (const [label, secondsInUnit] of units) {
    const value = Math.floor(seconds / secondsInUnit);
    if (value >= 1) return `${value} ${label}${value > 1 ? "s" : ""} ago`;
  }
  return "just now";
}
// The NoticeCard component displays a notice's title, category, body, status, and actions based on the user's role and the notice's status.
export function NoticeCard({ notice, onChange }) {
  const { isManager, isEmployee } = useAuth();
  const [readReport, setReadReport] = useState(null);
  const [busy, setBusy] = useState(false);

  // Helper function to run an asynchronous action (like approving or rejecting a notice) and update the notice state accordingly.
  async function runAction(fn) {
    setBusy(true);
    try {
      const updated = await fn();
      onChange(updated);
    } finally {
      setBusy(false);
    }
  }
 // Toggles the read report for the notice, fetching it from the backend if it's not already loaded.
  async function toggleReadReport() {
    if (readReport) {
      setReadReport(null);
      return;
    }
    const report = await api.getReadStatus(notice.id);
    setReadReport(report);
  }
  // Read state only ever means anything for an approved notice - PENDING/REJECTED
  // notices are never "read", they're just not yet (or no longer) live.
  const isUnread = notice.status === "APPROVED" && !notice.read_by_me;
  const isRead = notice.status === "APPROVED" && notice.read_by_me;

  // The component returns a Card component from MUI that contains the notice's details and action buttons based on the user's role and the notice's status.
  return (
    <Card
      sx={{
        mb: 2,
        // Once read, the card "sinks" back into the page: same background color as the
        // page behind it, no shadow, just a hairline border - so it visually recedes and
        // unread cards (still white + shadowed) stand out by comparison when scanning the feed.
        ...(isRead && {
          bgcolor: "background.default",
          boxShadow: "none",
          border: "1px solid rgba(0,0,0,0.06)",
        }),
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {/* Small unread dot - only shown while this specific viewer hasn't acknowledged
                the notice yet. Disappears the instant it's marked read. */}
            {isUnread && (
              <Box sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: "primary.main", flexShrink: 0 }} />
            )}
            <Typography sx={{ fontWeight: isRead ? 500 : 700, fontSize: 18 }}>{notice.title}</Typography>
          </Box>
          <Typography sx={{ fontWeight: 700, fontSize: 13, color: STATUS_COLOR[notice.status] }}>
            {notice.status.charAt(0) + notice.status.slice(1).toLowerCase()}
          </Typography>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
          <Chip label={notice.category} size="small" />
          <Typography sx={{ fontSize: 13, color: "text.secondary" }}>{timeAgo(notice.created_at)}</Typography>
        </Box>

        <Typography sx={{ fontSize: 15, mb: 2 }}>{notice.body}</Typography>

        {notice.status === "APPROVED" && (
          <Typography sx={{ fontSize: 13, color: "text.secondary", mb: 2 }}>
            {notice.read_count} read
          </Typography>
        )}

        <Divider sx={{ mb: 2 }} />

        <Box sx={{ display: "flex", gap: 1 }}>
          {isEmployee && isUnread && (
            <Button variant="contained" disabled={busy} onClick={() => runAction(() => api.acknowledgeNotice(notice.id))}>
              Mark as read
            </Button>
          )}
          {isEmployee && isRead && (
            <Typography sx={{ fontSize: 14, fontWeight: 600, color: "success.main", alignSelf: "center" }}>
              Read
            </Typography>
          )}

          {isManager && notice.status === "PENDING" && (
            <>
              <Button variant="contained" color="success" disabled={busy} onClick={() => runAction(() => api.approveNotice(notice.id))}>
                Approve
              </Button>
              <Button variant="outlined" color="error" disabled={busy} onClick={() => runAction(() => api.rejectNotice(notice.id))}>
                Reject
              </Button>
            </>
          )}

          {isManager && notice.status === "APPROVED" && (
            <Button variant="text" onClick={toggleReadReport}>
              {readReport ? "Hide read report" : "View read report"}
            </Button>
          )}
        </Box>

        {readReport && (
          <Box sx={{ mt: 2, pt: 2, borderTop: "1px solid rgba(0,0,0,0.06)" }}>
            <Typography sx={{ fontSize: 14, mb: 1 }}>
              {readReport.read_count} of {readReport.total_employees} employees have read this.
            </Typography>
            <LinearProgress
              variant="determinate"
              value={readReport.total_employees ? (readReport.read_count / readReport.total_employees) * 100 : 0}
              sx={{ height: 6, borderRadius: 3, mb: 1.5 }}
            />
            {readReport.unread_emails.length > 0 && (
              <Typography sx={{ fontSize: 13, color: "text.secondary" }}>
                Not yet read: {readReport.unread_emails.join(", ")}
              </Typography>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}