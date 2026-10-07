'use client';

import { useState } from 'react';
import { companiesApi } from '../api';
import { useT } from '@/lib/i18n/context';

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
  const { t } = useT();

  async function save() {
    setSaving(true);
    setError('');
    try {
      await companiesApi.updateCompany(id, {
        acceptedMaterialTypes: text.trim() || null,
      } as never);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('companies.saveFailed'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-w-[160px]">
      <input
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, 120))}
        placeholder={t('admin.materialsPlaceholder')}
        className="w-full rounded border border-[#c9a84c]/30 bg-black px-2 py-1 text-xs text-[#f3ead8]"
      />
      <button
        type="button"
        disabled={saving}
        onClick={() => void save()}
        className="mt-1 text-[10px] uppercase tracking-[0.15em] text-[#c9a84c]"
      >
        {saving ? '…' : t('admin.saveMaterials')}
      </button>
      {error && <p className="text-[10px] text-red-300">{error}</p>}
    </div>
  );
}
