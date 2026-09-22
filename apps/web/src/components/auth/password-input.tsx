'use client';
import { useT } from '@/lib/i18n/context';
import { useState } from 'react';

export function PasswordInput({
  const { t } = useT();

  value,
  onChange,
  placeholder = 'Password',
  required,
  minLength,
  autoComplete,
  name,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
  minLength?: number;
  autoComplete?: string;
  name?: string;
}) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        type={show ? 'text' : 'password'}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        minLength={minLength}
        autoComplete={autoComplete}
        name={name}
        className="h-12 w-full rounded-md border border-[color:color-mix(in_srgb,#c9a84c_30%,transparent)] bg-[#090807] px-4 pr-12 text-base text-[#f3ead8] outline-none transition-colors placeholder:text-[#6e6658] focus:border-[#c9a84c]"
      />
      <button
        type="button"
        onClick={() => setShow((s) => !s)}
        aria-label={show ? 'Skryť heslo' : 'Zobraziť heslo'}
        className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md px-2 py-1 text-[#9a8f7c] transition-colors hover:text-[#e8d48b]"
        tabIndex={-1}
      >
        {show ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 3l18 18" />
            <path d="M10.6 6.2A10.9 10.9 0 0 1 12 6c6.5 0 10 6 10 6a17.3 17.3 0 0 1-3.2 4" />
            <path d="M6.1 6.1C3.6 7.7 2 10 2 10s3.5 7 10 7c1.3 0 2.5-.2 3.6-.6" />
            <path d="M9.9 9.9A3 3 0 0 0 14.1 14.1" />
          </svg>
        )}
      </button>
    </div>
  );
}
