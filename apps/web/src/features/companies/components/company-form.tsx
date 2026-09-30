'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { companySchema, CompanyInput } from '../schemas';
import { useCreateCompany } from '../hooks/use-create-company';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { FormField } from '../../../components/ui/form-field';
import { useRouter } from 'next/navigation';
import { useT } from "@/lib/i18n/context";

export const CompanyForm = () => {
  const { mutate: createCompany, isPending, error } = useCreateCompany();
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CompanyInput>({
    resolver: zodResolver(companySchema),
    defaultValues: {
      countryCode: 'SK',
      companyType: 'seller_buyer',
      sellerCapability: true,
      buyerCapability: true,
      logisticsCapability: false,
    },
  });

  const onSubmit = (data: CompanyInput) => {
    const payload = {
      ...data,
      email: data.email || null,
      tradingName: data.tradingName || null,
      taxIdentifier: data.taxIdentifier || null,
      vatIdentifier: data.vatIdentifier || null,
      phone: data.phone || null,
    };
    createCompany(payload as any, {
      onSuccess: () => router.push('/dashboard'),
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 w-full max-w-2xl p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-gray-900">{t('companyForm.title')}</h2>

      {error && (
        <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md border border-red-200">
          {(error as any).message || 'Chyba pri registrácii firmy'}
        </div>
      )}

      <FormField label={t('companyForm.legalName')} error={errors.legalName?.message}>
        <Input {...register('legalName')} disabled={isPending} placeholder={t('companyForm.legalNamePh')} />
      </FormField>

      <FormField label={t('companyForm.tradingName')} error={errors.tradingName?.message}>
        <Input {...register('tradingName')} disabled={isPending} />
      </FormField>

      <div className="grid grid-cols-2 gap-4">
        <FormField label={t('companyForm.registrationNumber')} error={errors.registrationNumber?.message}>
          <Input {...register('registrationNumber')} disabled={isPending} />
        </FormField>
        <FormField label="IČO" error={errors.taxIdentifier?.message}>
          <Input {...register('taxIdentifier')} disabled={isPending} placeholder="8 cislic" />
        </FormField>
        <FormField label="DIČ" error={errors.vatIdentifier?.message}>
          <Input {...register('vatIdentifier')} disabled={isPending} />
        </FormField>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField label={t('companyForm.companyType')} error={errors.companyType?.message}>
          <select
            {...register('companyType')}
            disabled={isPending}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
          >
            <option value="seller_buyer">Predajca + Kupujúci</option>
            <option value="seller">{t('companyForm.seller')}</option>
            <option value="buyer">{t('companyForm.buyer')}</option>
            <option value="logistics_partner">{t('companyForm.logistics')}</option>
          </select>
        </FormField>
        <FormField label={t('companyForm.countryCode')} error={errors.countryCode?.message}>
          <Input {...register('countryCode')} disabled={isPending} placeholder="SK" />
        </FormField>
      </div>

      <FormField label={t('companyForm.address')} error={errors.addressLine1?.message}>
        <Input {...register('addressLine1')} disabled={isPending} />
      </FormField>

      <div className="grid grid-cols-2 gap-4">
        <FormField label={t('companyForm.city')} error={errors.city?.message}>
          <Input {...register('city')} disabled={isPending} />
        </FormField>
        <FormField label="PSČ" error={errors.postalCode?.message}>
          <Input {...register('postalCode')} disabled={isPending} />
        </FormField>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField label={t('companyForm.email')} error={errors.email?.message}>
          <Input type="email" {...register('email')} disabled={isPending} />
        </FormField>
        <FormField label={t('companyForm.phone')} error={errors.phone?.message}>
          <Input {...register('phone')} disabled={isPending} />
        </FormField>
      </div>

      <div className="flex justify-end gap-4 mt-6">
        <Button type="button" variant="outline" onClick={() => router.back()}>
          Zrušiť
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Ukladám...' : 'Registrovať'}
        </Button>
      </div>
    </form>
  );
};
