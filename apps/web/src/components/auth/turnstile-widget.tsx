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

  // Callbacky drzime v refs, aby sa useEffect NEspustal pri kazdom renderi.
  // Inak by sa widget zacyklil (render -> verify -> parent setState -> novy
  // callback -> useEffect cleanup + render -> verify -> ...).
  const onVerifyRef = useRef(onVerify);
  const onExpireRef = useRef(onExpire);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onVerifyRef.current = onVerify;
    onExpireRef.current = onExpire;
    onErrorRef.current = onError;
  });

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
          if (mounted) onVerifyRef.current(token);
        },
        "expired-callback": () => {
          if (mounted) onExpireRef.current?.();
        },
        "error-callback": () => {
          if (mounted) onErrorRef.current?.();
        },
      });
    };

    let intervalId: number | null = null;

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
      intervalId = window.setInterval(() => {
        if (window.turnstile) {
          if (intervalId !== null) window.clearInterval(intervalId);
          renderWidget();
        }
      }, 100);
    }

    return () => {
      mounted = false;
      if (intervalId !== null) window.clearInterval(intervalId);
      if (widgetId.current && window.turnstile) {
        try {
          window.turnstile.remove(widgetId.current);
        } catch {
          /* ignore */
        }
        widgetId.current = null;
      }
    };
  }, []);

  return <div ref={ref} className="flex justify-center" />;
}
