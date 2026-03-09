"use client";

import { useLocale, useTranslations } from "next-intl";
import { formatRelativeTime } from "@/lib/utils/format";
import { Trash2 } from "lucide-react";

interface Author {
  id: string;
  display_name: string;
}

export interface AnnouncementData {
  id: string;
  author: Author;
  content: string;
  created_at: string;
}

export function AnnouncementCard({
  announcement,
  isOrganizer,
  onDelete,
}: {
  announcement: AnnouncementData;
  isOrganizer: boolean;
  onDelete?: (id: string) => void;
}) {
  const t = useTranslations("tontine.announcements");
  const locale = useLocale();
  const formatLocale = locale === "fr" ? "fr-CA" : "en-CA";

  const initials = announcement.author.display_name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="rounded-lg border border-border bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          {/* Avatar */}
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
            {initials}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-foreground">
                {announcement.author.display_name}
              </span>
              <span className="text-xs text-muted-foreground">
                {formatRelativeTime(new Date(announcement.created_at), formatLocale)}
              </span>
            </div>
            <p className="mt-1 whitespace-pre-wrap text-sm text-foreground">
              {announcement.content}
            </p>
          </div>
        </div>
        {isOrganizer && onDelete && (
          <button
            onClick={() => onDelete(announcement.id)}
            className="shrink-0 rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            title={t("delete")}
          >
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
