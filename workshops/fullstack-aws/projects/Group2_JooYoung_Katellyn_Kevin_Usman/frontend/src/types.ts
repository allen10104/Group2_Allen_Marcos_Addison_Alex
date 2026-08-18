export interface Notice {
  id: string;
  name: string;
  message: string;
  image_url: string | null;
  expires_at: string | null;
  created_at: string;
}

export type ExpiryOption = "never" | "1d" | "3d" | "1w";

export const EXPIRY_OPTIONS: { value: ExpiryOption; label: string }[] = [
  { value: "never", label: "Never" },
  { value: "1d", label: "1 day" },
  { value: "3d", label: "3 days" },
  { value: "1w", label: "1 week" },
];
