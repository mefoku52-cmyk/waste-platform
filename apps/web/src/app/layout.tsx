import "./globals.css";
import { ReactNode } from "react";

import { AppProviders } from "@/components/providers/app-providers";
import { AnalyticsProvider } from "@/lib/analytics";
import { LanguageProvider } from "@/lib/i18n/context";
import Script from 'next/script';
import { config } from '@/lib/config';

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
      
        {config.metaPixelId ? (
          <Script id="meta-pixel" strategy="afterInteractive">
            {`
              !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
              n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
              n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
              t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
              document,'script','https://connect.facebook.net/en_US/fbevents.js');
              fbq('init','${config.metaPixelId}');
              fbq('track','PageView');
            `}
          </Script>
        ) : null}
      </body>
    </html>
  );
}
