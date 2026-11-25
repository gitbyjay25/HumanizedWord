import { Inter } from "next/font/google";
import "./globals.css";
import ClientProviders from "@/components/layout/ClientProviders";
import GoogleAnalytics from "@/components/GoogleAnalytics";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata = {
  title: "HumanizedText — AI Text Humanizer",
  description:
    "Transform AI-generated content into natural, human-like text with advanced AI humanizer tools.",
  keywords: [
    "humanizedtext",
    "ai to human text",
    "ai text converter",
    "chatgpt humanizer",
    "ai humanizer",
  ],
  authors: [{ name: "HumanizedText" }],
  openGraph: {
    title: "HumanizedText — AI Text Humanizer",
    description:
      "Transform AI-generated content into natural, human-like text.",
    siteName: "HumanizedText",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "HumanizedText — AI Text Humanizer",
    description:
      "Transform AI-generated content into natural, human-like text.",
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://humanizedtext.pro"),
  manifest: "/manifest.json",
};

export const viewport = {
  themeColor: "#1a1a1a",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="bg-bg-primary text-text-primary font-sans antialiased">
        <ClientProviders>{children}</ClientProviders>
        <GoogleAnalytics />
      </body>
    </html>
  );
}
