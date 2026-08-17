import { useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { ImagePlus, Loader2, Send, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { EXPIRY_OPTIONS, type ExpiryOption } from "@/types";
import { cn } from "@/lib/utils";

interface NoticeFormProps {
  onSubmit: (
    name: string,
    message: string,
    opts: { imageFile: File | null; expiresIn: ExpiryOption },
  ) => Promise<void>;
}

export function NoticeForm({ onSubmit }: NoticeFormProps) {
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [expiresIn, setExpiresIn] = useState<ExpiryOption>("never");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    setImageFile(e.target.files?.[0] ?? null);
  }

  function clearImage() {
    setImageFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim() || !message.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(name.trim(), message.trim(), { imageFile, expiresIn });
      setName("");
      setMessage("");
      setExpiresIn("never");
      clearImage();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Your name</Label>
        <Input
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Jane Doe"
          maxLength={80}
          disabled={submitting}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="message">Notice</Label>
        <Textarea
          id="message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="What do you want to post to the board?"
          maxLength={500}
          disabled={submitting}
          required
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="expires">Expires</Label>
          <select
            id="expires"
            value={expiresIn}
            onChange={(e) => setExpiresIn(e.target.value as ExpiryOption)}
            disabled={submitting}
            className={cn(
              "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              "disabled:cursor-not-allowed disabled:opacity-50",
            )}
          >
            {EXPIRY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="image">Image (optional)</Label>
          {imageFile ? (
            <div className="flex h-10 items-center justify-between rounded-md border border-input px-3 text-sm">
              <span className="truncate">{imageFile.name}</span>
              <button
                type="button"
                onClick={clearImage}
                disabled={submitting}
                aria-label="Remove image"
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <Button
              type="button"
              variant="outline"
              className="h-10 w-full justify-start text-muted-foreground font-normal"
              disabled={submitting}
              onClick={() => fileInputRef.current?.click()}
            >
              <ImagePlus className="h-4 w-4" />
              Attach an image
            </Button>
          )}
          <input
            ref={fileInputRef}
            id="image"
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            onChange={handleFileChange}
            disabled={submitting}
            className="hidden"
          />
        </div>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Button type="submit" disabled={submitting} className="w-full sm:w-auto">
        {submitting ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
        Post notice
      </Button>
    </form>
  );
}
