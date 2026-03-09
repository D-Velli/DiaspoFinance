"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useParams } from "next/navigation";
import { useApiFetch } from "@/lib/api-client";
import { Link } from "@/i18n/routing";
import { formatCurrency, formatDate } from "@/lib/utils/format";
import {
  ArrowLeft,
  Calendar,
  Copy,
  Check,
  Link2,
  Megaphone,
  Play,
  Shuffle,
  Users,
} from "lucide-react";

interface TontineDetail {
  id: string;
  name: string;
  status: string;
  hand_amount_cents: number;
  frequency: string;
  start_date: string | null;
  max_members: number | null;
  currency: string;
  reserve_enabled: boolean;
  reserve_percentage: number | null;
  invite_code: string | null;
  member_count: number;
  total_hands: number;
  pot_per_turn_cents: number;
}

interface MemberData {
  id: string;
  user_id: string;
  display_name: string;
  role: string;
  status: string;
  hands: number;
  turn_position: number | null;
}

const statusColors: Record<string, string> = {
  draft: "bg-muted text-muted-foreground",
  active: "bg-green-100 text-green-700",
  collecting: "bg-amber-100 text-amber-700",
  distributing: "bg-blue-100 text-blue-700",
  completed: "bg-blue-100 text-blue-700",
  cancelled: "bg-red-100 text-red-700",
};

export default function TontineDetailPage() {
  const t = useTranslations("tontine.detail");
  const tCard = useTranslations("tontine.card");
  const tCreate = useTranslations("tontine.create");
  const locale = useLocale();
  const params = useParams<{ id: string }>();
  const tontineId = params.id;
  const { apiFetch } = useApiFetch();
  const formatLocale = locale === "fr" ? "fr-CA" : "en-CA";

  const [tontine, setTontine] = useState<TontineDetail | null>(null);
  const [members, setMembers] = useState<MemberData[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [generatingInvite, setGeneratingInvite] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [tRes, mRes] = await Promise.all([
        apiFetch<TontineDetail>(`/tontines/${tontineId}`),
        apiFetch<MemberData[]>(`/tontines/${tontineId}/members`),
      ]);
      setTontine(tRes.data);
      setMembers(mRes.data);
    } catch {
      // handled by empty state
    } finally {
      setLoading(false);
    }
  }, [apiFetch, tontineId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleGenerateInvite = async () => {
    setGeneratingInvite(true);
    try {
      const res = await apiFetch<{ invite_code: string }>(
        `/tontines/${tontineId}/invite`,
        { method: "POST" },
      );
      setTontine((prev) =>
        prev ? { ...prev, invite_code: res.data.invite_code } : prev,
      );
    } catch {
      // silently fail
    } finally {
      setGeneratingInvite(false);
    }
  };

  const handleCopyInvite = async () => {
    if (!tontine?.invite_code) return;
    const url = `${window.location.origin}/${locale}/invite/${tontine.invite_code}`;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const freqLabel = (f: string) => {
    const labels: Record<string, string> = {
      weekly: tCreate("weekly"),
      biweekly: tCreate("biweekly"),
      monthly: tCreate("monthly"),
    };
    return labels[f] || f;
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!tontine) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground">Tontine introuvable</p>
      </div>
    );
  }

  const isDraft = tontine.status === "draft";
  const isActive = tontine.status === "active";
  const organizer = members.find((m) => m.role === "organizer");
  const sortedMembers = [...members].sort(
    (a, b) => (a.turn_position ?? 999) - (b.turn_position ?? 999),
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white">
        <nav className="mx-auto flex max-w-2xl items-center gap-3 px-4 py-4">
          <Link href="/dashboard" className="rounded-lg p-2 hover:bg-muted">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-lg font-bold text-foreground">
              {tontine.name}
            </h1>
          </div>
          <span
            className={`inline-flex shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[tontine.status] || statusColors.draft}`}
          >
            {tCard(tontine.status as "draft" | "active" | "completed")}
          </span>
        </nav>
      </header>

      <main className="mx-auto max-w-2xl space-y-6 px-4 py-6">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg border border-border bg-white p-4 text-center">
            <p className="text-2xl font-bold text-foreground">
              {tontine.member_count}
            </p>
            <p className="text-xs text-muted-foreground">{t("members")}</p>
          </div>
          <div className="rounded-lg border border-border bg-white p-4 text-center">
            <p className="text-2xl font-bold text-primary">
              {formatCurrency(tontine.pot_per_turn_cents, tontine.currency, formatLocale)}
            </p>
            <p className="text-xs text-muted-foreground">{t("potPerTurn")}</p>
          </div>
          <div className="rounded-lg border border-border bg-white p-4 text-center">
            <p className="text-2xl font-bold text-foreground">
              {freqLabel(tontine.frequency)}
            </p>
            <p className="text-xs text-muted-foreground">{t("frequency")}</p>
          </div>
        </div>

        {/* Info */}
        <div className="rounded-lg border border-border bg-white p-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{t("handAmount")}</span>
              <span className="font-medium">
                {formatCurrency(tontine.hand_amount_cents, tontine.currency, formatLocale)}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{t("totalHands")}</span>
              <span className="font-medium">{tontine.total_hands}</span>
            </div>
            {tontine.start_date && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{t("startDate")}</span>
                <span className="font-medium">
                  {formatDate(tontine.start_date, formatLocale, "long")}
                </span>
              </div>
            )}
            {tontine.reserve_enabled && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{t("reserve")}</span>
                <span className="font-medium">{tontine.reserve_percentage}%</span>
              </div>
            )}
          </div>
        </div>

        {/* Invite link */}
        {isDraft && (
          <div className="rounded-lg border border-border bg-white p-4">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <Link2 className="h-4 w-4" />
              {t("inviteLink")}
            </h2>
            {tontine.invite_code ? (
              <div className="mt-3 flex gap-2">
                <div className="flex-1 truncate rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                  {typeof window !== "undefined"
                    ? `${window.location.origin}/${locale}/invite/${tontine.invite_code}`
                    : `…/invite/${tontine.invite_code}`}
                </div>
                <button
                  onClick={handleCopyInvite}
                  className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-xs font-medium hover:bg-muted"
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-green-600" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                  {copied ? t("copied") : t("copy")}
                </button>
              </div>
            ) : (
              <button
                onClick={handleGenerateInvite}
                disabled={generatingInvite}
                className="mt-3 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary/90 disabled:opacity-50"
              >
                {t("generateLink")}
              </button>
            )}
            {isActive && (
              <p className="mt-2 text-xs text-muted-foreground">{t("closedMemberships")}</p>
            )}
          </div>
        )}

        {/* Members */}
        <div className="rounded-lg border border-border bg-white p-4">
          <h2 className="flex items-center gap-2 text-sm font-semibold">
            <Users className="h-4 w-4" />
            {t("membersList")} ({members.length})
          </h2>
          <div className="mt-3 space-y-2">
            {sortedMembers.map((m) => {
              const initials = m.display_name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()
                .slice(0, 2);
              return (
                <div
                  key={m.id}
                  className="flex items-center justify-between rounded-md border border-border px-3 py-2"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                      {initials}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{m.display_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {m.role === "organizer" ? t("organizer") : t("member")}
                        {" · "}
                        {m.hands === 0.5 ? "½" : m.hands} {m.hands <= 1 ? t("hand") : t("hands")}
                      </p>
                    </div>
                  </div>
                  {m.turn_position && (
                    <span className="rounded bg-muted px-2 py-0.5 text-xs font-medium">
                      #{m.turn_position}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          {isDraft && (
            <>
              <Link
                href={`/tontines/${tontineId}/start`}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 py-3 text-sm font-semibold text-white hover:bg-green-700"
              >
                <Play className="h-4 w-4" />
                {t("startCycle")}
              </Link>
            </>
          )}

          <Link
            href={`/tontines/${tontineId}/announcements`}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-border py-3 text-sm font-medium hover:bg-muted"
          >
            <Megaphone className="h-4 w-4" />
            {t("announcements")}
          </Link>

          {(isDraft || isActive) && (
            <Link
              href={`/tontines/${tontineId}/rounds`}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-border py-3 text-sm font-medium hover:bg-muted"
            >
              <Calendar className="h-4 w-4" />
              {t("viewRounds")}
            </Link>
          )}
        </div>
      </main>
    </div>
  );
}
