'use client';

import { useEffect, useMemo, useState } from 'react';

import { useT } from '@/lib/i18n/context';

import { companyPagesApi } from '../api';
import {
  useCompanyPage,
  usePublishCompanyPage,
  useSaveCompanyPage,
  useUnpublishCompanyPage,
} from '../hooks/use-company-page';
import { CompanyPageUpsertInput } from '../types';
import { PhotoGalleryManager } from './photo-gallery-manager';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const OK = '#5fd17a';
const DANGER = '#e8a598';

type FormState = {
  slug: string;
  displayName: string;
  tagline: string;
  aboutShort: string;
  aboutLong: string;
  services: string;
  specialization: string;
  certifications: string;
  openingHours: string;
  languages: string;
  categories: string;
  area: string;
  publicEmail: string;
  publicPhone: string;
  publicWebsite: string;
  seoTitle: string;
  seoDescription: string;
};

const EMPTY: FormState = {
  slug: '',
  displayName: '',
  tagline: '',
  aboutShort: '',
  aboutLong: '',
  services: '',
  specialization: '',
  certifications: '',
  openingHours: '',
  languages: '',
  categories: '',
  area: '',
  publicEmail: '',
  publicPhone: '',
  publicWebsite: '',
  seoTitle: '',
  seoDescription: '',
};

function fromPage(page: ReturnType<typeof useCompanyPage>['data']): FormState {
  if (!page) return EMPTY;
  return {
    slug: page.slug ?? '',
    displayName: page.displayName ?? '',
    tagline: page.tagline ?? '',
    aboutShort: page.aboutShort ?? '',
    aboutLong: page.aboutLong ?? '',
    services: page.services ?? '',
    specialization: page.specialization ?? '',
    certifications: page.certifications ?? '',
    openingHours: page.openingHours ?? '',
    languages: page.languages ?? '',
    categories: page.categories ?? '',
    area: page.area ?? '',
    publicEmail: page.publicEmail ?? '',
    publicPhone: page.publicPhone ?? '',
    publicWebsite: page.publicWebsite ?? '',
    seoTitle: page.seoTitle ?? '',
    seoDescription: page.seoDescription ?? '',
  };
}

function toInput(form: FormState): CompanyPageUpsertInput {
  const nullable = (v: string) => (v.trim() === '' ? null : v.trim());
  return {
    slug: form.slug.trim() || undefined,
    displayName: nullable(form.displayName),
    tagline: nullable(form.tagline),
    aboutShort: nullable(form.aboutShort),
    aboutLong: nullable(form.aboutLong),
    services: nullable(form.services),
    specialization: nullable(form.specialization),
    certifications: nullable(form.certifications),
    openingHours: nullable(form.openingHours),
    languages: nullable(form.languages),
    categories: nullable(form.categories),
    area: nullable(form.area),
    publicEmail: nullable(form.publicEmail),
    publicPhone: nullable(form.publicPhone),
    publicWebsite: nullable(form.publicWebsite),
    seoTitle: nullable(form.seoTitle),
    seoDescription: nullable(form.seoDescription),
  };
}

type Props = { companyId: string };

export function CompanyPageEditor({ companyId }: Props) {
  const { t } = useT();
  const pageQuery = useCompanyPage(companyId);
  const save = useSaveCompanyPage(companyId);
  const publish = usePublishCompanyPage(companyId);
  const unpublish = useUnpublishCompanyPage(companyId);

  const [form, setForm] = useState<FormState>(EMPTY);
  const [notice, setNotice] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null);
  const [slugCheck, setSlugCheck] = useState<{ available: boolean; reason: string } | null>(null);
  const [checkingSlug, setCheckingSlug] = useState(false);

  const page = pageQuery.data;

  useEffect(() => {
    if (page) setForm(fromPage(page));
  }, [page]);

  const status = page?.status ?? 'draft';
  const published = status === 'published';

  const missing = useMemo(() => page?.missingForPublish ?? [], [page]);

  function set<K extends keyof FormState>(key: K, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function checkSlug() {
    const slug = form.slug.trim();
    if (!slug) return;
    setCheckingSlug(true);
    setSlugCheck(null);
    try {
      const res = await companyPagesApi.checkSlug(companyId, slug);
      setSlugCheck({ available: res.available, reason: res.reason });
    } catch {
      setSlugCheck(null);
    } finally {
      setCheckingSlug(false);
    }
  }

  async function onSave() {
    setNotice(null);
    try {
      await save.mutateAsync(toInput(form));
      setNotice({ kind: 'ok', text: t('companyPage.saved') });
    } catch (err) {
      setNotice({
        kind: 'err',
        text: err instanceof Error ? err.message : t('companyPage.saveFailed'),
      });
    }
  }

  async function onPublish() {
    setNotice(null);
    try {
      await publish.mutateAsync();
      setNotice({ kind: 'ok', text: t('companyPage.published') });
    } catch (err) {
      setNotice({
        kind: 'err',
        text: err instanceof Error ? err.message : t('companyPage.publishFailed'),
      });
    }
  }

  async function onUnpublish() {
    setNotice(null);
    try {
      await unpublish.mutateAsync();
      setNotice({ kind: 'ok', text: t('companyPage.unpublished') });
    } catch (err) {
      setNotice({
        kind: 'err',
        text: err instanceof Error ? err.message : t('companyPage.publishFailed'),
      });
    }
  }

  if (pageQuery.isLoading) {
    return <p className="mt-6 text-sm" style={{ color: MUTED }}>{t('tables.loading')}</p>;
  }
  if (pageQuery.error) {
    return (
      <div className="mt-6 rounded-2xl border border-[#c45c4a]/60 bg-[#c45c4a]/10 p-4 text-sm text-[#f0bbb0]">
        {pageQuery.error instanceof Error ? pageQuery.error.message : t('companies.loadError')}
      </div>
    );
  }

  const field = (
    key: keyof FormState,
    label: string,
    opts: { textarea?: boolean; rows?: number; type?: string; maxLength?: number } = {},
  ) => (
    <label className="block">
      <span className="mb-1 block text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>
        {label}
      </span>
      {opts.textarea ? (
        <textarea
          className="w-full rounded-md border bg-transparent px-3 py-2 text-sm"
          style={{ borderColor: 'rgba(201,168,76,0.3)', color: 'inherit' }}
          rows={opts.rows ?? 3}
          maxLength={opts.maxLength}
          value={form[key]}
          onChange={(e) => set(key, e.target.value)}
        />
      ) : (
        <input
          className="w-full rounded-md border bg-transparent px-3 py-2 text-sm"
          style={{ borderColor: 'rgba(201,168,76,0.3)', color: 'inherit' }}
          type={opts.type ?? 'text'}
          maxLength={opts.maxLength}
          value={form[key]}
          onChange={(e) => set(key, e.target.value)}
        />
      )}
    </label>
  );

  return (
    <div>
      {/* Stav + akcie */}
      <section className="mt-6 overflow-hidden rounded-2xl border border-[rgba(201,168,76,0.28)] bg-[#0f0e0a] p-5 sm:p-7">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em]" style={{ color: GOLD }}>
              {t('companyPage.eyebrow')}
            </p>
            <h1 className="mt-2 font-serif text-3xl leading-tight" style={{ color: GOLD_BRIGHT }}>
              {t('companyPage.title')}
            </h1>
          </div>
          <span
            className="rounded-full px-3 py-1 text-xs font-semibold"
            style={{
              background: 'color-mix(in srgb, currentColor 15%, transparent)',
              color: published ? OK : MUTED,
            }}
          >
            ● {published ? t('companyPage.statusPublished') : t('companyPage.statusDraft')}
          </span>
        </div>

        {missing.length > 0 ? (
          <div className="mt-4 rounded-xl border border-[#c9a84c]/40 bg-[#c9a84c]/10 p-3 text-sm">
            <p style={{ color: GOLD_BRIGHT, fontWeight: 600 }}>
              {t('companyPage.missingTitle')}
            </p>
            <ul className="mt-1 list-disc pl-5" style={{ color: MUTED }}>
              {missing.map((m) => (
                <li key={m}>{t(`companyPage.missing.${m}`, m)}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {notice ? (
          <div
            className="mt-4 rounded-xl p-3 text-sm"
            style={{
              border: `1px solid ${notice.kind === 'ok' ? 'rgba(95,209,122,0.5)' : 'rgba(196,92,74,0.6)'}`,
              background: notice.kind === 'ok' ? 'rgba(95,209,122,0.1)' : 'rgba(196,92,74,0.1)',
              color: notice.kind === 'ok' ? OK : DANGER,
            }}
          >
            {notice.text}
          </div>
        ) : null}

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            disabled={save.isPending}
            onClick={onSave}
            className="rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-50"
            style={{ background: GOLD, color: '#090807' }}
          >
            {save.isPending ? t('companyPage.saving') : t('companyPage.save')}
          </button>

          {!published ? (
            <button
              type="button"
              disabled={publish.isPending}
              onClick={onPublish}
              className="rounded-full border px-4 py-2 text-sm font-semibold disabled:opacity-50"
              style={{ borderColor: 'rgba(201,168,76,0.4)', color: GOLD_BRIGHT }}
            >
              {publish.isPending ? t('companyPage.publishing') : t('companyPage.publish')}
            </button>
          ) : (
            <>
              <a
                href={`/firma/${page?.slug ?? ''}`}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-full border px-4 py-2 text-sm font-semibold"
                style={{ borderColor: 'rgba(201,168,76,0.4)', color: GOLD_BRIGHT }}
              >
                {t('companyPage.viewPublic')}
              </a>
              <button
                type="button"
                disabled={unpublish.isPending}
                onClick={onUnpublish}
                className="rounded-full border px-4 py-2 text-sm font-semibold disabled:opacity-50"
                style={{ borderColor: 'rgba(232,165,152,0.4)', color: DANGER }}
              >
                {unpublish.isPending ? t('companyPage.publishing') : t('companyPage.unpublish')}
              </button>
            </>
          )}
        </div>
      </section>

      {/* Adresa stránky (slug) */}
      <section className="mt-6">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
          {t('companyPage.slugSection')}
        </p>
        <div className="cmep-panel rounded-xl p-4">
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-[240px] flex-1">
              <label className="block">
                <span className="mb-1 block text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>
                  {t('companyPage.slug')}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-sm" style={{ color: MUTED }}>/firma/</span>
                  <input
                    className="w-full rounded-md border bg-transparent px-3 py-2 text-sm"
                    style={{ borderColor: 'rgba(201,168,76,0.3)', color: 'inherit' }}
                    value={form.slug}
                    onChange={(e) => {
                      set('slug', e.target.value);
                      setSlugCheck(null);
                    }}
                    placeholder="moja-firma"
                  />
                </div>
              </label>
            </div>
            <button
              type="button"
              disabled={checkingSlug || !form.slug.trim()}
              onClick={checkSlug}
              className="rounded-full border px-4 py-2 text-sm font-semibold disabled:opacity-40"
              style={{ borderColor: 'rgba(201,168,76,0.4)', color: GOLD_BRIGHT }}
            >
              {checkingSlug ? t('companyPage.checking') : t('companyPage.checkSlug')}
            </button>
          </div>
          {slugCheck ? (
            <p className="mt-2 text-xs" style={{ color: slugCheck.available ? OK : DANGER }}>
              {slugCheck.available
                ? t('companyPage.slugAvailable')
                : t(`companyPage.slugReason.${slugCheck.reason}`, t('companyPage.slugTaken'))}
            </p>
          ) : null}
        </div>
      </section>

      {/* Prezentácia */}
      <section className="mt-6">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
          {t('companyPage.presentationSection')}
        </p>
        <div className="space-y-3">
          {field('displayName', t('companyPage.f.displayName'))}
          {field('tagline', t('companyPage.f.tagline'))}
          {field('aboutShort', t('companyPage.f.aboutShort'), { textarea: true, rows: 2, maxLength: 600 })}
          {field('aboutLong', t('companyPage.f.aboutLong'), { textarea: true, rows: 6 })}
          {field('services', t('companyPage.f.services'), { textarea: true, rows: 4 })}
          {field('specialization', t('companyPage.f.specialization'))}
          {field('certifications', t('companyPage.f.certifications'), { textarea: true, rows: 2 })}
        </div>
      </section>

      {/* Prevádzka */}
      <section className="mt-6">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
          {t('companyPage.operationsSection')}
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          {field('openingHours', t('companyPage.f.openingHours'))}
          {field('languages', t('companyPage.f.languages'))}
          {field('categories', t('companyPage.f.categories'))}
          {field('area', t('companyPage.f.area'))}
        </div>
      </section>

      {/* Verejné kontakty */}
      <section className="mt-6">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
          {t('companyPage.contactsSection')}
        </p>
        <p className="mb-2 text-xs" style={{ color: MUTED }}>{t('companyPage.contactsHint')}</p>
        <div className="grid gap-3 sm:grid-cols-2">
          {field('publicEmail', t('companyPage.f.publicEmail'), { type: 'email' })}
          {field('publicPhone', t('companyPage.f.publicPhone'))}
          <div className="sm:col-span-2">
            {field('publicWebsite', t('companyPage.f.publicWebsite'))}
          </div>
        </div>
      </section>

      {/* SEO */}
      <section className="mt-6">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
          {t('companyPage.seoSection')}
        </p>
        <div className="space-y-3">
          {field('seoTitle', t('companyPage.f.seoTitle'), { maxLength: 255 })}
          {field('seoDescription', t('companyPage.f.seoDescription'), {
            textarea: true,
            rows: 2,
            maxLength: 320,
          })}
        </div>
      </section>

      <PhotoGalleryManager companyId={companyId} />
    </div>
  );
}
