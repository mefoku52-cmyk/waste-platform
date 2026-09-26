'use client';

import type { Persona } from '../lib/persona-store';

type Props = {
  current: Persona;
  onChange: (p: Persona) => void;
};

const OPTIONS: { key: Persona; label: string; title: string }[] = [
  { key: 'bystry', label: '🧠', title: 'Bystrý – štandardný' },
  { key: 'drzy', label: '😏', title: 'Drzý – priamy, bez servítky' },
  { key: 'lenivy', label: '💤', title: 'Lenivý – krátke odpovede' },
  { key: 'op', label: '⚡', title: 'OP – len fakty, nič viac' },
];

export function PersonaPicker({ current, onChange }: Props) {
  return (
    <div className="flex items-center gap-0.5">
      {OPTIONS.map((o) => {
        const active = o.key === current;
        return (
          <button
            key={o.key}
            type="button"
            onClick={() => onChange(o.key)}
            title={o.title}
            aria-label={o.title}
            className="rounded-full px-1.5 py-0.5 text-sm transition"
            style={{
              background: active ? 'color-mix(in srgb, #c9a84c 20%, transparent)' : 'transparent',
              color: active ? '#e8d48b' : '#9a8f7c',
              fontSize: 14,
            }}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
