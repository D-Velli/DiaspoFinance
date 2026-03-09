"use client";

import { WifiOff } from "lucide-react";

/**
 * Root-level offline fallback page.
 * Served by the Service Worker when the user is offline and no cached page is available.
 * Intentionally outside [locale] to avoid i18n middleware dependency.
 */
export default function OfflineFallback() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background p-4 text-center">
      <div className="space-y-4">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-border">
          <WifiOff className="h-8 w-8 text-[var(--muted-400)]" />
        </div>
        <h1 className="text-xl font-semibold text-foreground">
          Mode hors-ligne
        </h1>
        <p className="max-w-sm text-muted-foreground">
          Reconnectez-vous à Internet pour accéder à DiaspoFinance.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 rounded-lg bg-primary px-6 py-3 font-medium text-white transition-colors hover:bg-secondary-foreground"
        >
          Réessayer
        </button>
      </div>
    </main>
  );
}
