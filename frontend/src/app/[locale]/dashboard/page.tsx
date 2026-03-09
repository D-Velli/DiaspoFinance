import { currentUser } from "@clerk/nextjs/server";
import { UserButton } from "@clerk/nextjs";
import { getTranslations } from "next-intl/server";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";

export default async function DashboardPage() {
  const user = await currentUser();
  const t = await getTranslations("dashboard");

  return (
    <div className="min-h-screen bg-[#F9FAFB]">
      <header className="border-b border-[#E5E7EB] bg-white">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <span className="text-xl font-bold tracking-tight text-[#0F2B4C]">
            DiaspoFinance
          </span>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <UserButton />
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold text-[#111827]">
          {t("welcome", { name: user?.firstName || "utilisateur" })}
        </h1>
        <p className="mt-2 text-[#374151]">
          {t("placeholder")}
        </p>
      </main>
    </div>
  );
}
