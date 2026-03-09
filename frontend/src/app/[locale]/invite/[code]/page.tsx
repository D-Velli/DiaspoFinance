import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import { InviteContent } from "./InviteContent";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface InviteData {
  name: string;
  hand_amount_cents: number;
  frequency: string;
  currency: string;
  member_count: number;
  pot_per_turn_cents: number;
}

async function fetchInvite(code: string): Promise<InviteData | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/invite/${code}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    const json = await res.json();
    return json.data;
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ code: string; locale: string }>;
}): Promise<Metadata> {
  const { code, locale } = await params;
  const invite = await fetchInvite(code);

  const t = await getTranslations({ locale, namespace: "tontine.invite" });

  if (!invite) {
    return { title: "DiaspoFinance", robots: { index: false, follow: false } };
  }

  const amount = (invite.hand_amount_cents / 100).toFixed(0);
  const title = t("ogTitle", { name: invite.name });
  const description = t("ogDescription", {
    amount,
    currency: invite.currency,
    count: invite.member_count,
  });

  return {
    title,
    description,
    robots: { index: false, follow: false },
    openGraph: {
      title,
      description,
      type: "website",
      url: `/invite/${code}`,
      images: [{ url: "/og-image.png", width: 1200, height: 630 }],
    },
    twitter: { card: "summary_large_image" },
  };
}

export default async function InvitePage({
  params,
}: {
  params: Promise<{ code: string; locale: string }>;
}) {
  const { code } = await params;
  const invite = await fetchInvite(code);

  if (!invite) {
    notFound();
  }

  return <InviteContent code={code} invite={invite} />;
}
