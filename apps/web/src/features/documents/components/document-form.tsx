'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCreateDocument } from '../hooks/use-create-document';
import { useCompanies } from '../../companies/hooks/use-companies';
import { uploadFile } from '../../uploads/api';
import { config } from '../../../lib/config';
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
  const [localError, setLocalError] = useState(null);
  const [uploading, setUploading] = useState(false);

  const onFileChange = async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    setLocalError(null);
    setUploading(true);
    try {
      const res = await uploadFile(file);
      var path = res.url;
      if (path && path.indexOf('http') !== 0) {
        path = String(config.apiBaseUrl || '') + path;
      }
      setFileUrl(path);
    } catch (err) {
      setLocalError((err && err.message) || 'Upload zlyhal');
    } finally {
      setUploading(false);
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);
    const cid = companyId || (companies[0] && companies[0].id);
    if (!title.trim() || !fileUrl.trim() || !cid) {
      setLocalError('Vyplň názov, nahraj súbor a firmu.');
      return;
    }
    try {
      await mutateAsync({
        title: title.trim(),
        documentType: (documentType.trim() || 'certificate'),
        fileUrl: fileUrl.trim(),
        companyId: String(cid),
      });
      router.push('/dashboard');
    } catch (err) {
      setLocalError((err && err.message) || 'Uloženie zlyhalo');
    }
  };

  const busy = isPending || uploading;

  return (
    <form onSubmit={onSubmit} className="w-full max-w-md space-y-4 rounded-lg bg-white p-6 shadow-md">
      <h2 className="mb-2 text-2xl font-bold text-gray-900">Pridať dokument</h2>

      {(localError || error) && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-600">
          {localError || (error && error.message)}
        </div>
      )}

      <FormField label="Názov">
        <Input value={title} onChange={(e) => setTitle(e.target.value)} disabled={busy} />
      </FormField>

      <FormField label="Typ (certificate, invoice, other)">
        <Input value={documentType} onChange={(e) => setDocumentType(e.target.value)} disabled={busy} />
      </FormField>

      <FormField label="Súbor (pdf, jpg, png)">
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/*"
          onChange={onFileChange}
          disabled={busy}
          className="block w-full text-sm text-gray-700"
        />
        {uploading && <p className="mt-1 text-xs text-gray-500">Nahrávam...</p>}
        {fileUrl && !uploading && (
          <p className="mt-1 truncate text-xs text-green-700">OK: {fileUrl}</p>
        )}
      </FormField>

      <FormField label="URL súboru">
        <Input
          value={fileUrl}
          onChange={(e) => setFileUrl(e.target.value)}
          placeholder="vyplní sa po uploade"
          disabled={busy}
        />
      </FormField>

      <FormField label="Firma">
        <select
          className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          value={companyId}
          onChange={(e) => setCompanyId(e.target.value)}
          disabled={busy}
        >
          <option value="">— vyber firmu —</option>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>
              {c.legalName || c.legal_name || c.id}
            </option>
          ))}
        </select>
      </FormField>

      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="outline" onClick={() => router.back()} disabled={busy}>
          Zrušiť
        </Button>
        <Button type="submit" disabled={busy}>
          {busy ? 'Ukladám...' : 'Uložiť'}
        </Button>
      </div>
    </form>
  );
};
