"use client";

import { useEffect, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useAuth } from "@clerk/nextjs";
import { Link } from "@/i18n/routing";
import { formatCurrency } from "@/lib/utils/format";
import { Users, Copy, Check, Share2 } from "lucide-react";

interface InviteData {
  name: string;
  hand_amount_cents: number;
  frequency: string;
  currency: string;
  member_count: number;
  pot_per_turn_cents: number;
}

export function InviteContent({
  code,
  invite,
}: {
  code: string;
  invite: InviteData;
}) {
  const t = useTranslations("tontine.invite");
  const locale = useLocale();
  const { isSignedIn } = useAuth();
  const [copied, setCopied] = useState(false);
  const [inviteUrl, setInviteUrl] = useState(`/invite/${code}`);

  useEffect(() => {
    setInviteUrl(`${window.location.origin}/invite/${code}`);
  }, [code]);

  const formatLocale = locale === "fr" ? "fr-CA" : "en-CA";

  const freqLabel =
    invite.frequency === "weekly"
      ? t("weekly")
      : invite.frequency === "biweekly"
        ? t("biweekly")
        : t("monthly");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(inviteUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = async () => {
    const shareData = {
      title: invite.name,
      text: t("shareMessage", {
        name: invite.name,
        amount: formatCurrency(invite.hand_amount_cents, invite.currency, formatLocale),
      }),
      url: inviteUrl,
    };

    if (navigator.share) {
      await navigator.share(shareData);
    } else {
      handleCopy();
    }
  };

  const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(
    t("shareMessage", {
      name: invite.name,
      amount: formatCurrency(invite.hand_amount_cents, invite.currency, formatLocale),
    }) + " " + inviteUrl
  )}`;

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-border bg-white p-8 shadow-sm">
          {/* Header */}
          <p className="text-center text-sm text-muted-foreground">
            {t("title")}
          </p>
          <h1 className="mt-2 text-center text-2xl font-bold text-foreground">
            {invite.name}
          </h1>

          {/* Stats */}
          <div className="mt-6 space-y-3 rounded-lg bg-muted/50 p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                {t("handAmount")}
              </span>
              <span className="text-sm font-semibold text-foreground">
                {formatCurrency(invite.hand_amount_cents, invite.currency, formatLocale)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                {t("frequency")}
              </span>
              <span className="text-sm font-medium text-foreground">
                {freqLabel}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                <Users className="mr-1 inline h-3.5 w-3.5" />
                {t("members", { count: invite.member_count })}
              </span>
              <span className="text-sm font-semibold text-primary">
                {t("potPerTurn")}{" "}
                {formatCurrency(invite.pot_per_turn_cents, invite.currency, formatLocale)}
              </span>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-6">
            {isSignedIn ? (
              <Link
                href={`/tontines/join/${code}`}
                className="flex w-full items-center justify-center rounded-lg bg-primary py-3 text-sm font-semibold text-white hover:bg-primary/90"
              >
                {t("join")}
              </Link>
            ) : (
              <Link
                href="/signup"
                className="flex w-full items-center justify-center rounded-lg bg-primary py-3 text-sm font-semibold text-white hover:bg-primary/90"
              >
                {t("signUpFirst")}
              </Link>
            )}
          </div>

          {/* Share buttons */}
          <div className="mt-4 flex gap-2">
            <button
              onClick={handleShare}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-border py-2.5 text-sm font-medium hover:bg-muted"
            >
              <Share2 className="h-4 w-4" />
              {t("share")}
            </button>
            <button
              onClick={handleCopy}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-border py-2.5 text-sm font-medium hover:bg-muted"
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-600" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              {copied ? t("copied") : t("copyLink")}
            </button>
          </div>

          {/* WhatsApp */}
          <a
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-[#25D366] py-2.5 text-sm font-semibold text-white hover:bg-[#20BD5A]"
          >
            {t("shareWhatsApp")}
          </a>
        </div>

        {/* Brand */}
        <p className="mt-6 text-center text-xs text-muted-foreground">
          DiaspoFinance
        </p>
      </div>
    </div>
  );
}
