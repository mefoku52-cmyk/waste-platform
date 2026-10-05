'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { listingSchema, ListingInput } from '../schemas';
import { useCreateListing } from '../hooks/use-create-listing';
import { useUpdateListing } from '../hooks/use-update-listing';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { FormField } from '../../../components/ui/form-field';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '../../companies/api';
import { uploadFile } from '../../uploads/api';
import { config } from '../../../lib/config';
import { useT } from "@/lib/i18n/context";

type Props = {
  listingId?: string;
  initialData?: Partial<ListingInput>;
};

export const ListingForm = ({ listingId, initialData }: Props = {}) => {
  const { t } = useT();
  const isEdit = Boolean(listingId);

  const createResult = useCreateListing();
  const updateResult = useUpdateListing(listingId || '');

  const {
    mutate: createListing,
    isPending: createPending,
    error: createError,
  } = createResult;

  const {
    mutate: updateListing,
    isPending: updatePending,
    error: updateError,
  } = updateResult;

  const isPending = isEdit ? updatePending : createPending;
  const error = isEdit ? updateError : createError;

  const router = useRouter();

  const { data: companiesData, isLoading: isLoadingCompanies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesApi.getCompanies(),
  });

  const companies = (companiesData as any)?.items ?? [];
  const hasCompanies = companies.length > 0;

  const myCompany = companies[0];
  const companyStatus: string = myCompany?.status || 'draft';
  const isVerified = companyStatus === 'verified';

  const {
    register,
    handleSubmit,
    setValue,
    reset,
    formState: { errors },
  } = useForm<ListingInput>({
    resolver: zodResolver(listingSchema),
    defaultValues: {
      title: initialData?.title ?? '',
      materialType: initialData?.materialType ?? '',
      quantity: initialData?.quantity ?? 0,
      unit: initialData?.unit ?? 'kg',
      price: initialData?.price,
      currency: initialData?.currency ?? 'EUR',
      condition: initialData?.condition ?? 'použité',
      location: initialData?.location ?? '',
      companyId: initialData?.companyId ?? '',
      description: initialData?.description ?? '',
      imageUrl: initialData?.imageUrl ?? '',
    },
  });

  useEffect(() => {
    if (!initialData) return;
    reset({
      title: initialData.title ?? '',
      materialType: initialData.materialType ?? '',
      quantity: initialData.quantity ?? 0,
      unit: initialData.unit ?? 'kg',
      price: initialData.price,
      currency: initialData.currency ?? 'EUR',
      condition: initialData.condition ?? 'použité',
      location: initialData.location ?? '',
      companyId: initialData.companyId ?? '',
      description: initialData.description ?? '',
      imageUrl: initialData.imageUrl ?? '',
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  const onSubmit = (data: ListingInput) => {
    if (!hasCompanies) {
      return;
    }

    const onSuccess = () => {
      if (isEdit && listingId) {
        router.push(`/dashboard/listings/${listingId}`);
      } else {
        router.push('/dashboard');
      }
    };

    if (isEdit && listingId) {
      updateListing(data as any, { onSuccess });
    } else {
      createListing(data as any, { onSuccess });
    }
  };

  if (!isLoadingCompanies && !hasCompanies) {
    return (
      <div className="w-full max-w-2xl bg-slate-100 p-6 sm:p-8">
        <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: '#c9a84c' }}>
          Prvý krok
        </p>

        <h2 className="mt-2 text-xl font-bold text-slate-900">
          Najprv pridajte firmu
        </h2>

        <p className="mt-2 max-w-lg text-sm leading-relaxed text-slate-700">
          Každá ponuka musí patriť konkrétnej firme. Po vytvorení firmy sa sem môžete
          okamžite vrátiť a pridať ponuku materiálu.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Button
            type="button"
            className="font-semibold text-[#090807] hover:opacity-90"
            style={{ background: '#c9a84c' }}
            onClick={() => router.push('/dashboard/companies/new')}
          >
            Pridať firmu
          </Button>

          <Button
            type="button"
            variant="outline"
            className="border-slate-400 bg-transparent text-slate-700 hover:bg-slate-200"
            onClick={() => router.push('/dashboard')}
          >
            Späť na dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <>
    {hasCompanies && !isVerified && (
      <div
        className="mb-4 w-full max-w-2xl rounded-2xl border p-5"
        style={{
          borderColor: 'rgba(201,168,76,0.4)',
          background: 'rgba(201,168,76,0.06)',
        }}
      >
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.25em]" style={{ color: '#c9a84c' }}>
          Stav firmy: {companyStatus}
        </p>
        <p className="text-sm leading-relaxed" style={{ color: '#f3ead8' }}>
          ⚠️ Vaša firma ešte nie je overená. Ponuku môžete vytvoriť, ale
          publikovať ju bude možné až po schválení administrátorom.
        </p>
      </div>
    )}

    <form
      onSubmit={handleSubmit(onSubmit)}
      className="w-full max-w-2xl space-y-4 bg-slate-100 p-6 sm:p-8"
    >
      <div className="border-b border-slate-300 pb-4">
        <p className="text-[10px] font-semibold uppercase tracking-wider">
          {isEdit ? 'Upraviť ponuku' : 'Nová ponuka'}
        </p>
        <h2 className="mt-1 text-xl font-bold text-slate-900">{t('listingForm.titleAdd')}</h2>
        <p className="mt-1 text-sm text-slate-600">
          Vyplňte údaje o materiáli, ktorý chcete ponúknuť.
        </p>
      </div>

      {isLoadingCompanies && (
        <div className="rounded-xl border border-slate-300 bg-slate-50 p-3 text-sm text-slate-700">
          Načítavam firmy…
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-900/70 bg-red-950/40 p-3 text-sm text-red-200">
          {(error as any).message || 'Chyba pri vytváraní ponuky'}
        </div>
      )}

      <FormField label="Firma" error={errors.companyId?.message}>
        <select
          {...register('companyId')}
          disabled={isPending || isLoadingCompanies}
          className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-[#c9a84c] focus:ring-2 focus:ring-[#c9a84c]/30 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <option value="">— vyberte firmu —</option>
          {companies.map((company: any) => (
            <option key={company.id} value={company.id}>
              {company.legalName || company.name}
            </option>
          ))}
        </select>
      </FormField>

      <FormField label={t('listingForm.nameLabel')} error={errors.title?.message}>
        <Input
          {...register('title')}
          disabled={isPending || isLoadingCompanies}
          placeholder="Zvyšky železa"
          className="rounded-xl"
        />
      </FormField>

      <FormField label={t('listingForm.materialLabel')} error={errors.materialType?.message}>
        <Input
          {...register('materialType')}
          disabled={isPending || isLoadingCompanies}
          placeholder="železo, plast, drevo..."
          className="rounded-xl"
        />
      </FormField>

      <FormField label="Popis" error={errors.description?.message}>
        <textarea
          className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-[#c9a84c] focus:ring-2 focus:ring-[#c9a84c]/30 disabled:cursor-not-allowed disabled:opacity-50"
          rows={3}
          {...register('description')}
          disabled={isPending || isLoadingCompanies}
        />
      </FormField>

      <FormField label="URL fotky (voliteľné)" error={(errors as any).imageUrl?.message}>
        <Input
          placeholder="https://... alebo nahrajte súbor nižšie"
          {...register('imageUrl')}
          disabled={isPending || isLoadingCompanies}
          className="rounded-xl"
        />

        <input
          type="file"
          accept="image/*,.pdf"
          className="mt-2 block w-full text-sm text-slate-700 file:mr-3 file:rounded-lg file:border-0 file:bg-[#c9a84c] file:px-3 file:py-2 file:text-sm file:font-semibold file:text-[#090807] hover:file:opacity-90"
          disabled={isPending || isLoadingCompanies}
          onChange={async (event) => {
            const file = event.target.files?.[0];
            if (!file) return;

            try {
              const response = await uploadFile(file);
              const base = config.apiBaseUrl;
              const url = response.url.startsWith('http')
                ? response.url
                : base + response.url;

              setValue('imageUrl', url as any, { shouldValidate: true });
            } catch (uploadError: any) {
              alert(uploadError?.message || 'Nahranie súboru zlyhalo');
            }
          }}
        />
      </FormField>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label="Množstvo" error={errors.quantity?.message}>
          <Input
            type="number"
            step="0.01"
            {...register('quantity', { valueAsNumber: true })}
            disabled={isPending || isLoadingCompanies}
            className="rounded-xl"
          />
        </FormField>

        <FormField label="Jednotka" error={errors.unit?.message}>
          <Input
            {...register('unit')}
            disabled={isPending || isLoadingCompanies}
            placeholder="kg"
            className="rounded-xl"
          />
        </FormField>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label="Cena (voliteľné)" error={errors.price?.message}>
          <Input
            type="number"
            step="0.01"
            {...register('price', { valueAsNumber: true })}
            disabled={isPending || isLoadingCompanies}
            className="rounded-xl"
          />
        </FormField>

        <FormField label="Mena" error={errors.currency?.message}>
          <Input
            {...register('currency')}
            disabled={isPending || isLoadingCompanies}
            className="rounded-xl"
          />
        </FormField>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label={t('listingForm.conditionLabel')} error={errors.condition?.message}>
          <Input
            {...register('condition')}
            disabled={isPending || isLoadingCompanies}
            placeholder="nové / použité / odpad"
            className="rounded-xl"
          />
        </FormField>

        <FormField label="Lokalita" error={errors.location?.message}>
          <Input
            {...register('location')}
            disabled={isPending || isLoadingCompanies}
            placeholder="Bratislava"
            className="rounded-xl"
          />
        </FormField>
      </div>

      <div className="flex flex-wrap justify-end gap-3 border-t border-slate-300 pt-5">
        <Button
          type="button"
          variant="outline"
          className="border-slate-400 bg-transparent text-slate-700 hover:bg-slate-200"
          onClick={() => router.back()}
        >
          Zrušiť
        </Button>

        <Button
          type="submit"
          disabled={isPending || isLoadingCompanies || !hasCompanies}
          className="font-semibold text-[#090807] hover:opacity-90"
          style={{ background: '#c9a84c' }}
        >
          {isPending
            ? 'Ukladám...'
            : isEdit
              ? 'Uložiť zmeny'
              : 'Vytvoriť ponuku'}
        </Button>
      </div>
    </form>
    </>
  );
};
