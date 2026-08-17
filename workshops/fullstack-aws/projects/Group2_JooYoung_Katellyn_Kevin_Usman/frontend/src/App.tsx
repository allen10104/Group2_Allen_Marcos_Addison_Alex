import { useEffect, useState } from "react";
import { Loader2, Pin, RefreshCw } from "lucide-react";

import { NoticeForm } from "@/components/NoticeForm";
import { NoticeList } from "@/components/NoticeList";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { ExpiryOption, Notice } from "@/types";

function App() {
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function loadNotices(opts: { silent?: boolean } = {}) {
    if (opts.silent) setRefreshing(true);
    setLoadError(null);
    try {
      const { notices } = await api.listNotices();
      setNotices(notices);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load notices");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadNotices();
  }, []);

  async function handleCreate(
    name: string,
    message: string,
    opts: { imageFile: File | null; expiresIn: ExpiryOption },
  ) {
    let imageKey: string | null = null;
    if (opts.imageFile) {
      const uploaded = await api.uploadImage(opts.imageFile);
      imageKey = uploaded.key;
    }
    const { notice } = await api.createNotice(name, message, {
      imageKey,
      expiresIn: opts.expiresIn,
    });
    setNotices((prev) => [notice, ...prev]);
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    const previous = notices;
    setNotices((prev) => prev.filter((n) => n.id !== id));
    try {
      await api.deleteNotice(id);
    } catch (err) {
      setNotices(previous); // roll back on failure
      setLoadError(err instanceof Error ? err.message : "Failed to delete notice");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <div className="container max-w-4xl py-10">
        <header className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Pin className="h-6 w-6" />
            <h1 className="text-3xl font-bold tracking-tight">Notice Board</h1>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadNotices({ silent: true })}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </header>

        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-lg">Post a notice</CardTitle>
          </CardHeader>
          <CardContent>
            <NoticeForm onSubmit={handleCreate} />
          </CardContent>
        </Card>

        {loadError && (
          <p className="mb-4 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
            {loadError}
          </p>
        )}

        {loading ? (
          <div className="flex items-center justify-center gap-2 p-12 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            Loading notices…
          </div>
        ) : (
          <NoticeList notices={notices} onDelete={handleDelete} deletingId={deletingId} />
        )}
      </div>
    </div>
  );
}

export default App;
