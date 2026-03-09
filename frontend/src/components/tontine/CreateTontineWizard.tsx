"use client";

import { useState, useCallback } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/routing";
import { useApiFetch } from "@/lib/api-client";
import { StepWizard, type WizardStep } from "./StepWizard";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { formatCurrency } from "@/lib/utils/format";
import { useLocale } from "next-intl";

type Frequency = "weekly" | "biweekly" | "monthly";
type Hands = 0.5 | 1 | 2;

interface FormData {
  name: string;
  handAmountCents: number;
  frequency: Frequency;
  startDate: string;
  maxMembers: string;
  maxPotCents: string;
  reserveEnabled: boolean;
  reservePercentage: string;
  organizerHands: Hands;
}

const MAX_HAND_CENTS = 100_000; // 1000 CAD

const INITIAL_DATA: FormData = {
  name: "",
  handAmountCents: 0,
  frequency: "monthly",
  startDate: "",
  maxMembers: "",
  maxPotCents: "",
  reserveEnabled: false,
  reservePercentage: "2.5",
  organizerHands: 1,
};

export function CreateTontineWizard() {
  const t = useTranslations("tontine.create");
  const locale = useLocale();
  const router = useRouter();
  const { apiFetch } = useApiFetch();

  const [step, setStep] = useState(0);
  const [data, setData] = useState<FormData>(INITIAL_DATA);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const steps: WizardStep[] = [
    { title: t("step1Title"), description: t("step1Desc") },
    { title: t("step2Title"), description: t("step2Desc") },
    { title: t("step3Title"), description: t("step3Desc") },
    { title: t("step4Title"), description: t("step4Desc") },
    { title: t("step5Title"), description: t("step5Desc") },
    { title: t("step6Title"), description: t("step6Desc") },
  ];

  const update = useCallback(
    <K extends keyof FormData>(key: K, value: FormData[K]) => {
      setData((prev) => ({ ...prev, [key]: value }));
      setError(null);
    },
    []
  );

  const canProceed = (): boolean => {
    switch (step) {
      case 0:
        return data.name.trim().length >= 3;
      case 1:
        return data.handAmountCents > 0 && data.handAmountCents <= MAX_HAND_CENTS;
      case 2: {
        if (!data.startDate) return false;
        const selected = new Date(data.startDate + "T00:00:00");
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return selected >= today;
      }
      case 3:
        return true; // limits are optional
      case 4:
        if (data.reserveEnabled) {
          const pct = parseFloat(data.reservePercentage);
          return pct >= 1 && pct <= 5;
        }
        return true;
      case 5:
        return true; // summary step
      default:
        return false;
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        name: data.name.trim(),
        hand_amount_cents: data.handAmountCents,
        frequency: data.frequency,
        start_date: data.startDate,
        max_members: data.maxMembers ? parseInt(data.maxMembers) : null,
        max_pot_cents: data.maxPotCents
          ? Math.round(parseFloat(data.maxPotCents) * 100)
          : null,
        reserve_enabled: data.reserveEnabled,
        reserve_percentage: data.reserveEnabled
          ? parseFloat(data.reservePercentage)
          : null,
        organizer_hands: data.organizerHands,
      };

      const res = await apiFetch<{ id: string }>("/tontines", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      router.push(`/tontines/${res.data.id}`);
    } catch (err: unknown) {
      const apiErr = err as { message?: string; code?: string };
      if (apiErr.code === "PLAFOND_EXCEEDED") {
        setError(t("plafondError"));
      } else if (apiErr.code === "MONTHLY_LIMIT_EXCEEDED") {
        setError(t("monthlyLimitError"));
      } else {
        setError(apiErr.message || "An error occurred");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatLocale = locale === "fr" ? "fr-CA" : "en-CA";

  const contributionPerTurn =
    data.handAmountCents * data.organizerHands;

  const frequencyLabels: Record<Frequency, string> = {
    weekly: t("weekly"),
    biweekly: t("biweekly"),
    monthly: t("monthly"),
  };

  return (
    <StepWizard
      steps={steps}
      currentStep={step}
      onNext={() => setStep((s) => Math.min(s + 1, steps.length - 1))}
      onBack={() => setStep((s) => Math.max(s - 1, 0))}
      isLastStep={step === steps.length - 1}
      canProceed={canProceed()}
      onSubmit={handleSubmit}
      isSubmitting={isSubmitting}
    >
      {/* Step 1: Name */}
      {step === 0 && (
        <div className="space-y-4">
          <div>
            <Label htmlFor="name">{t("nameLabel")}</Label>
            <Input
              id="name"
              value={data.name}
              onChange={(e) => update("name", e.target.value)}
              placeholder={t("namePlaceholder")}
              maxLength={100}
              className="mt-1.5 h-10"
              autoFocus
            />
          </div>
        </div>
      )}

      {/* Step 2: Hand amount */}
      {step === 1 && (
        <div className="space-y-4">
          <div>
            <Label htmlFor="handAmount">{t("handAmountLabel")}</Label>
            <Input
              id="handAmount"
              type="number"
              min={1}
              max={1000}
              value={data.handAmountCents ? data.handAmountCents / 100 : ""}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                update(
                  "handAmountCents",
                  isNaN(val) ? 0 : Math.round(val * 100)
                );
              }}
              placeholder={t("handAmountPlaceholder")}
              className="mt-1.5 h-10"
              autoFocus
            />
            <p className="mt-1.5 text-xs text-muted-foreground">
              {t("handAmountHelp")}
            </p>
          </div>

          <div>
            <Label>{t("yourHandsLabel")}</Label>
            <div className="mt-1.5 flex gap-2">
              {([0.5, 1, 2] as Hands[]).map((h) => {
                const label =
                  h === 0.5
                    ? t("halfHand")
                    : h === 1
                      ? t("oneHand")
                      : t("twoHands");
                const isSelected = data.organizerHands === h;
                return (
                  <button
                    key={h}
                    type="button"
                    onClick={() => update("organizerHands", h)}
                    className={`flex-1 rounded-lg border px-3 py-2.5 text-sm font-medium transition-colors ${
                      isSelected
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border hover:bg-muted"
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Frequency + Start date */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="space-y-2">
            <Label>{t("frequencyLabel")}</Label>
            <div className="mt-1.5 space-y-2">
              {(["weekly", "biweekly", "monthly"] as Frequency[]).map((freq) => {
                const isSelected = data.frequency === freq;
                return (
                  <button
                    key={freq}
                    type="button"
                    onClick={() => update("frequency", freq)}
                    className={`flex w-full items-center rounded-lg border px-4 py-3 text-left text-sm font-medium transition-colors ${
                      isSelected
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border hover:bg-muted"
                    }`}
                  >
                    <div
                      className={`mr-3 h-4 w-4 rounded-full border-2 ${
                        isSelected
                          ? "border-primary bg-primary"
                          : "border-muted-foreground/40"
                      }`}
                    >
                      {isSelected && (
                        <div className="m-0.5 h-2 w-2 rounded-full bg-white" />
                      )}
                    </div>
                    {frequencyLabels[freq]}
                  </button>
                );
              })}
            </div>
          </div>

          <Separator />

          <div>
            <Label htmlFor="startDate">{t("startDateLabel")}</Label>
            <input
              id="startDate"
              type="date"
              value={data.startDate}
              min={new Date().toISOString().split("T")[0]}
              onChange={(e) => update("startDate", e.target.value)}
              className="mt-1.5 h-10 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
            <p className="mt-1.5 text-xs text-muted-foreground">
              {t("startDateHelp")}
            </p>
            {data.startDate && (
              <p className="mt-1 text-xs font-medium text-primary">
                {getDateHint(data.startDate, data.frequency, formatLocale, t)}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Step 4: Limits */}
      {step === 3 && (
        <div className="space-y-4">
          <div>
            <Label htmlFor="maxMembers">{t("maxMembersLabel")}</Label>
            <Input
              id="maxMembers"
              type="number"
              min={2}
              value={data.maxMembers}
              onChange={(e) => update("maxMembers", e.target.value)}
              placeholder={t("maxMembersPlaceholder")}
              className="mt-1.5 h-10"
            />
          </div>
          <div>
            <Label htmlFor="maxPot">{t("maxPotLabel")}</Label>
            <Input
              id="maxPot"
              type="number"
              min={1}
              value={data.maxPotCents}
              onChange={(e) => update("maxPotCents", e.target.value)}
              placeholder={t("maxPotPlaceholder")}
              className="mt-1.5 h-10"
            />
          </div>
        </div>
      )}

      {/* Step 5: Security reserve */}
      {step === 4 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>{t("reserveLabel")}</Label>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {t("reserveHelp")}
              </p>
            </div>
            <Switch
              checked={data.reserveEnabled}
              onCheckedChange={(checked) =>
                update("reserveEnabled", checked)
              }
            />
          </div>
          {data.reserveEnabled && (
            <div>
              <Label htmlFor="reservePct">{t("reservePercentLabel")}</Label>
              <div className="mt-1.5 flex items-center gap-2">
                <Input
                  id="reservePct"
                  type="number"
                  min={1}
                  max={5}
                  step={0.5}
                  value={data.reservePercentage}
                  onChange={(e) =>
                    update("reservePercentage", e.target.value)
                  }
                  className="h-10 w-24"
                />
                <span className="text-sm text-muted-foreground">%</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Step 6: Summary */}
      {step === 5 && (
        <div className="space-y-4">
          <h3 className="font-semibold text-foreground">{t("summary")}</h3>

          <div className="space-y-3 rounded-lg bg-muted/50 p-4">
            <SummaryRow label={t("nameLabel")} value={data.name} />
            <Separator />
            <SummaryRow
              label={t("handAmount")}
              value={formatCurrency(data.handAmountCents, "CAD", formatLocale)}
            />
            <Separator />
            <SummaryRow
              label={t("frequency")}
              value={frequencyLabels[data.frequency]}
            />
            <Separator />
            <SummaryRow
              label={t("startDate")}
              value={
                data.startDate
                  ? new Date(data.startDate + "T00:00:00").toLocaleDateString(
                      formatLocale,
                      { day: "numeric", month: "long", year: "numeric" }
                    )
                  : "—"
              }
            />
            <Separator />
            <SummaryRow
              label={t("maxMembers")}
              value={data.maxMembers || t("unlimited")}
            />
            {data.reserveEnabled && (
              <>
                <Separator />
                <SummaryRow
                  label={t("reserve")}
                  value={`${data.reservePercentage}%`}
                />
              </>
            )}
            <Separator />
            <SummaryRow
              label={t("yourHandsLabel")}
              value={
                data.organizerHands === 0.5
                  ? t("halfHand")
                  : data.organizerHands === 1
                    ? t("oneHand")
                    : t("twoHands")
              }
            />
            <Separator />
            <div className="flex items-center justify-between pt-1">
              <span className="text-sm font-semibold text-foreground">
                {t("yourContribution")}
              </span>
              <span className="text-lg font-bold text-primary">
                {formatCurrency(contributionPerTurn, "CAD", formatLocale)}
              </span>
            </div>
          </div>

          {error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
        </div>
      )}
    </StepWizard>
  );
}

function SummaryRow({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

const DAY_NAMES_FR = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];
const DAY_NAMES_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

function getDateHint(
  dateStr: string,
  frequency: Frequency,
  locale: string,
  t: (key: string, values?: Record<string, string | number>) => string,
): string {
  const d = new Date(dateStr + "T00:00:00");
  const dayOfMonth = d.getDate();
  const dayOfWeek = d.getDay();
  const dayNames = locale.startsWith("fr") ? DAY_NAMES_FR : DAY_NAMES_EN;
  const formattedDate = d.toLocaleDateString(locale, {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  switch (frequency) {
    case "monthly":
      return t("startDateHintMonthly", { day: dayOfMonth });
    case "weekly":
      return t("startDateHintWeekly", { dayOfWeek: dayNames[dayOfWeek] });
    case "biweekly":
      return t("startDateHintBiweekly", { date: formattedDate });
  }
}
