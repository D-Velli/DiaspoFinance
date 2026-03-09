/**
 * Formate un montant en cents vers la devise locale.
 * Les montants sont TOUJOURS en cents dans l'API.
 */
export function formatCurrency(
  amountCents: number,
  currency: string = "CAD",
  locale: string = "fr-CA",
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
  }).format(amountCents / 100);
}

/**
 * Formate une date selon la locale.
 */
export function formatDate(
  date: Date | string,
  locale: string = "fr-CA",
  style: "short" | "long" = "long",
): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const options: Intl.DateTimeFormatOptions =
    style === "long"
      ? { year: "numeric", month: "long", day: "numeric" }
      : { year: "numeric", month: "short", day: "numeric" };
  return new Intl.DateTimeFormat(locale, options).format(d);
}

/**
 * Formate un temps relatif.
 */
export function formatRelativeTime(
  date: Date,
  locale: string = "fr-CA",
): string {
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });

  if (Math.abs(diffDays) < 1) {
    const diffHours = Math.round(diffMs / (1000 * 60 * 60));
    if (Math.abs(diffHours) < 1) {
      const diffMinutes = Math.round(diffMs / (1000 * 60));
      return rtf.format(diffMinutes, "minute");
    }
    return rtf.format(diffHours, "hour");
  }
  if (Math.abs(diffDays) < 30) {
    return rtf.format(diffDays, "day");
  }
  const diffMonths = Math.round(diffDays / 30);
  return rtf.format(diffMonths, "month");
}
