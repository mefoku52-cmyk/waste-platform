'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useT } from '@/lib/i18n/context';
import { AppShell } from '@/components/layout/app-shell';
import { useCurrentUser } from '@/features/auth/hooks/use-current-user';
import { InspectionPanel } from '@/features/inspections/components/inspection-panel';
import { inspectionsApi } from '@/features/inspections/api';
import { inspectionStateLabel } from '@/features/inspections/state-label';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const DANGER = '#f0bbb0';

export default function InspectionPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { t } = useT();
  const { data: me } = useCurrentUser();
  const [inspection, setInspection] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const inspectionId = String(params?.id || '');
  const myId = String((me as any)?.id || (me as any)?.user?.id || '');

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await inspectionsApi.get(inspectionId);
        if (!cancelled) setInspection(res.data);
      } catch (e: any) {
        if (!cancelled) {
          setErr(e?.status === 401 || e?.message?.includes('401')
            ? t('inspections.loginRequired')
            : e?.message || t('inspections.startFailed'));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    if (inspectionId) void load();
    return () => { cancelled = true; };
  }, [inspectionId, t]);

  if (!inspectionId) {
    router.replace('/dashboard/listings');
    return null;
  }

  const isOwner = inspection
    ? String(inspection.ownerUserId || inspection.owner_user_id) === myId
    : false;
  const isViewer = inspection
    ? String(inspection.viewerUserId || inspection.viewer_user_id) === myId
    : false;
  const state = inspection?.state ?? null;

  if (loading) {
    return (
      <AppShell>
        <div className="mx-auto w-full max-w-2xl px-4 py-12 sm:px-6">
          <p className="text-sm" style={{ color: MUTED }}>{t('inspections.working')}</p>
        </div>
      </AppShell>
    );
  }

  if (!inspection) {
    return (
      <AppShell>
        <div className="mx-auto w-full max-w-2xl px-4 py-12 sm:px-6 text-center">
          <p className="text-sm" style={{ color: err ? DANGER : MUTED }}>{err || t('inspections.none')}</p>
          {err && <button type="button" onClick={() => router.replace('/login')} className="mt-3 text-xs underline">{t('common.login')}</button>}
        </div>
      </AppShell>
    );
  }

  const canAct = isOwner || isViewer;

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-3xl px-4 py-7 sm:px-6 sm:py-10">
        <div className="flex items-center gap-2 mb-4">
          <span className="rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.15em]"
                style={{ borderColor: 'color-mix(in srgb, #c9a84c 35%, transparent)', color: GOLD }}>
            🎥 {t('inspections.title')}
          </span>
        </div>

        <section className="rounded-2xl border border-[rgba(201,168,76,0.28)] bg-[#0f0e0a] p-5 sm:p-7">
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <h2 className="font-serif text-2xl sm:text-3xl" style={{ color: GOLD_BRIGHT }}>
              {t('inspections.title')}
            </h2>
            <span style={{ color: MUTED }}>{t('inspections.state')}:{' '}
              <span style={{ color: GOLD_BRIGHT, fontWeight: 600 }}>
                {t(`inspections.state_${inspectionStateLabel(state)}`)}
              </span>
            </span>
            {inspection.roomId && (
              <span className="rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.12em]"
                    style={{ borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)', color: GOLD_BRIGHT }}>
                {t('inspections.roomReady')}
              </span>
            )}
          </div>

          <p className="text-[11px]" style={{ color: MUTED }}>
            {t('common.inspectionId')}: <code style={{ color: FG }}>{inspection.id}</code>{' '}
            · {t('common.listingId')}: <code style={{ color: FG }}>{inspection.listingId}</code>
          </p>

          {!canAct ? (
            <p className="mt-3 text-sm" style={{ color: MUTED }}>
              {t('inspections.notParticipant')}
            </p>
          ) : isOwner ? (
            <>
              <p className="mt-3 text-sm" style={{ color: MUTED }}>
                {t('inspections.ownerHint')}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {!inspection.consentToRecord && (
                  <button type="button" onClick={() => {
                    inspectionsApi.grantRecordingConsent(inspection.id).then(() => {
                      inspectionsApi.get(inspection.id).then(r => setInspection(r.data));
                    });
                  }} className="rounded-lg border px-3 py-1.5 text-xs transition"
                        style={{ borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)', color: GOLD_BRIGHT }}>
                    {t('inspections.consent')}
                  </button>
                )}
                <button type="button" onClick={() => {
                  inspectionsApi.publisherLink(inspection.id).then((r: any) => {
                    window.open(r.publishUrl, '_blank', 'noopener,noreferrer');
                  });
                }} className="rounded-lg px-3 py-1.5 text-xs font-semibold transition"
                      style={{ background: GOLD, color: '#090807' }}>
                  {t('inspections.openPublisher')}
                </button>
                <button type="button" onClick={() => {
                  const url = `${window.location.origin}/obhliadka/${inspection.id}`;
                  navigator.clipboard.writeText(url);
                }} className="rounded-lg border px-3 py-1.5 text-xs transition"
                      style={{ borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)', color: GOLD_BRIGHT }}>
                  {t('inspections.invite')}
                </button>
                <button type="button" onClick={() => {
                  if (window.confirm(t('inspections.endConfirm'))) {
                    inspectionsApi.end(inspection.id).then(() => {
                      inspectionsApi.get(inspection.id).then(r => setInspection(r.data));
                    });
                  }
                }} className="rounded-lg px-3 py-1.5 text-xs font-semibold transition"
                      style={{ background: DANGER, color: '#090807' }}>
                  {t('inspections.end')}
                </button>
              </div>
            </>
          ) : (
            <>
              <p className="mt-3 text-sm" style={{ color: MUTED }}>
                {t('inspections.viewerHint')}
              </p>
              <div className="mt-4">
                <button type="button" onClick={() => {
                  inspectionsApi.join({ inspectionId: inspection.id, waitRoomSeconds: 8 }).then((r: any) => {
                    window.open(r.viewerUrl, '_blank', 'noopener,noreferrer');
                  });
                }} className="rounded-lg px-4 py-1.5 text-xs font-semibold transition"
                      style={{ background: GOLD, color: '#090807' }}>
                  {t('inspections.join')}
                </button>
              </div>
            </>
          )}
        </section>
      </div>
    </AppShell>
  );
}
