"use client";

import { WifiOff } from "lucide-react";
import { useTranslations } from "next-intl";

export default function OfflinePage() {
  const t = useTranslations("offline");

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-[#F9FAFB] p-4 text-center">
      <div className="space-y-4">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#E5E7EB]">
          <WifiOff className="h-8 w-8 text-[#9CA3AF]" />
        </div>
        <h1 className="text-xl font-semibold text-[#111827]">
          {t("title")}
        </h1>
        <p className="max-w-sm text-[#374151]">
          {t("message")}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 rounded-lg bg-[#1A4175] px-6 py-3 font-medium text-white transition-colors hover:bg-[#0F2B4C]"
        >
          {t("retry")}
        </button>
      </div>
    </main>
  );
}
