import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";

export default function Home() {
  const t = useTranslations("home");

  const steps = [
    { number: "1", title: t("step1Title"), description: t("step1Desc") },
    { number: "2", title: t("step2Title"), description: t("step2Desc") },
    { number: "3", title: t("step3Title"), description: t("step3Desc") },
    { number: "4", title: t("step4Title"), description: t("step4Desc") },
  ];

  const stats = [
    { value: t("stat1Value"), label: t("stat1Label") },
    { value: t("stat2Value"), label: t("stat2Label") },
    { value: t("stat3Value"), label: t("stat3Label") },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <span className="text-xl font-bold tracking-tight text-secondary-foreground">
            {t("brand")}
          </span>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <Link
              href="/login"
              className="inline-flex h-10 items-center justify-center rounded-lg border border-border bg-background px-4 text-sm font-medium hover:bg-muted"
            >
              {t("signIn")}
            </Link>
          </div>
        </nav>
      </header>

      <main>
        {/* Hero */}
        <section className="px-4 py-16 sm:px-6 sm:py-20 lg:py-28">
          <div className="mx-auto max-w-6xl text-center">
            <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl lg:text-5xl lg:leading-tight">
              {t("title")}
              <br />
              <span className="text-[var(--primary-500)]">{t("titleHighlight")}</span>
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground sm:text-xl">
              {t("subtitle")}
              <br className="hidden sm:block" />
              {t("subtitleLine2")}
            </p>
            <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link
                href="/signup"
                className="inline-flex h-12 w-full items-center justify-center rounded-lg bg-primary px-8 text-base font-semibold text-white hover:bg-secondary-foreground sm:w-auto"
              >
                {t("cta")}
              </Link>
              <a
                href="#comment-ca-marche"
                className="inline-flex h-12 w-full items-center justify-center rounded-lg border border-primary px-8 text-base font-semibold text-primary hover:bg-secondary sm:w-auto"
              >
                {t("discover")}
              </a>
            </div>
          </div>
        </section>

        {/* Comment ça marche */}
        <section id="comment-ca-marche" className="bg-white px-4 py-16 sm:px-6 sm:py-20">
          <div className="mx-auto max-w-6xl">
            <h2 className="text-center text-2xl font-bold text-foreground sm:text-3xl">
              {t("howItWorks")}
            </h2>
            <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {steps.map((step) => (
                <div
                  key={step.number}
                  className="rounded-xl border border-border bg-background p-6 shadow-sm"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary text-sm font-bold text-primary">
                    {step.number}
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-foreground">
                    {step.title}
                  </h3>
                  <p className="mt-2 text-base text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Social Proof */}
        <section className="px-4 py-16 sm:px-6 sm:py-20">
          <div className="mx-auto max-w-6xl">
            <div className="rounded-2xl bg-white p-8 shadow-sm sm:p-12">
              <h2 className="text-center text-2xl font-bold text-foreground sm:text-3xl">
                {t("trustTitle")}
              </h2>
              <div className="mt-10 grid gap-8 sm:grid-cols-3">
                {stats.map((stat) => (
                  <div key={stat.label} className="text-center">
                    <p className="font-mono text-3xl font-bold tabular-nums text-primary sm:text-4xl">
                      {stat.value}
                    </p>
                    <p className="mt-2 text-base text-muted-foreground">
                      {stat.label}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Confiance */}
        <section className="bg-white px-4 py-16 sm:px-6 sm:py-20">
          <div className="mx-auto max-w-6xl text-center">
            <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
              {t("securityTitle")}
            </h2>
            <div className="mt-10 grid gap-6 sm:grid-cols-3">
              <div className="rounded-xl border border-border p-6">
                <h3 className="text-lg font-semibold text-foreground">
                  {t("security1Title")}
                </h3>
                <p className="mt-2 text-base text-muted-foreground">
                  {t("security1Desc")}
                </p>
              </div>
              <div className="rounded-xl border border-border p-6">
                <h3 className="text-lg font-semibold text-foreground">
                  {t("security2Title")}
                </h3>
                <p className="mt-2 text-base text-muted-foreground">
                  {t("security2Desc")}
                </p>
              </div>
              <div className="rounded-xl border border-border p-6">
                <h3 className="text-lg font-semibold text-foreground">
                  {t("security3Title")}
                </h3>
                <p className="mt-2 text-base text-muted-foreground">
                  {t("security3Desc")}
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-white px-4 py-8 sm:px-6">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <p className="text-sm text-[var(--muted-400)]">
            {t("copyright", { year: new Date().getFullYear() })}
          </p>
          <div className="flex gap-6 text-sm text-[var(--muted-400)]">
            <a href="#" className="hover:text-muted-foreground">
              {t("terms")}
            </a>
            <a href="#" className="hover:text-muted-foreground">
              {t("privacy")}
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
