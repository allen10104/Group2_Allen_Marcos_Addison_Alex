import { NoticeCard } from "@/components/NoticeCard";
import type { Notice } from "@/types";

interface NoticeListProps {
  notices: Notice[];
  onDelete: (id: string) => void;
  deletingId: string | null;
}

export function NoticeList({ notices, onDelete, deletingId }: NoticeListProps) {
  if (notices.length === 0) {
    return (
      <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
        No notices yet. Be the first to post one.
      </p>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {notices.map((notice) => (
        <NoticeCard
          key={notice.id}
          notice={notice}
          onDelete={onDelete}
          deleting={deletingId === notice.id}
        />
      ))}
    </div>
  );
}
