"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useParams, useRouter } from "next/navigation";
import { useApiFetch } from "@/lib/api-client";
import { Link } from "@/i18n/routing";
import { formatCurrency, formatDate } from "@/lib/utils/format";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  Calendar,
  Lock,
} from "lucide-react";

interface PreStartCheck {
  code: string;
  message: string;
  severity: "error" | "warning";
}

interface PreStartData {
  can_start: boolean;
  blockers: PreStartCheck[];
  warnings: PreStartCheck[];
}

interface RoundData {
  id: string;
  round_number: number;
  beneficiary_user_id: string;
  beneficiary_display_name: string;
  beneficiary_hands: number;
  expected_collection_date: string;
  expected_distribution_date: string;
  status: string;
  pot_expected_amount_cents: number;
}

export default function StartCyclePage() {
  const t = useTranslations("tontine.start");
  const tCommon = useTranslations("common");
  const locale = useLocale();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const tontineId = params.id;
  const { apiFetch } = useApiFetch();
  const formatLocale = locale === "fr" ? "fr-CA" : "en-CA";

  const [checks, setChecks] = useState<PreStartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [rounds, setRounds] = useState<RoundData[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchChecks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch<PreStartData>(
        `/tontines/${tontineId}/pre-start-checks`,
      );
      setChecks(res.data);
    } catch {
      setError(t("loadError"));
    } finally {
      setLoading(false);
    }
  }, [apiFetch, tontineId, t]);

  useEffect(() => {
    fetchChecks();
    // Set default start date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setStartDate(tomorrow.toISOString().split("T")[0]);
  }, [fetchChecks]);

  const handleStart = async () => {
    setStarting(true);
    setError(null);
    try {
      const res = await apiFetch<{ rounds: RoundData[] }>(
        `/tontines/${tontineId}/start`,
        {
          method: "POST",
          body: JSON.stringify({ cycle_start_date: startDate || null }),
        },
      );
      setRounds(res.data.rounds);
      setShowConfirm(false);
    } catch (err: unknown) {
      const apiErr = err as { code?: string; message?: string };
      setError(apiErr?.message || t("startError"));
    } finally {
      setStarting(false);
    }
  };

  // Post-start: show rounds calendar
  if (rounds) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b border-border bg-white">
          <nav className="mx-auto flex max-w-2xl items-center gap-3 px-4 py-4">
            <Link href="/dashboard" className="rounded-lg p-2 hover:bg-muted">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <h1 className="text-lg font-bold text-foreground">
              {t("success")}
            </h1>
          </nav>
        </header>
        <main className="mx-auto max-w-2xl px-4 py-6">
          <div className="mb-4 flex items-center gap-2 rounded-lg bg-green-50 p-3 text-sm text-green-700">
            <CheckCircle2 className="h-5 w-5" />
            {t("cycleStarted")}
          </div>
          <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
            <Lock className="h-4 w-4" />
            {t("locked")}
          </div>
          <h2 className="mb-4 flex items-center gap-2 text-base font-semibold">
            <Calendar className="h-5 w-5" />
            {t("roundsTitle")}
          </h2>
          <div className="space-y-2">
            {rounds.map((r) => (
              <div
                key={r.id}
                className="flex items-center justify-between rounded-lg border border-border bg-white p-3"
              >
                <div>
                  <span className="text-xs font-medium text-muted-foreground">
                    {t("roundNumber", { n: r.round_number })}
                  </span>
                  <p className="text-sm font-semibold">
                    {r.beneficiary_display_name}
                    {r.beneficiary_hands !== 1 &&
                      ` (${r.beneficiary_hands} ${r.beneficiary_hands === 0.5 ? "½" : ""} main${r.beneficiary_hands > 1 ? "s" : ""})`}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">
                    {formatDate(r.expected_distribution_date, formatLocale, "short")}
                  </p>
                  <p className="text-xs font-medium text-primary">
                    {formatCurrency(r.pot_expected_amount_cents, "CAD", formatLocale)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <nav className="mx-auto flex max-w-2xl items-center gap-3 px-4 py-4">
          <Link href="/dashboard" className="rounded-lg p-2 hover:bg-muted">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <h1 className="text-lg font-bold text-foreground">{t("title")}</h1>
        </nav>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-6">
        {error && (
          <div className="mb-4 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex justify-center py-12">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        )}

        {checks && (
          <>
            {/* Checklist */}
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-foreground">
                {t("checklist")}
              </h2>

              {checks.blockers.map((b) => (
                <div
                  key={b.code}
                  className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-3"
                >
                  <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
                  <p className="text-sm text-red-700">{b.message}</p>
                </div>
              ))}

              {checks.warnings.map((w) => (
                <div
                  key={w.code}
                  className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3"
                >
                  <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" />
                  <p className="text-sm text-amber-700">{w.message}</p>
                </div>
              ))}

              {checks.blockers.length === 0 && (
                <div className="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-3">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-green-500" />
                  <p className="text-sm text-green-700">{t("allGood")}</p>
                </div>
              )}
            </div>

            {/* Start date */}
            <div className="mt-6">
              <label className="block text-sm font-medium text-foreground">
                {t("startDate")}
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                min={new Date().toISOString().split("T")[0]}
                className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
              />
            </div>

            {/* Start button */}
            <button
              onClick={() => setShowConfirm(true)}
              disabled={!checks.can_start}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 py-3 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Play className="h-4 w-4" />
              {t("button")}
            </button>
          </>
        )}

        {/* Confirmation modal */}
        {showConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-sm rounded-2xl bg-white p-6">
              <h3 className="text-lg font-bold">{t("confirmTitle")}</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {t("confirmMessage")}
              </p>
              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => setShowConfirm(false)}
                  className="flex-1 rounded-lg border border-border py-2.5 text-sm font-medium hover:bg-muted"
                >
                  {tCommon("cancel")}
                </button>
                <button
                  onClick={handleStart}
                  disabled={starting}
                  className="flex-1 rounded-lg bg-green-600 py-2.5 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50"
                >
                  {starting ? tCommon("loading") : t("button")}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
