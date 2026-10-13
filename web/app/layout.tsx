import type { Metadata } from "next";
import {
  Geist,
  Geist_Mono,
  Hammersmith_One,
  Fanwood_Text,
} from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const hammersmith = Hammersmith_One({
  weight: "400",
  variable: "--font-hammersmith-one",
  subsets: ["latin"],
});

const fanwood = Fanwood_Text({
  weight: "400",
  style: ["normal", "italic"],
  variable: "--font-fanwood-text",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "paperclip",
  description: "A local personal assistant. Terminal, voice, and Telegram, with memory on your machine.",
  metadataBase: new URL("https://paperclip.pages.dev"),
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${hammersmith.variable} ${fanwood.variable} antialiased`}
    >
      <body>{children}</body>
    </html>
  );
}