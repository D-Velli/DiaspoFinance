import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "DiaspoFinance — Tontine digitale",
    short_name: "DiaspoFinance",
    description:
      "Faites une tontine sans vous fâcher avec vos amis. Collecte automatique, distribution transparente.",
    start_url: "/",
    display: "standalone",
    background_color: "#F9FAFB",
    theme_color: "#1A4175",
    orientation: "portrait",
    icons: [
      {
        src: "/icons/icon-192x192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icons/icon-512x512.png",
        sizes: "512x512",
        type: "image/png",
      },
      {
        src: "/icons/icon-maskable-512x512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
