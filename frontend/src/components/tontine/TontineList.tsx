"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useApiFetch } from "@/lib/api-client";
import { TontineCard } from "./TontineCard";

interface TontineData {
  id: string;
  name: string;
  status: "draft" | "active" | "completed";
  member_count: number;
  pot_per_turn_cents: number;
  frequency: "weekly" | "biweekly" | "monthly";
  currency: string;
}

export function TontineList() {
  const { apiFetch } = useApiFetch();
  const t = useTranslations("dashboard");
  const [tontines, setTontines] = useState<TontineData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch<TontineData[]>("/tontines");
        setTontines(res.data);
      } catch {
        // silently fail — empty list
      } finally {
        setLoading(false);
      }
    })();
  }, [apiFetch]);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (tontines.length === 0) {
    return (
      <p className="mt-2 text-muted-foreground">{t("empty")}</p>
    );
  }

  return (
    <div className="mt-6 grid gap-4 sm:grid-cols-2">
      {tontines.map((t) => (
        <TontineCard
          key={t.id}
          id={t.id}
          name={t.name}
          status={t.status}
          memberCount={t.member_count}
          potPerTurnCents={t.pot_per_turn_cents}
          frequency={t.frequency}
          currency={t.currency}
        />
      ))}
    </div>
  );
}
