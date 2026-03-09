import { Skeleton } from "@/components/ui/skeleton";

export function DashboardSkeleton() {
  return (
    <div className="min-h-screen bg-[#F9FAFB]">
      <header className="border-b border-[#E5E7EB] bg-white">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <Skeleton className="h-7 w-36" />
          <Skeleton className="h-8 w-8 rounded-full" />
        </nav>
      </header>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-12 sm:px-6 lg:px-8">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-32 w-full rounded-lg" />
          <Skeleton className="h-24 w-full rounded-lg" />
          <Skeleton className="h-24 w-full rounded-lg" />
        </div>
      </main>
    </div>
  );
}
