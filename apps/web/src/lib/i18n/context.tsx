'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import sk from './messages/sk.json';
import en from './messages/en.json';
import ru from './messages/ru.json';
import fr from './messages/fr.json';
import de from './messages/de.json';

export type Locale = 'sk' | 'en' | 'ru' | 'fr' | 'de';

export const LOCALES: Locale[] = ['sk', 'en', 'ru', 'fr', 'de'];
export const LOCALE_LABELS: Record<Locale, string> = {
  sk: 'SK',
  en: 'EN',
  ru: 'RU',
  fr: 'FR',
  de: 'DE',
};
export const LOCALE_FLAGS: Record<Locale, string> = {
  sk: '🇸🇰',
  en: '🇬🇧',
  ru: '🇷🇺',
  fr: '🇫🇷',
  de: '🇩🇪',
};

const messages: Record<Locale, any> = { sk, en, ru, fr, de };
const STORAGE_KEY = 'cmep.locale';

type Ctx = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, fallback?: string) => string;
};

const LanguageContext = createContext<Ctx | null>(null);

function detectLocale(): Locale {
  if (typeof window === 'undefined') return 'sk';
  const stored = window.localStorage.getItem(STORAGE_KEY) as Locale | null;
  if (stored && LOCALES.includes(stored)) return stored;
  const nav = window.navigator.language.slice(0, 2).toLowerCase();
  if (LOCALES.includes(nav as Locale)) return nav as Locale;
  return 'sk';
}

function get(obj: any, path: string): any {
  return path.split('.').reduce((acc, k) => (acc ? acc[k] : undefined), obj);
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('sk');

  useEffect(() => {
    setLocaleState(detectLocale());
  }, []);

  const setLocale = (l: Locale) => {
    setLocaleState(l);
    if (typeof window !== 'undefined') window.localStorage.setItem(STORAGE_KEY, l);
  };

  const t = (key: string, fallback?: string) => {
    const v = get(messages[locale], key);
    if (typeof v === 'string' && v.length > 0) return v;
    const f = get(messages.sk, key);
    if (typeof f === 'string' && f.length > 0) return f;
    if (fallback && fallback.length > 0) return fallback;
    const last = key.split('.').pop() || key;
    return last
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, (c) => c.toUpperCase())
      .trim();
  };

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useT() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useT must be used inside LanguageProvider');
  return ctx;
}
