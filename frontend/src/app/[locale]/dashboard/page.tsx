import { currentUser } from "@clerk/nextjs/server";
import { UserButton } from "@clerk/nextjs";
import { getTranslations } from "next-intl/server";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { Link } from "@/i18n/routing";
import { Plus } from "lucide-react";
import { TontineList } from "@/components/tontine/TontineList";

export default async function DashboardPage() {
  const user = await currentUser();
  const t = await getTranslations("dashboard");
  const tTontine = await getTranslations("tontine.create");

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-white">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <span className="text-xl font-bold tracking-tight text-secondary-foreground">
            DiaspoFinance
          </span>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <UserButton />
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-foreground">
            {t("welcome", { name: user?.firstName || t("defaultUser") })}
          </h1>
          <Link
            href="/tontines/new"
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-white hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            {tTontine("title")}
          </Link>
        </div>
        <TontineList />
      </main>
    </div>
  );
}
