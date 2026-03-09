import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

const intlMiddleware = createMiddleware(routing);

const isPublicRoute = createRouteMatcher([
  "/",
  "/(fr|en)",
  "/(fr|en)/login(.*)",
  "/(fr|en)/signup(.*)",
  "/(fr|en)/invite/(.*)",
  "/(fr|en)/offline",
  "/api/webhooks/(.*)",
]);

export default clerkMiddleware(async (auth, request) => {
  // Apply i18n middleware for locale detection on non-API routes
  if (!request.nextUrl.pathname.startsWith("/api")) {
    const response = intlMiddleware(request);
    if (response) return response;
  }

  // Protect non-public routes
  if (!isPublicRoute(request)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
