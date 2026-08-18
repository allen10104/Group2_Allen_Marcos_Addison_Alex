// A JWT is three base64 parts separated by dots
// (header.payload.signature). The middle part carries the claims, so this
// pulls just that part out and parses it, with no extra library needed.
//
// This reads the token, it does not verify it. The signature can only be
// checked by whoever holds the signing key, which is the backend and never
// the browser. So nothing here is a security check: a user who edits their
// own stored token can make this return whatever they like, and the only
// consequence is that the UI shows them the wrong thing until the backend
// refuses the request. Every real decision is made server side.
//
// Returns null for a missing or malformed token, so callers can treat "no
// usable token" as one case rather than catching around every use.
export function decodeToken(token) {
  if (!token) {
    return null;
  }

  try {
    const payload = token.split(".")[1];

    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
}

// Turns a token into the user it describes, or null if it cannot.
//
// id is converted with Number on purpose. The backend puts the user id in
// the "sub" claim as a string, because the JWT spec requires it, while
// notices.user_id comes back from the API as a number. Comparing them with
// === without this conversion is always false, which would hide the delete
// button on every notice including the user's own.
//
// An expired token returns null. The stored token outlives the tab it was
// created in, so without this check a user coming back the next day would
// look signed in and have every request rejected. exp is in seconds since
// the epoch, Date.now() is in milliseconds, hence the division.
export function userFromToken(token) {
  const claims = decodeToken(token);

  if (!claims) {
    return null;
  }

  const id = Number(claims.sub);

  if (!Number.isFinite(id)) {
    return null;
  }

  if (typeof claims.exp === "number" && claims.exp <= Date.now() / 1000) {
    return null;
  }

  return { id, username: claims.username };
}
