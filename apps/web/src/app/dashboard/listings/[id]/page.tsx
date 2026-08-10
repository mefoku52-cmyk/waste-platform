'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listingsApi } from '@/features/listings/api';
import { inquiriesApi } from '@/features/inquiries/api';
import { useAuthRequired } from '@/features/auth/hooks/use-auth-required';
import { Button } from '@/components/ui/button';

export default function ListingDetailPage() {
  const params = useParams();
  const id = String(params?.id || '');
  const router = useRouter();
  const { user } = useAuthRequired();

  const { data, isLoading, error } = useQuery({
    queryKey: ['listing', id],
    queryFn: async () => {
      const res: any = await listingsApi.getListing(id);
      return res?.data ?? res;
    },
    enabled: !!id,
  });

  const [message, setMessage] = useState('Mám záujem o túto ponuku.');
  const [phone, setPhone] = useState('');
  const [busy, setBusy] = useState(false);
  const [ok, setOk] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const memberships = (user as any)?.memberships || [];
  const myCompanyId = memberships[0]?.companyId || memberships[0]?.company_id || null;
  const email = (user as any)?.email || (user as any)?.user?.email || '';

  const isOwn =
    data?.companyId &&
    memberships.some(
      (m: any) => String(m.companyId || m.company_id) === String(data.companyId)
    );

  const handleInquiry = async () => {
    if (!myCompanyId) {
      setErr('Najprv si vytvor firmu – dopyt ide v mene tvojej firmy.');
      return;
    }
    if (!message.trim()) {
      setErr('Správa je povinná.');
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await inquiriesApi.create({
        listingId: id,
        companyId: String(myCompanyId),
        message: message.trim(),
        contactEmail: email || 'unknown@example.com',
        contactPhone: phone || undefined,
      });
      setOk(true);
    } catch (e: any) {
      setErr(e?.message || 'Odoslanie dopytu zlyhalo');
    } finally {
      setBusy(false);
    }
  };

  if (isLoading) return <div className="p-8 text-center">Načítavam detail...</div>;
  if (error || !data) {
    return (
      <div className="p-8 text-center text-red-500">
        Ponuku sa nepodarilo načítať.
        <div className="mt-4">
          <Button variant="outline" onClick={() => router.push('/dashboard')}>Späť</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-2xl space-y-6">
        <Button variant="outline" size="sm" onClick={() => router.push('/dashboard')}>
          ← Späť na dashboard
        </Button>

        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-2 text-sm text-gray-500 uppercase tracking-wide">{data.status}</div>
          <h1 className="text-2xl font-bold text-gray-900">{data.title}</h1>
          <p className="mt-2 text-gray-600 whitespace-pre-wrap">{data.description || 'Bez popisu'}</p>

          <dl className="mt-6 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-gray-500">Materiál</dt>
              <dd className="font-medium text-gray-900">{data.materialType}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Množstvo</dt>
              <dd className="font-medium text-gray-900">
                {data.quantity} {data.unit}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Cena</dt>
              <dd className="font-medium text-gray-900">
                {data.price != null ? `${data.price} ${data.currency || 'EUR'}` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Stav materiálu</dt>
              <dd className="font-medium text-gray-900">{data.condition || '—'}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Lokalita</dt>
              <dd className="font-medium text-gray-900">{data.location || '—'}</dd>
            </div>
          </dl>
        </div>

        {!isOwn && data.status === 'published' && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Mám záujem</h2>
            <p className="mt-1 text-sm text-gray-500">
              Pošli dopyt predávajúcej firme. Uvidí správu, e-mail a telefón.
            </p>

            {ok ? (
              <div className="mt-4 rounded bg-green-50 p-3 text-sm text-green-800">
                Dopyt odoslaný. Predávajúci ho uvidí v zozname dopytov.
              </div>
            ) : (
              <div className="mt-4 space-y-3">
                <div>
                  <label className="block text-sm text-gray-700">Správa</label>
                  <textarea
                    className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
                    rows={3}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-700">Telefón (voliteľné)</label>
                  <input
                    className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="09xx xxx xxx"
                  />
                </div>
                {err && <div className="text-sm text-red-600">{err}</div>}
                <Button onClick={handleInquiry} disabled={busy}>
                  {busy ? 'Odosielam...' : 'Odoslať dopyt'}
                </Button>
              </div>
            )}
          </div>
        )}

        {isOwn && (
          <div className="rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-800">
            Toto je tvoja ponuka – dopyt tu neodosielaš.
          </div>
        )}
      </div>
    </div>
  );
}
