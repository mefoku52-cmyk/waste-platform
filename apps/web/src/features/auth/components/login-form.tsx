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
      className="w-full max-w-sm space-y-4 rounded-2xl border border-white/60 bg-white/90 p-6 shadow-xl shadow-slate-900/5 backdrop-blur-md sm:p-8"
    >
      <div className="mb-2 text-center">
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Prihlásenie</h2>
        <p className="mt-1 text-xs text-slate-500">Vstup do firemného účtu</p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {(error as any).message || 'Nesprávne meno alebo heslo'}
        </div>
      )}

      <FormField label="E-mail" error={errors.email?.message}>
        <Input
          type="email"
          placeholder="vas@email.sk"
          {...register('email')}
          disabled={isPending}
          className="rounded-xl"
        />
      </FormField>

      <FormField label="Heslo" error={errors.password?.message}>
        <Input
          type="password"
          placeholder="******"
          {...register('password')}
          disabled={isPending}
          className="rounded-xl"
        />
      </FormField>

      <label className="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" defaultChecked {...register('remember')} className="rounded border-slate-300" />
        Zapamätať prihlásenie
      </label>

      <Button
        type="submit"
        className="w-full rounded-xl bg-emerald-600 py-2.5 font-semibold hover:bg-emerald-700"
        disabled={isPending}
      >
        {isPending ? 'Prihlasujem...' : 'Prihlásiť sa'}
      </Button>

      <div className="flex flex-col items-center gap-2 pt-1 text-center text-sm">
        <Link href="/forgot-password" className="text-emerald-700 hover:underline">
          Zabudnuté heslo?
        </Link>
        <button
          type="button"
          onClick={() => alert('Google login: treba GOOGLE_CLIENT_ID z Google Cloud Console. Dáme to hneď ako pošleš Client ID.')}
          className="w-full rounded-xl border border-slate-200 bg-white py-2.5 text-sm font-medium text-slate-800 hover:bg-slate-50"
        >
          Prihlásiť cez Google
        </button>
        <Link href="/register" className="font-medium text-slate-700 hover:text-emerald-700 hover:underline">
          Vytvoriť účet
        </Link>
      </div>
    </form>
  );
};
