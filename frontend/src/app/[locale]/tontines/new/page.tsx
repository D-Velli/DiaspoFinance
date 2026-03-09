"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { UserButton } from "@clerk/nextjs";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { CreateTontineWizard } from "@/components/tontine/CreateTontineWizard";
import { ArrowLeft } from "lucide-react";

export default function NewTontinePage() {
  const t = useTranslations("tontine.create");

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex h-8 w-8 items-center justify-center rounded-lg hover:bg-muted"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <span className="text-xl font-bold tracking-tight text-secondary-foreground">
              DiaspoFinance
            </span>
          </div>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <UserButton />
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="mb-8 text-2xl font-bold text-foreground">{t("title")}</h1>
        <CreateTontineWizard />
      </main>
    </div>
  );
}
