'use client';

import { useState } from 'react';
import { companiesApi } from '../api';

export function AcceptedMaterialsCell({
  id,
  value,
}: {
  id: string;
  value?: string | null;
}) {
  const [text, setText] = useState(value || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function save() {
    setSaving(true);
    setError('');
    try {
      await companiesApi.updateCompany(id, {
        acceptedMaterialTypes: text.trim() || null,
      } as never);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-w-[160px]">
      <input
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, 120))}
        placeholder="bio, drevo, kov"
        className="w-full rounded border border-[#c9a84c]/30 bg-black px-2 py-1 text-xs text-[#f3ead8]"
      />
      <button
        type="button"
        disabled={saving}
        onClick={() => void save()}
        className="mt-1 text-[10px] uppercase tracking-[0.15em] text-[#c9a84c]"
      >
        {saving ? '…' : 'Ulozit material'}
      </button>
      {error && <p className="text-[10px] text-red-300">{error}</p>}
    </div>
  );
}
