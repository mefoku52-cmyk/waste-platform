'use client';

import { useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema, LoginInput } from '../schemas';
import { useLogin } from '../hooks/use-login';
import { authApi } from '../api';
import { tokenStore } from '../../../lib/auth/token-store';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { FormField } from '../../../components/ui/form-field';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

declare global {
  interface Window {
    google?: any;
  }
}

export const LoginForm = () => {
  const { mutateAsync: login, isPending, error } = useLogin();
  const router = useRouter();
  const googleButtonRef = useRef<HTMLDivElement | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginInput) => {
    try {
      await login(data);


      router.refresh();
      router.push('/dashboard');
    } catch (e: any) {
      alert(e?.message || 'Prihlásenie zlyhalo');
    }
  };

  useEffect(() => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

    if (!clientId || !googleButtonRef.current) return;

    const initGoogle = () => {
      if (!window.google || !googleButtonRef.current) return;

      googleButtonRef.current.innerHTML = '';

      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response: { credential?: string }) => {
          try {
            if (!response.credential) {
              throw new Error('Google credential missing');
            }

            const result = await authApi.googleLogin(response.credential);
            tokenStore.setTokens(
              result.accessToken,
              result.refreshToken,
              true,
            );


            router.refresh();
            router.push('/dashboard');
          } catch (e: any) {
            alert(e?.message || 'Google prihlásenie zlyhalo');
          }
        },
      });

      window.google.accounts.id.renderButton(googleButtonRef.current, {
        theme: 'outline',
        size: 'large',
        width: 320,
        text: 'signin_with',
        shape: 'rectangular',
      });
    };

    const existingScript = document.querySelector(
      'script[src="https://accounts.google.com/gsi/client"]'
    ) as HTMLScriptElement | null;

    if (existingScript) {
      if (window.google) initGoogle();
      else existingScript.addEventListener('load', initGoogle, { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = initGoogle;
    document.head.appendChild(script);

    return () => {
      script.onload = null;
    };
  }, [router]);

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

      <div className="flex items-center justify-between text-sm">
        <label className="inline-flex items-center gap-2 text-slate-600">
          <input type="checkbox" {...register('remember')} className="rounded border-slate-300" />
          Zapamätať si ma
        </label>
        <Link href="/forgot-password" className="text-emerald-700 hover:text-emerald-800">
          Zabudnuté heslo?
        </Link>
      </div>

      <Button type="submit" className="w-full rounded-xl" disabled={isPending}>
        {isPending ? 'Prihlasujem...' : 'Prihlásiť sa'}
      </Button>

      <div className="relative py-2">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-slate-200" />
        </div>
        <div className="relative flex justify-center text-xs uppercase tracking-[0.2em] text-slate-400">
          <span className="bg-white px-3">alebo</span>
        </div>
      </div>

      <div ref={googleButtonRef} className="flex justify-center" />

      <p className="text-center text-sm text-slate-500">
        Nemáte účet?{' '}
        <Link href="/register" className="font-medium text-emerald-700 hover:text-emerald-800">
          Zaregistrujte sa
        </Link>
      </p>
    </form>
  );
};
