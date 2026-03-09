import { SignIn } from "@clerk/nextjs";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F9FAFB]">
      <SignIn
        appearance={{
          elements: {
            rootBox: "mx-auto",
            card: "shadow-sm border border-[#E5E7EB] rounded-xl",
            headerTitle: "text-[#111827] font-semibold",
            headerSubtitle: "text-[#374151]",
            formButtonPrimary:
              "bg-[#1A4175] hover:bg-[#0F2B4C] min-h-[44px]",
            footerActionLink: "text-[#2563EB]",
          },
        }}
      />
    </main>
  );
}
