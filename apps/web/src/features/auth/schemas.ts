import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Neplatný formát e-mailu'),
  password: z.string().min(6, 'Heslo musí mať aspoň 6 znakov'),
});

export type LoginInput = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  email: z.string().email('Neplatný formát e-mailu'),
  firstName: z.string().min(2, 'Meno musí mať aspoň 2 znaky'),
  lastName: z.string().min(2, 'Priezvisko musí mať aspoň 2 znaky'),
  password: z.string().min(8, 'Heslo musí mať aspoň 8 znakov'),
});

export type RegisterInput = z.infer<typeof registerSchema>;
