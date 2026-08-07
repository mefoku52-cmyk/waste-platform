import "./globals.css";
import { ReactNode } from "react";

import { AppProviders } from "@/components/providers/app-providers";

export const metadata = {
  title: "CMEP Web",
  description: "Circular Materials Exchange Platform frontend"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="sk">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
