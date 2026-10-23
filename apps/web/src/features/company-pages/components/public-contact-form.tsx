'use client';

import { useState } from 'react';

import { http } from '@/lib/api/http';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const FG = '#f3ead8';

type Props = { slug: string };

export function PublicContactForm({ slug }: Props) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState('');
  const [website, setWebsite] = useState('');
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSending(true);
    try {
      await http.post(
        `/public/company-pages/${encodeURIComponent(slug)}/contact`,
        {
          name,
          email,
          phone: phone || null,
          message,
          website,
        },
        { timeoutMs: 60000 },
      );
      setSent(true);
      setName('');
      setEmail('');
      setPhone('');
      setMessage('');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Správu sa nepodarilo odoslať. Skús neskôr.',
      );
    } finally {
      setSending(false);
    }
  }

  if (sent) {
    return (
      <div
        className="cmep-panel rounded-xl p-5 text-sm"
        style={{ borderColor: 'rgba(95,209,122,0.35)', color: GOLD_BRIGHT }}
      >
        Ďakujeme, správa bola odoslaná. Firma ťa bude kontaktovať.
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="cmep-panel space-y-3 rounded-xl p-5">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-xs" style={{ color: MUTED }}>
          Meno *
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={200}
            className="mt-1 w-full rounded-lg border bg-transparent px-3 py-2 text-sm"
            style={{ borderColor: 'rgba(201,168,76,0.3)', color: FG }}
          />
        </label>
        <label className="text-xs" style={{ color: MUTED }}>
          E-mail *
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            maxLength={320}
            className="mt-1 w-full rounded-lg border bg-transparent px-3 py-2 text-sm"
            style={{ borderColor: 'rgba(201,168,76,0.3)', color: FG }}
          />
        </label>
        <label className="text-xs" style={{ color: MUTED }}>
          Telefón
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            maxLength={64}
            className="mt-1 w-full rounded-lg border bg-transparent px-3 py-2 text-sm"
            style={{ borderColor: 'rgba(201,168,76,0.3)', color: FG }}
          />
        </label>
        <div aria-hidden="true" className="hidden">
          <label>
            Website
            <input
              tabIndex={-1}
              autoComplete="off"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
            />
          </label>
        </div>
      </div>
      <label className="block text-xs" style={{ color: MUTED }}>
        Správa *
        <textarea
          required
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          maxLength={4000}
          rows={4}
          className="mt-1 w-full rounded-lg border bg-transparent px-3 py-2 text-sm"
          style={{ borderColor: 'rgba(201,168,76,0.3)', color: FG }}
        />
      </label>
      {error ? (
        <p className="text-xs" style={{ color: '#e8a598' }}>
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={sending}
        className="rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-50"
        style={{ background: GOLD, color: '#090807' }}
      >
        {sending ? 'Odosielam…' : 'Odoslať správu'}
      </button>
    </form>
  );
}
