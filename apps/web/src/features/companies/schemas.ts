import { z } from 'zod';

export const companySchema = z.object({
  legalName: z.string().min(2, 'Názov firmy musí mať aspoň 2 znaky'),
  registrationNumber: z.string().min(5, 'IČO musí mať aspoň 5 znakov'),
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
  taxIdentifier: z.string().optional(),
  email: z.string().email('Neplatný e-mail').optional().or(z.literal('')),
  phone: z.string().optional(),
});

export type CompanyInput = z.infer<typeof companySchema>;
