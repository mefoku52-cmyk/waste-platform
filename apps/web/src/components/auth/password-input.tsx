'use client';
import { useState } from 'react';

export function PasswordInput({
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
        aria-label={show ? 'Hide password' : 'Show password'}
        className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md px-2 py-1 text-[#9a8f7c] transition-colors hover:text-[#e8d48b]"
        tabIndex={-1}
      >
        {show ? 'Hide' : 'Show'}
      </button>
    </div>
  );
}
