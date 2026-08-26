'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { listingSchema, ListingInput } from '../schemas';
import { useCreateListing } from '../hooks/use-create-listing';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { FormField } from '../../../components/ui/form-field';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '../../companies/api';
import { uploadFile } from '../../uploads/api';

export const ListingForm = () => {
  const { mutate: createListing, isPending, error } = useCreateListing();
  const router = useRouter();

  const { data: companiesData } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesApi.getCompanies(),
  });

  const companies = (companiesData as any)?.items ?? [];

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ListingInput>({
    resolver: zodResolver(listingSchema),
    defaultValues: {
      imageUrl: '',
      quantity: 0,
      unit: 'kg',
      currency: 'EUR',
      condition: 'použité',
    },
  });

  const onSubmit = (data: ListingInput) => {
    createListing(data as any, {
      onSuccess: () => {
        router.push('/dashboard');
      },
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 w-full max-w-2xl p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-gray-900">Pridať novú ponuku</h2>

      {error && (
        <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md border border-red-200">
          {(error as any).message || 'Chyba pri vytváraní ponuky'}
        </div>
      )}

      <FormField label="Firma" error={errors.companyId?.message}>
        <select
          {...register('companyId')}
          disabled={isPending}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
        >
          <option value="">— vyber firmu —</option>
          {companies.map((c: any) => (
            <option key={c.id} value={c.id}>
              {c.legalName || c.name}
            </option>
          ))}
        </select>
      </FormField>

      <FormField label="Názov ponuky" error={errors.title?.message}>
        <Input {...register('title')} disabled={isPending} placeholder="Zvyšky železa" />
      </FormField>

      <FormField label="Typ materiálu" error={errors.materialType?.message}>
        <Input {...register('materialType')} disabled={isPending} placeholder="železo, plast, drevo..." />
      </FormField>

      <FormField label="Popis" error={errors.description?.message}>
        <textarea
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          rows={3}
          {...register('description')}
          disabled={isPending}
        />
      </FormField>

      <FormField label="URL fotky (voliteľné)" error={(errors as any).imageUrl?.message}>
        <Input
          placeholder="https://... alebo nahraj nižšie"
          {...register('imageUrl')}
          disabled={isPending}
        />
        <input
          type="file"
          accept="image/*,.pdf"
          className="mt-2 block w-full text-sm text-gray-600"
          disabled={isPending}
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            try {
              const res = await uploadFile(f);
              const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001/api/v1';
              const full = res.url.startsWith('http') ? res.url : base + res.url;
              setValue('imageUrl', full as any, { shouldValidate: true });
            } catch (err: any) {
              alert(err?.message || 'Upload zlyhal');
            }
          }}
        />
      </FormField>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="Množstvo" error={errors.quantity?.message}>
          <Input type="number" step="0.01" {...register('quantity', { valueAsNumber: true })} disabled={isPending} />
        </FormField>
        <FormField label="Jednotka" error={errors.unit?.message}>
          <Input {...register('unit')} disabled={isPending} placeholder="kg" />
        </FormField>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="Cena (voliteľné)" error={errors.price?.message}>
          <Input type="number" step="0.01" {...register('price', { valueAsNumber: true })} disabled={isPending} />
        </FormField>
        <FormField label="Mena" error={errors.currency?.message}>
          <Input {...register('currency')} disabled={isPending} />
        </FormField>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField label="Stav" error={errors.condition?.message}>
          <Input {...register('condition')} disabled={isPending} placeholder="nové / použité / odpad" />
        </FormField>
        <FormField label="Lokalita" error={errors.location?.message}>
          <Input {...register('location')} disabled={isPending} placeholder="Bratislava" />
        </FormField>
      </div>

      <div className="flex justify-end gap-4 mt-6">
        <Button type="button" variant="outline" onClick={() => router.back()}>
          Zrušiť
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Ukladám...' : 'Vytvoriť'}
        </Button>
      </div>
    </form>
  );
};
