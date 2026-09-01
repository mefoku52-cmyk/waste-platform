'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerSchema, RegisterInput } from '../schemas';
import { useRegister } from '../hooks/use-register';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { FormField } from '../../../components/ui/form-field';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export const RegisterForm = () => {
  const { mutate: registerUser, isPending, error } = useRegister();
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = (data: RegisterInput) => {
    registerUser(data, {
      onSuccess: () => {
        router.push('/login');
      },
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 w-full max-w-sm p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-center mb-6">Registrácia</h2>

      {error && (
        <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md border border-red-200">
          {(error as any).message || 'Registrácia zlyhala'}
        </div>
      )}

      <FormField label="Meno" error={errors.firstName?.message}>
        <Input
          type="text"
          placeholder="Ján"
          {...register('firstName')}
          disabled={isPending}
        />
      </FormField>

      <FormField label="Priezvisko" error={errors.lastName?.message}>
        <Input
          type="text"
          placeholder="Novák"
          {...register('lastName')}
          disabled={isPending}
        />
      </FormField>

      <FormField label="E-mail" error={errors.email?.message}>
        <Input
          type="email"
          placeholder="vas@email.sk"
          {...register('email')}
          disabled={isPending}
        />
      </FormField>

      <FormField label="Heslo" error={errors.password?.message}>
        <Input
          type="password"
          placeholder="Minimálne 8 znakov"
          {...register('password')}
          disabled={isPending}
        />
      </FormField>

      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? 'Registrujem...' : 'Zaregistrovať sa'}
      </Button>

      <p className="text-center text-sm text-gray-600 mt-4">
        Už máš účet?{' '}
        <Link href="/login" className="text-blue-600 hover:underline">
          Prihlásiť sa
        </Link>
      </p>
    </form>
  );
};
