"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRouter, usePathname } from "@/i18n/routing";

export function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations("profile");

  const otherLocale = locale === "fr" ? "en" : "fr";
  const label = locale === "fr" ? t("english") : t("french");

  function switchLocale() {
    document.cookie = `NEXT_LOCALE=${otherLocale};path=/;max-age=31536000`;
    router.replace(pathname, { locale: otherLocale });
  }

  return (
    <button
      onClick={switchLocale}
      className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted"
      aria-label={`Switch to ${label}`}
    >
      <span className="text-xs">{locale === "fr" ? "🇬🇧" : "🇫🇷"}</span>
      <span>{label}</span>
    </button>
  );
}
