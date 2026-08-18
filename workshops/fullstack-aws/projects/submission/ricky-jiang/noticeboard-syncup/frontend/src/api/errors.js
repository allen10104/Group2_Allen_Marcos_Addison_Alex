// FastAPI sends error details in two different shapes, depending on how the error was raised:
//   1. A custom error (e.g. HTTPException(detail="Email already in use")) -> err.response.data.detail is a plain STRING.
//   2. An automatic Pydantic validation error (e.g. a password under 8 characters) -> err.response.data.detail
//      is an ARRAY of objects, one per failed field, each with its own "msg" describing what went wrong.
// React cannot render a raw object/array of objects as text directly ("Objects are not valid as a React child"),
// so any page that tries to display detail straight from the response will crash on validation errors.
// This helper normalizes both shapes into a single plain string that's always safe to render.
export function getErrorMessage(err, fallback) {
  const detail = err.response?.data?.detail;

  // Custom errors: detail is already the exact message we want to show.
  if (typeof detail === "string") return detail;

  // Validation errors: detail is an array of { msg, loc, type, ... } objects.
  // Pull out just the "msg" from each one and join them into a single readable string.
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(" ");

  // No usable detail at all (network error, unexpected response shape, etc.) - fall back to a generic message.
  return fallback;
}
