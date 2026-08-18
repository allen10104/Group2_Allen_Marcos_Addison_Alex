// A JWT has three dot-separated parts: header.payload.signature.
// This function pulls out just the payload (the part with "sub" and
// "role" in it) and turns it back into a plain JS object.
// This does NOT verify the token's signature — it's only for reading
// the data on the frontend to decide what to show. The backend is what
// actually verifies the token is valid.
export function decodeToken(token) {
  // Split the token into its three parts, and grab the middle one.
  const payloadBase64 = token.split('.')[1];

  // JWTs use base64url encoding, which swaps a couple characters
  // compared to normal base64. This converts it back to standard base64
  // so atob() (the browser's base64 decoder) can read it.
  const base64 = payloadBase64.replace(/-/g, '+').replace(/_/g, '/');

  // Decode the base64 string into a plain JSON string.
  const jsonPayload = atob(base64);

  // Parse the JSON string into a real JavaScript object, e.g.
  // { sub: "1", role: "ADMIN", exp: 1234567890 }
  return JSON.parse(jsonPayload);
}