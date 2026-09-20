import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";

import { SuccessIcon } from "@/components/icons/successIcon";

export const metadata: Metadata = {
  title: "paperclip",
  description: "Offline personal assistant AI agent harness.",
  metadataBase: new URL('https://paperclip.pages.dev')
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
        <Toaster
          toastOptions={{
            classNames: {
              toast: 'bg-stone-800',
              title: 'text-white',
            },
            style: {
              border: 'none',
            },
          }}
          icons={{
            success: <SuccessIcon />,
          }}
        />
      </body>
    </html>
  );
}
