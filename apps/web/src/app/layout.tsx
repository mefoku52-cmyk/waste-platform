import "./globals.css";
import { ReactNode } from "react";

import { AppProviders } from "@/components/providers/app-providers";
import { AnalyticsProvider } from "@/lib/analytics";
import { LanguageProvider } from "@/lib/i18n/context";

export const metadata = {
  title: "CMEP · Obehové materiály",
  description: "Circular Materials Exchange Platform frontend"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="sk">
      <body>
        <AppProviders>
          <LanguageProvider>
            <AnalyticsProvider>{children}</AnalyticsProvider>
          </LanguageProvider>
        </AppProviders>
      </body>
    </html>
  );
}
