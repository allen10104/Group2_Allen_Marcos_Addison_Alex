import { Clock, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { resolveAssetUrl } from "@/lib/api";
import type { Notice } from "@/types";

interface NoticeCardProps {
  notice: Notice;
  onDelete: (id: string) => void;
  deleting: boolean;
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function formatExpiry(iso: string) {
  const diffMs = new Date(iso).getTime() - Date.now();
  if (diffMs <= 0) return "expiring soon";
  const hours = Math.round(diffMs / (1000 * 60 * 60));
  if (hours < 24) return `expires in ${hours}h`;
  return `expires in ${Math.round(hours / 24)}d`;
}

export function NoticeCard({ notice, onDelete, deleting }: NoticeCardProps) {
  return (
    <Card className="overflow-hidden">
      {notice.image_url && (
        <img
          src={resolveAssetUrl(notice.image_url)}
          alt=""
          className="h-40 w-full object-cover"
        />
      )}
      <CardHeader className="flex-row items-start justify-between space-y-0 pb-2">
        <div>
          <p className="font-semibold leading-none">{notice.name}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {formatDate(notice.created_at)}
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Delete notice"
          disabled={deleting}
          onClick={() => onDelete(notice.id)}
        >
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </CardHeader>
      <CardContent>
        <p className="whitespace-pre-wrap text-sm">{notice.message}</p>
        {notice.expires_at && (
          <p className="mt-3 flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatExpiry(notice.expires_at)}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
