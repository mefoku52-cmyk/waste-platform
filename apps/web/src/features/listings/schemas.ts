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
  // imageUrl môže byť:
  //   - prázdny string (bez fotky)
  //   - plná URL (https://...)
  //   - relatívna cesta z API ("/api/v1/uploads/<file_id>")
  // SignedImage potrebuje file_id v ceste, preto relatívna cesta je preferovaná.
  imageUrl: z
    .string()
    .refine(
      (v) =>
        v === '' ||
        /^https?:\/\//.test(v) ||
        /^\/api\/v1\/uploads\//.test(v),
      { message: 'Neplatná URL fotky' },
    )
    .optional(),

});

export type ListingInput = z.infer<typeof listingSchema>;
