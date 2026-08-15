'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema, LoginInput } from '../schemas';
import { useLogin } from '../hooks/use-login';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { FormField } from '../../../components/ui/form-field';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export const LoginForm = () => {
  const { mutate: login, isPending, error } = useLogin();
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = (data: LoginInput) => {
    login(data, {
      onSuccess: () => {
        router.push('/dashboard');
      },
    });
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-4 w-full max-w-sm p-6 bg-white rounded-lg shadow-md"
    >
      <h2 className="text-2xl font-bold text-center mb-6">Prihlásenie</h2>

      {error && (
        <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md border border-red-200">
          {(error as any).message || 'Nesprávne meno alebo heslo'}
        </div>
      )}

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
          placeholder="******"
          {...register('password')}
          disabled={isPending}
        />
      </FormField>

      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? 'Prihlasujem...' : 'Prihlásiť sa'}
      </Button>

      <div className="text-center text-sm space-y-2 pt-2">
        <p className="text-gray-600">
          Nemáte účet?{' '}
          <Link href="/register" className="text-blue-600 hover:underline font-medium">
            Registrácia
          </Link>
        </p>
        <p className="text-gray-400 text-xs">
          Zabudnuté heslo – zatiaľ nie je dostupné (pridáme neskôr)
        </p>
      </div>
          <p className="text-center text-sm text-gray-600">
        <Link href="/forgot-password" className="text-blue-600 hover:underline">Zabudnuté heslo?</Link>
        {' · '}
        <Link href="/register" className="text-blue-600 hover:underline">Registrácia</Link>
      </p>
    </form>
  );
};
