'use client';
import Link from 'next/link';
import { LanguageSwitcher } from '@/components/language-switcher';

// const GOLD = '#c9a84c';

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="relative min-h-[100dvh] bg-[#090807] text-[#f3ead8]">
        <div className="absolute right-4 top-4 z-50">
          <LanguageSwitcher />
        </div>
        <main className="grid min-h-[100dvh] place-items-center px-4 py-12">
          <div className="w-full max-w-md">
            <div className="text-center">
              <Link href="/" className="inline-block">
                <img
                  src="/trc-mark.jpg"
                  alt="TRČ"
                  className="mx-auto h-20 w-20 rounded-full object-cover shadow-[0_24px_60px_-28px_rgba(0,0,0,0.7)]"
                />
              </Link>
              <h1
                className="mt-4 text-4xl font-normal tracking-[-0.03em]"
                style={{ fontFamily: 'DM Serif Display, serif' }}
              >
                {title}
              </h1>
              {subtitle ? (
                <p className="mt-2 text-sm text-[#9a8f7c]">{subtitle}</p>
              ) : null}
            </div>
            <div className="mt-8">{children}</div>
          </div>
        </main>
      </div>
    </>
  );
}

export function AuthDivider({ label = 'alebo' }: { label?: string }) {
  return (
    <div className="my-6">
      <div className="h-px bg-gradient-to-r from-transparent via-[color:color-mix(in_srgb,#c9a84c_55%,transparent)] to-transparent" />
      <p className="mt-3 text-center text-[0.7rem] uppercase tracking-[0.2em] text-[#6e6658]">
        {label}
      </p>
    </div>
  );
}

export function AuthButton({
  children,
  variant = 'primary',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'ghost';
}) {
  const base =
    'inline-flex h-12 w-full items-center justify-center rounded-md text-[0.95rem] font-semibold transition-colors disabled:opacity-50';
  if (variant === 'ghost') {
    return (
      <button
        {...props}
        className={`${base} border border-[color:color-mix(in_srgb,#c9a84c_35%,transparent)] bg-transparent text-[#f3ead8] hover:border-[#c9a84c]`}
      >
        {children}
      </button>
    );
  }
  return (
    <button
      {...props}
      className={`${base} bg-[#c9a84c] text-[#090807] hover:bg-[#e8d48b]`}
    >
      {children}
    </button>
  );
}

export function AuthInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className="h-12 w-full rounded-md border border-[color:color-mix(in_srgb,#c9a84c_30%,transparent)] bg-[#090807] px-4 text-base text-[#f3ead8] outline-none transition-colors placeholder:text-[#6e6658] focus:border-[#c9a84c]"
    />
  );
}

export function AuthLink({
  children,
  href,
}: {
  children: React.ReactNode;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="text-center text-sm text-[#9a8f7c] transition-colors hover:text-[#e8d48b]"
    >
      {children}
    </Link>
  );
}
