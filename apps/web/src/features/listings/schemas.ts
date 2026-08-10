import { z } from 'zod';

export const listingSchema = z.object({
  title: z.string().min(3, 'Názov musí mať aspoň 3 znaky'),
  materialType: z.string().min(2, 'Typ materiálu je povinný'),
  quantity: z.number().min(0.01, 'Množstvo musí byť kladné'),
  unit: z.string().min(1, 'Jednotka je povinná'),
  price: z.number().optional(),
  currency: z.string().default('EUR'),
  condition: z.string().min(1, 'Stav je povinný'),
  location: z.string().min(2, 'Lokalita je povinná'),
  companyId: z.string().uuid('Vyber firmu'),
  description: z.string().optional(),
});

export type ListingInput = z.infer<typeof listingSchema>;
