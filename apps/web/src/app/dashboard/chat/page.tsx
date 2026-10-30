"use client";

import { PremiumHero } from '@/components/layout/premium-hero';
import { AppShell } from "@/components/layout/app-shell";
import { ChatShell } from "@/features/chat/components/chat-shell";
import { useT } from "@/lib/i18n/context";

const MUTED = "#9a8f7c";
const GOLD_BRIGHT = "#e8d48b";

export default function ChatPage() {
  const { t } = useT();

  return (
    <AppShell>
      <ChatShell>
        <div className="flex flex-1 flex-col items-center justify-center px-6 py-16 text-center">
          <p className="font-serif text-xl" style={{ color: GOLD_BRIGHT }}>
            {t("chat.title")}
          </p>
          <p className="mt-2 text-sm" style={{ color: MUTED }}>
            {t("chat.emptyHint")}
          </p>
        </div>
      </ChatShell>
    </AppShell>
  );
}
