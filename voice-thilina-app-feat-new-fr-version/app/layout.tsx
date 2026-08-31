import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { RequestLocaleProvider } from "../components/servio/request-i18n";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Servio",
    template: "%s · Servio",
  },
  description:
    "Smart Local Services, Powered by Voice — describe what you need in Sinhala, Tamil, English or mixed language, and get matched to a nearby provider.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      data-scroll-behavior="smooth"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-dvh min-w-0 flex-col overflow-x-clip">
        <RequestLocaleProvider>{children}</RequestLocaleProvider>
      </body>
    </html>
  );
}
