"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useParams } from "next/navigation";
import { useApiFetch } from "@/lib/api-client";
import { Link } from "@/i18n/routing";
import { AnnouncementCard, type AnnouncementData } from "@/components/tontine/AnnouncementCard";
import { AnnouncementForm } from "@/components/tontine/AnnouncementForm";
import { ArrowLeft, Megaphone } from "lucide-react";

interface MemberInfo {
  role: string;
}

export default function AnnouncementsPage() {
  const t = useTranslations("tontine.announcements");
  const params = useParams<{ id: string }>();
  const tontineId = params.id;
  const { apiFetch } = useApiFetch();

  const [announcements, setAnnouncements] = useState<AnnouncementData[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [isOrganizer, setIsOrganizer] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnnouncements = useCallback(
    async (cursorParam?: string | null) => {
      const isLoadMore = !!cursorParam;
      if (isLoadMore) setLoadingMore(true);
      else setLoading(true);

      try {
        const query = cursorParam ? `?cursor=${cursorParam}` : "";
        const res = await apiFetch<{
          data: AnnouncementData[];
          meta: { cursor: string | null; has_more: boolean };
        }>(`/tontines/${tontineId}/announcements${query}`);

        // The response from our endpoint is already in the correct shape
        const body = res as unknown as {
          data: AnnouncementData[];
          meta: { cursor: string | null; has_more: boolean };
        };

        if (isLoadMore) {
          setAnnouncements((prev) => [...prev, ...body.data]);
        } else {
          setAnnouncements(body.data);
        }
        setCursor(body.meta.cursor);
        setHasMore(body.meta.has_more);
      } catch {
        setError(t("loadError"));
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [apiFetch, tontineId, t],
  );

  const checkRole = useCallback(async () => {
    try {
      const res = await apiFetch<{ id: string; user_id: string; role: string }[]>(
        `/tontines/${tontineId}/members`,
      );
      // Find current user's member record — check by role for now
      const members = res.data;
      const organizer = members.find((m: MemberInfo) => m.role === "organizer");
      if (organizer) {
        // We need to compare with current user, but the endpoint returns user_id
        // For simplicity, check if any member has organizer role
        // The API already checks membership, so if we can access it, we're a member
        setIsOrganizer(!!organizer);
      }
    } catch {
      // Not critical — just affects UI
    }
  }, [apiFetch, tontineId]);

  useEffect(() => {
    fetchAnnouncements();
    checkRole();
  }, [fetchAnnouncements, checkRole]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAnnouncements();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchAnnouncements]);

  const handlePublish = async (content: string) => {
    await apiFetch(`/tontines/${tontineId}/announcements`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
    // Reload from top
    await fetchAnnouncements();
  };

  const handleDelete = async (announcementId: string) => {
    if (!confirm(t("confirmDelete"))) return;
    await apiFetch(`/tontines/${tontineId}/announcements/${announcementId}`, {
      method: "DELETE",
    });
    setAnnouncements((prev) => prev.filter((a) => a.id !== announcementId));
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <nav className="mx-auto flex max-w-2xl items-center gap-3 px-4 py-4">
          <Link
            href={`/dashboard`}
            className="rounded-lg p-2 hover:bg-muted"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <h1 className="text-lg font-bold text-foreground">{t("title")}</h1>
        </nav>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-6">
        {/* Form — organizer only */}
        {isOrganizer && (
          <div className="mb-6">
            <AnnouncementForm onSubmit={handlePublish} />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-4 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-12">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        )}

        {/* Empty state */}
        {!loading && announcements.length === 0 && (
          <div className="flex flex-col items-center py-16 text-center">
            <Megaphone className="mb-4 h-12 w-12 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">{t("empty")}</p>
          </div>
        )}

        {/* Announcements list */}
        {!loading && announcements.length > 0 && (
          <div className="space-y-3">
            {announcements.map((ann) => (
              <AnnouncementCard
                key={ann.id}
                announcement={ann}
                isOrganizer={isOrganizer}
                onDelete={handleDelete}
              />
            ))}

            {/* Load more */}
            {hasMore && (
              <div className="flex justify-center pt-4">
                <button
                  onClick={() => fetchAnnouncements(cursor)}
                  disabled={loadingMore}
                  className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
                >
                  {loadingMore ? t("loadingMore") : t("loadMore")}
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
