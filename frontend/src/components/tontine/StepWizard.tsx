"use client";

import { cn } from "@/lib/utils";
import { useTranslations } from "next-intl";
import { Check } from "lucide-react";

export interface WizardStep {
  title: string;
  description: string;
}

interface StepWizardProps {
  steps: WizardStep[];
  currentStep: number;
  children: React.ReactNode;
  onNext: () => void;
  onBack: () => void;
  isLastStep: boolean;
  canProceed: boolean;
  onSubmit?: () => void;
  isSubmitting?: boolean;
}

export function StepWizard({
  steps,
  currentStep,
  children,
  onNext,
  onBack,
  isLastStep,
  canProceed,
  onSubmit,
  isSubmitting,
}: StepWizardProps) {
  const t = useTranslations("common");

  return (
    <div className="mx-auto max-w-2xl">
      {/* Step indicators */}
      <nav aria-label="Progress" className="mb-8">
        <ol className="flex items-center gap-2">
          {steps.map((step, index) => {
            const isCompleted = index < currentStep;
            const isCurrent = index === currentStep;

            return (
              <li key={step.title} className="flex flex-1 items-center gap-2">
                <div className="flex flex-col items-center gap-1.5">
                  <div
                    className={cn(
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-colors",
                      isCompleted && "bg-primary text-white",
                      isCurrent &&
                        "border-2 border-primary bg-white text-primary",
                      !isCompleted &&
                        !isCurrent &&
                        "border border-border bg-muted text-muted-foreground"
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      index + 1
                    )}
                  </div>
                  <span
                    className={cn(
                      "hidden text-center text-xs sm:block",
                      isCurrent
                        ? "font-medium text-foreground"
                        : "text-muted-foreground"
                    )}
                  >
                    {step.title}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      "mb-5 h-px flex-1",
                      isCompleted ? "bg-primary" : "bg-border"
                    )}
                  />
                )}
              </li>
            );
          })}
        </ol>
      </nav>

      {/* Step content */}
      <div className="rounded-xl border border-border bg-white p-6 shadow-sm">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-foreground">
            {steps[currentStep].title}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {steps[currentStep].description}
          </p>
        </div>

        {children}

        {/* Navigation */}
        <div className="mt-8 flex items-center justify-between">
          <button
            type="button"
            onClick={onBack}
            disabled={currentStep === 0}
            className={cn(
              "inline-flex h-10 items-center justify-center rounded-lg border border-border px-4 text-sm font-medium transition-colors",
              currentStep === 0
                ? "cursor-not-allowed opacity-50"
                : "hover:bg-muted"
            )}
          >
            {t("back")}
          </button>

          {isLastStep ? (
            <button
              type="button"
              onClick={onSubmit}
              disabled={!canProceed || isSubmitting}
              className="inline-flex h-10 items-center justify-center rounded-lg bg-primary px-6 text-sm font-semibold text-white transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? t("loading") : t("confirm")}
            </button>
          ) : (
            <button
              type="button"
              onClick={onNext}
              disabled={!canProceed}
              className="inline-flex h-10 items-center justify-center rounded-lg bg-primary px-6 text-sm font-semibold text-white transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("next")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
