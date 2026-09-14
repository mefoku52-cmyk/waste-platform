'use client';

import { useState } from 'react';
import { useT, LOCALES, LOCALE_FLAGS, LOCALE_LABELS, Locale } from '@/lib/i18n/context';

export function LanguageSwitcher() {
  const { locale, setLocale } = useT();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 rounded border border-slate-600 bg-slate-900 px-2 py-1 text-sm text-slate-100 hover:bg-slate-800"
        aria-label="Language"
      >
        <span>{LOCALE_FLAGS[locale]}</span>
        <span>{LOCALE_LABELS[locale]}</span>
        <span className="text-xs opacity-70">▾</span>
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-1 min-w-[120px] rounded border border-slate-700 bg-slate-900 shadow-lg">
          {LOCALES.map((l: Locale) => (
            <button
              key={l}
              type="button"
              onClick={() => {
                setLocale(l);
                setOpen(false);
              }}
              className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-800 ${
                l === locale ? 'text-emerald-400' : 'text-slate-100'
              }`}
            >
              <span>{LOCALE_FLAGS[l]}</span>
              <span>{LOCALE_LABELS[l]}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
