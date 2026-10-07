import { z } from 'zod';

export const companySchema = z.object({
  // Typ subjektu — dynamicky mení label „Obchodný názov" / „Meno a priezvisko"
  entityType: z.enum(['sole_trader', 'company', 'ngo'], {
    errorMap: () => ({ message: 'Vyber typ subjektu' }),
  }).default('company'),

  // Pre firmu je to obchodný názov, pre SZČO je to meno a priezvisko.
  legalName: z.string().min(2, 'Názov musí mať aspoň 2 znaky'),

  // Jedno pole — je to IČO (8 číslic). Backend ho mapuje aj do
  // taxIdentifier (kompatibilita), do DB sa ukladá ako registration_number.
  registrationNumber: z.string().regex(/^\d{8}$/, 'IČO musí mať presne 8 číslic'),

  companyType: z.enum(['seller', 'buyer', 'seller_buyer', 'logistics_partner'], {
    errorMap: () => ({ message: 'Vyber typ firmy' }),
  }),
  countryCode: z.string().min(2).default('SK'),
  addressLine1: z.string().min(5, 'Adresa je povinná'),
  city: z.string().min(2, 'Mesto je povinné'),
  postalCode: z.string().min(3, 'PSČ je povinné'),
  sellerCapability: z.boolean().default(true),
  buyerCapability: z.boolean().default(true),
  logisticsCapability: z.boolean().default(false),
  tradingName: z.string().optional(),
  vatIdentifier: z.string().optional(),
  email: z.string().email('Neplatný e-mail').optional().or(z.literal('')),
  phone: z.string().optional(),
});

export type CompanyInput = z.infer<typeof companySchema>;
