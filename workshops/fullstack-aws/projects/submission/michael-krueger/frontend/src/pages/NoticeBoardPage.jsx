// useState holds the refresh counter that ties the form and the list
// together. useCallback keeps the handler identity stable between renders.
import { useCallback, useState } from "react";

import { Box, Container, Typography } from "@mui/material";

import NoticeForm from "../components/NoticeForm";
import NoticeList from "../components/NoticeList";

// The board itself, moved out of App.jsx when routing was added so that App
// is only about wiring: providers, routes and the header.
function NoticeBoardPage() {
  // Bumped after every successful create or delete. NoticeList watches this
  // number and refetches when it changes.
  //
  // A counter rather than a boolean, because two creates in a row have to
  // register as two separate changes. A boolean flipped back and forth would
  // work by accident and break the moment anything else touched it.
  const [refreshKey, setRefreshKey] = useState(0);

  // Uses the updater form, so it is always incrementing the current value
  // rather than one captured when this render happened. That matters when a
  // create and a delete finish at almost the same moment.
  //
  // useCallback keeps this the same function across renders, which means
  // passing it down does not give NoticeList a new prop every time this page
  // re-renders.
  const handleChanged = useCallback(() => {
    setRefreshKey((previous) => previous + 1);
  }, []);

  return (
    // maxWidth sm keeps the column narrow enough to read comfortably on a
    // wide monitor. The notices are short text, so a full width page would
    // stretch each one into a single long line.
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <NoticeForm onCreated={handleChanged} />

      <Box>
        <Typography variant="h6" gutterBottom>
          Notices
        </Typography>

        <NoticeList refreshKey={refreshKey} onDeleted={handleChanged} />
      </Box>
    </Container>
  );
}

export default NoticeBoardPage;
