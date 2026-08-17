import type { ExpiryOption, Notice } from "@/types";

// Injected at build time by Vite (see ASSIGNMENT.md: VITE_API_URL).
// Expected to include the /api suffix, e.g. https://<cloudfront-domain>/api
// (or http://localhost:8000/api for local dev).
const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

// The API returns image_url as a path relative to the site's origin (e.g.
// "/uploads/abc123.jpg") since in production the frontend and /uploads/*
// share one CloudFront domain. Locally, the Vite dev server and the API run
// on different ports, so relative paths need this to resolve against the
// API's own origin instead of the page's.
const ASSET_BASE = API_URL.replace(/\/api\/?$/, "");

export function resolveAssetUrl(path: string): string {
  return path.startsWith("http") ? path : `${ASSET_BASE}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_URL) {
    throw new Error(
      "VITE_API_URL is not set. Set it before running `npm run build` (or in frontend/.env for local dev).",
    );
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let message = `Request failed: ${res.status}`;
    try {
      const body = await res.json();
      // FastAPI's HTTPException serializes as { "detail": "..." }.
      if (body?.detail) message = body.detail;
    } catch {
      // response wasn't JSON; fall back to the generic message
    }
    throw new Error(message);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  listNotices: () => request<{ notices: Notice[] }>("/notices"),

  createNotice: (
    name: string,
    message: string,
    opts: { imageKey?: string | null; expiresIn?: ExpiryOption } = {},
  ) =>
    request<{ notice: Notice }>("/notices", {
      method: "POST",
      body: JSON.stringify({
        name,
        message,
        image_key: opts.imageKey ?? null,
        expires_in: opts.expiresIn ?? "never",
      }),
    }),

  deleteNotice: (id: string) =>
    request<{ deleted: string }>(`/notices/${id}`, { method: "DELETE" }),

  uploadImage: async (file: File): Promise<{ key: string }> => {
    if (!API_URL) {
      throw new Error("VITE_API_URL is not set.");
    }
    const form = new FormData();
    form.append("file", file);

    const res = await fetch(`${API_URL}/uploads`, { method: "POST", body: form });
    if (!res.ok) {
      let message = `Upload failed: ${res.status}`;
      try {
        const body = await res.json();
        if (body?.detail) message = body.detail;
      } catch {
        // ignore, use generic message
      }
      throw new Error(message);
    }
    return res.json();
  },
};
