"use client";

import { useTranslations, useLocale } from "next-intl";
import { Link } from "@/i18n/routing";
import { formatCurrency } from "@/lib/utils/format";
import { Users } from "lucide-react";

interface TontineCardProps {
  id: string;
  name: string;
  status: "draft" | "active" | "completed";
  memberCount: number;
  potPerTurnCents: number;
  frequency: "weekly" | "biweekly" | "monthly";
  currency?: string;
}

const statusColors: Record<string, string> = {
  draft: "bg-muted text-muted-foreground",
  active: "bg-green-100 text-green-700",
  completed: "bg-blue-100 text-blue-700",
};

export function TontineCard({
  id,
  name,
  status,
  memberCount,
  potPerTurnCents,
  currency = "CAD",
}: TontineCardProps) {
  const t = useTranslations("tontine.card");
  const locale = useLocale();
  const formatLocale = locale === "fr" ? "fr-CA" : "en-CA";

  const statusLabel =
    status === "draft"
      ? t("draft")
      : status === "active"
        ? t("active")
        : t("completed");

  return (
    <Link
      href={`/tontines/${id}`}
      className="block rounded-xl border border-border bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <h3 className="text-base font-semibold text-foreground">{name}</h3>
        <span
          className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[status]}`}
        >
          {statusLabel}
        </span>
      </div>

      <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <Users className="h-3.5 w-3.5" />
          <span>{t("members", { count: memberCount })}</span>
        </div>
        <div>
          <span className="text-xs text-muted-foreground">{t("potPerTurn")}</span>{" "}
          <span className="font-semibold text-foreground">
            {formatCurrency(potPerTurnCents, currency, formatLocale)}
          </span>
        </div>
      </div>
    </Link>
  );
}
