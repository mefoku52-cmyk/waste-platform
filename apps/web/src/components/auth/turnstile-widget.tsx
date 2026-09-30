"use client";

import { useEffect, useRef } from "react";

declare global {
  interface Window {
    turnstile?: {
      render: (el: HTMLElement, opts: Record<string, unknown>) => string;
      reset: (id?: string) => void;
      remove: (id: string) => void;
    };
  }
}

const SCRIPT_ID = "cf-turnstile-script";
const SCRIPT_SRC =
  "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

type Props = {
  onVerify: (token: string) => void;
  onExpire?: () => void;
  onError?: () => void;
};

export function TurnstileWidget({ onVerify, onExpire, onError }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const renderWidget = () => {
      if (!mounted || !ref.current || !window.turnstile) return;
      if (widgetId.current) return;
      const sitekey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
      if (!sitekey) {
        console.warn("TURNSTILE: NEXT_PUBLIC_TURNSTILE_SITE_KEY nie je nastaveny");
        return;
      }
      widgetId.current = window.turnstile.render(ref.current, {
        sitekey,
        theme: "dark",
        callback: (token: string) => {
          if (mounted) onVerify(token);
        },
        "expired-callback": () => {
          if (mounted) onExpire?.();
        },
        "error-callback": () => {
          if (mounted) onError?.();
        },
      });
    };

    if (window.turnstile) {
      renderWidget();
    } else if (!document.getElementById(SCRIPT_ID)) {
      const script = document.createElement("script");
      script.id = SCRIPT_ID;
      script.src = SCRIPT_SRC;
      script.async = true;
      script.defer = true;
      script.onload = renderWidget;
      document.head.appendChild(script);
    } else {
      const iv = window.setInterval(() => {
        if (window.turnstile) {
          window.clearInterval(iv);
          renderWidget();
        }
      }, 100);
      return () => {
        mounted = false;
        window.clearInterval(iv);
      };
    }

    return () => {
      mounted = false;
      if (widgetId.current && window.turnstile) {
        try {
          window.turnstile.remove(widgetId.current);
        } catch {
          /* ignore */
        }
        widgetId.current = null;
      }
    };
  }, [onVerify, onExpire, onError]);

  return <div ref={ref} className="flex justify-center" />;
}
