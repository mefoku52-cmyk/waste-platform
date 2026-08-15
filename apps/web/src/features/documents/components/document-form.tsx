'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCreateDocument } from '../hooks/use-create-document';
import { useCompanies } from '../../companies/hooks/use-companies';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { FormField } from '../../../components/ui/form-field';

export const DocumentForm = () => {
  const router = useRouter();
  const { mutateAsync, isPending, error } = useCreateDocument();
  const { data: companiesData } = useCompanies();
  const companies = (companiesData as any)?.items ?? [];

  const [title, setTitle] = useState('');
  const [documentType, setDocumentType] = useState('certificate');
  const [fileUrl, setFileUrl] = useState('');
  const [companyId, setCompanyId] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    const cid = companyId || companies[0]?.id;
    if (!title.trim() || !fileUrl.trim() || !cid) {
      setLocalError('Vyplň názov, URL súboru a firmu.');
      return;
    }
    try {
      await mutateAsync({
        title: title.trim(),
        documentType: documentType.trim() || 'certificate',
        fileUrl: fileUrl.trim(),
        companyId: String(cid),
      });
      router.push('/dashboard');
    } catch (err: any) {
      setLocalError(err?.message || 'Uloženie zlyhalo');
    }
  };

  return (
    <form onSubmit={onSubmit} className="w-full max-w-md space-y-4 rounded-lg bg-white p-6 shadow-md">
      <h2 className="mb-2 text-2xl font-bold text-gray-900">Pridať dokument</h2>

      {(localError || error) && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-600">
          {localError || (error as any)?.message}
        </div>
      )}

      <FormField label="Názov">
        <Input value={title} onChange={(e) => setTitle(e.target.value)} disabled={isPending} />
      </FormField>

      <FormField label="Typ (certificate, invoice, other)">
        <Input value={documentType} onChange={(e) => setDocumentType(e.target.value)} disabled={isPending} />
      </FormField>

      <FormField label="URL súboru">
        <Input
          value={fileUrl}
          onChange={(e) => setFileUrl(e.target.value)}
          placeholder="https://..."
          disabled={isPending}
        />
      </FormField>

      <FormField label="Firma">
        <select
          className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          value={companyId}
          onChange={(e) => setCompanyId(e.target.value)}
          disabled={isPending}
        >
          <option value="">— vyber firmu —</option>
          {companies.map((c: any) => (
            <option key={c.id} value={c.id}>
              {c.legalName || c.legal_name || c.id}
            </option>
          ))}
        </select>
      </FormField>

      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="outline" onClick={() => router.back()} disabled={isPending}>
          Zrušiť
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Ukladám...' : 'Uložiť'}
        </Button>
      </div>
    </form>
  );
};
