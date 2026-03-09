import type { Metadata, Viewport } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { notFound } from "next/navigation";
import { ClerkProvider } from "@clerk/nextjs";
import { frFR, enUS } from "@clerk/localizations";
import { Inter, JetBrains_Mono } from "next/font/google";
import { OfflineBanner } from "@/components/layout/OfflineBanner";
import { routing } from "@/i18n/routing";
import "../globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#1A4175",
};

export const metadata: Metadata = {
  title: "DiaspoFinance — Tontine digitale pour la diaspora",
  description:
    "Faites une tontine sans vous fâcher avec vos amis. Collecte automatique, distribution transparente, zéro stress.",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "DiaspoFinance",
  },
  openGraph: {
    title: "DiaspoFinance — Tontine digitale pour la diaspora",
    description:
      "Faites une tontine sans vous fâcher avec vos amis. Collecte automatique, distribution transparente, zéro stress.",
    type: "website",
    locale: "fr_FR",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
};

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  if (!routing.locales.includes(locale as "fr" | "en")) {
    notFound();
  }

  const messages = await getMessages();

  return (
    <html lang={locale}>
      <head>
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}
      >
        <ClerkProvider
          localization={locale === "fr" ? frFR : enUS}
          signInUrl="/login"
          signUpUrl="/signup"
          afterSignOutUrl="/"
          signInFallbackRedirectUrl="/dashboard"
          signUpFallbackRedirectUrl="/dashboard"
        >
          <NextIntlClientProvider messages={messages}>
            <OfflineBanner />
            {children}
          </NextIntlClientProvider>
        </ClerkProvider>
      </body>
    </html>
  );
}
