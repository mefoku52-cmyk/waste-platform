'use client';

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { companySchema, CompanyInput } from '../schemas';
import { useCreateCompany } from '../hooks/use-create-company';
import { useUpdateCompany } from '../hooks/use-update-company';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { FormField } from '../../../components/ui/form-field';
import { useRouter } from 'next/navigation';
import { useT } from '@/lib/i18n/context';
import { uploadFile } from '../../uploads/api';
import { SignedImage } from '../../uploads/components/signed-image';
import { useAiFormFilling } from '@/lib/ai-agent/use-ai-form-filling';
import { COMPANY_FORM_FIELDS } from '@/lib/ai-agent/form-fields';

const ENTITY_TYPE_OPTIONS = [
  { value: 'sole_trader', labelKey: 'companyForm.entityType.soleTrader' },
  { value: 'company', labelKey: 'companyForm.entityType.company' },
  { value: 'ngo', labelKey: 'companyForm.entityType.ngo' },
] as const;

type CompanyFormData = Partial<CompanyInput> & {
  id?: string;
  legalName?: string | null;
  tradingName?: string | null;
  registrationNumber?: string | null;
  taxIdentifier?: string | null;
  vatIdentifier?: string | null;
  companyType?: string | null;
  entityType?: string | null;
  email?: string | null;
  phone?: string | null;
  countryCode?: string | null;
  addressLine1?: string | null;
  addressLine2?: string | null;
  city?: string | null;
  postalCode?: string | null;
  sellerCapability?: boolean | null;
  buyerCapability?: boolean | null;
  logisticsCapability?: boolean | null;
  logoUrl?: string | null;
};

type CompanyFormProps = {
  mode?: 'create' | 'edit';
  companyId?: string;
  initialData?: CompanyFormData;
};

export const CompanyForm = ({
  mode = 'create',
  companyId = '',
  initialData,
}: CompanyFormProps = {}) => {
  const { t } = useT();
  // logo_upload_marker
  const [logoUrl, setLogoUrl] = useState<string>(String(initialData?.logoUrl || ''));
  const [logoUploading, setLogoUploading] = useState(false);
  const router = useRouter();

  const createResult = useCreateCompany();
  const updateResult = useUpdateCompany(companyId);

  const isEdit = mode === 'edit' && Boolean(companyId);
  const { mutate: submitCompany, isPending, error } = isEdit
    ? updateResult
    : createResult;

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<CompanyInput>({
    resolver: zodResolver(companySchema),
    defaultValues: {
      entityType: 'company',
      countryCode: 'SK',
      companyType: 'seller_buyer',
      sellerCapability: true,
      buyerCapability: true,
      logisticsCapability: false,
    },
  });

  // Pri edit mode predvyplň z initialData
  useEffect(() => {
    if (!initialData) return;
    reset({
      entityType: (initialData.entityType as any) || 'company',
      legalName: initialData.legalName || '',
      tradingName: initialData.tradingName || '',
      registrationNumber: initialData.registrationNumber || '',
      companyType: (initialData.companyType as any) || 'seller_buyer',
      countryCode: initialData.countryCode || 'SK',
      addressLine1: initialData.addressLine1 || '',
      city: initialData.city || '',
      postalCode: initialData.postalCode || '',
      sellerCapability: Boolean(initialData.sellerCapability),
      buyerCapability: Boolean(initialData.buyerCapability),
      logisticsCapability: Boolean(initialData.logisticsCapability),
      vatIdentifier: initialData.vatIdentifier || '',
      email: initialData.email || '',
      phone: initialData.phone || '',
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialData?.id]);

  const entityType = watch('entityType');
  const isSoleTrader = entityType === 'sole_trader';
  const nameLabel = isSoleTrader
    ? t('companyForm.legalNameSoleTrader')
    : t('companyForm.legalNameCompany');

  // AI Agent — let the assistant fill this form (fill_form_field/highlight_field).
  useAiFormFilling({ setValue, fields: COMPANY_FORM_FIELDS });

  const onSubmit = (data: CompanyInput) => {
    // Backend očakáva obe polia (registrationNumber aj taxIdentifier).
    // Do DB sa ukladá registration_number; taxIdentifier slúži na RPO lookup.
    const payload = {
      ...data,
      logoUrl: logoUrl || null,
      taxIdentifier: data.registrationNumber,
      email: data.email || null,
      tradingName: data.tradingName || null,
      vatIdentifier: data.vatIdentifier || null,
      phone: data.phone || null,
    };
    submitCompany(payload as any, {
      onSuccess: () => {
        if (isEdit) {
          router.push(`/dashboard/companies/${companyId}`);
        } else {
          router.push('/dashboard');
        }
      },
    });
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-4 w-full max-w-2xl p-6 bg-slate-100"
    >
      <h2 className="text-2xl font-bold mb-6 text-gray-900">
        {isEdit ? t('companyForm.titleEdit') : t('companyForm.title')}
      </h2>

      {error && (
        <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md border border-red-200">
          {(error as any).message || (isEdit ? t('companies.errorSave') : t('companies.errorRegister'))}
        </div>
      )}

      {/* Typ subjektu — rádio, dynamicky prepína labely nižšie */}
      <FormField
        label={t('companyForm.entityTypeLabel')}
        error={(errors as any).entityType?.message}
      >
        <div className="flex flex-wrap gap-3">
          {ENTITY_TYPE_OPTIONS.map((opt) => (
            <label
              key={opt.value}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm cursor-pointer hover:border-[#c9a84c] has-[:checked]:border-[#c9a84c] has-[:checked]:bg-[#c9a84c]/10"
            >
              <input
                type="radio"
                value={opt.value}
                {...register('entityType')}
                disabled={isPending}
                className="accent-[#c9a84c]"
              />
              {t(opt.labelKey)}
            </label>
          ))}
        </div>
      </FormField>

      {/* Meno / Obchodný názov — label sa mení podľa entityType */}
      <FormField label={nameLabel} error={errors.legalName?.message}>
        <Input
          {...register('legalName')}
          disabled={isPending}
          placeholder={
            isSoleTrader ? 'Ján Novák' : 'Firma s.r.o.'
          }
        />
      </FormField>

      <FormField
        label={t('companyForm.tradingNameOptional')}
        error={errors.tradingName?.message}
      >
        <Input
          {...register('tradingName')}
          disabled={isPending}
          placeholder="Novák – stolárstvo"
        />
      </FormField>

      <div className="grid grid-cols-2 gap-4">
        {/* Jedno pole — IČO (8 číslic). Backend ho mapuje aj do taxIdentifier. */}
        <FormField
          label={t('companyForm.icoLabel')}
          error={errors.registrationNumber?.message}
        >
          <Input
            {...register('registrationNumber')}
            disabled={isPending}
            placeholder="54642442"
            maxLength={8}
          />
        </FormField>
        <FormField
          label={t('companyForm.vatLabel')}
          error={errors.vatIdentifier?.message}
        >
          <Input
            {...register('vatIdentifier')}
            disabled={isPending}
            placeholder="SK2020123456"
          />
        </FormField>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField label={t('companyForm.companyTypeLabel')} error={errors.companyType?.message}>
          <select
            {...register('companyType')}
            disabled={isPending}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
          >
            <option value="seller_buyer">{t('companyForm.sellerBuyer')}</option>
            <option value="seller">{t('companyForm.seller')}</option>
            <option value="buyer">{t('companyForm.buyer')}</option>
            <option value="logistics_partner">{t('companyForm.logistics')}</option>
          </select>
        </FormField>
        <FormField label={t('companyForm.countryLabel')} error={errors.countryCode?.message}>
          <Input
            {...register('countryCode')}
            disabled={isPending}
            placeholder="SK"
          />
        </FormField>
      </div>

      <FormField label={t('companyForm.addressLabel')} error={errors.addressLine1?.message}>
        <Input
          {...register('addressLine1')}
          disabled={isPending}
          placeholder="Hlavná 1"
        />
      </FormField>

      <div className="grid grid-cols-2 gap-4">
        <FormField label={t('companyForm.cityLabel')} error={errors.city?.message}>
          <Input {...register('city')} disabled={isPending} placeholder="Bratislava" />
        </FormField>
        <FormField label={t('companyForm.pscLabel')} error={errors.postalCode?.message}>
          <Input {...register('postalCode')} disabled={isPending} placeholder="81101" />
        </FormField>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField label={t('companyForm.emailLabel')} error={errors.email?.message}>
          <Input
            type="email"
            {...register('email')}
            disabled={isPending}
            placeholder="firma@example.sk"
          />
        </FormField>
        <FormField label={t('companyForm.phoneLabel')} error={errors.phone?.message}>
          <Input
            {...register('phone')}
            disabled={isPending}
            placeholder="+421 900 000 000"
          />
        </FormField>
      </div>

      {/* Logo firmy */}
      <FormField label="Logo firmy" error={(errors as any).logoUrl?.message}>
        <div className="flex items-center gap-4">
          {logoUrl ? (
            <SignedImage src={logoUrl} alt="Logo" className="h-16 w-16 rounded-lg object-cover" />
          ) : (
            <div
              className="flex h-16 w-16 items-center justify-center rounded-lg border border-dashed"
              style={{ borderColor: '#c9a84c', color: '#c9a84c' }}
            >
              LOGO
            </div>
          )}
          <input
            type="file"
            accept="image/*"
            disabled={isPending || logoUploading}
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              setLogoUploading(true);
              try {
                const res = await uploadFile(file);
                setLogoUrl(res.url);
              } catch (err: any) {
                alert(err?.message || 'Upload zlyhal');
              } finally {
                setLogoUploading(false);
              }
            }}
            className="text-sm"
          />
          {logoUrl ? (
            <button
              type="button"
              onClick={() => setLogoUrl('')}
              className="text-xs underline"
              style={{ color: '#c45c4a' }}
            >
              Odstrániť
            </button>
          ) : null}
        </div>
        <input type="hidden" {...register('logoUrl')} value={logoUrl} />
      </FormField>

      <div className="flex justify-end gap-4 mt-6">
        <Button
          type="button"
          variant="outline"
          onClick={() => router.back()}
        >
          {t('companyForm.cancel')}
        </Button>
        <Button
          type="submit"
          disabled={isPending}
          style={{ background: '#c9a84c', color: '#090807', borderColor: '#c9a84c' }}
          className="font-semibold hover:opacity-90"
        >
          {isPending
            ? t('companyForm.saving')
            : isEdit
              ? t('companyForm.saveChanges')
              : t('companyForm.submit')}
        </Button>
      </div>
    </form>
  );
};
