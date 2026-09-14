'use client';

import { useEffect, useRef, useState } from 'react';
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
import { useT } from '../../../lib/i18n/context';

declare global {
  interface Window {
    google?: any;
  }
}

export const LoginForm = () => {
  const { t } = useT();
  const { mutateAsync: login, isPending, error } = useLogin();
  const router = useRouter();
  const googleButtonRef = useRef<HTMLDivElement | null>(null);
  const [showPassword, setShowPassword] = useState(false);

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
      alert(e?.message || t('login.errorFailed'));
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
            alert(e?.message || t('login.errorGoogleFailed'));
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
        <h2 className="text-xl font-bold tracking-tight text-slate-900">{t('login.title')}</h2>
        <p className="mt-1 text-xs text-slate-500">{t('login.subtitle_company')}</p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {(error as any).message || t('login.errorInvalid')}
        </div>
      )}

      <FormField label={t('login.emailLabel')} error={errors.email?.message}>
        <Input
          type="email"
          placeholder={t('login.emailPlaceholder')}
          {...register('email')}
          disabled={isPending}
          className="rounded-xl"
        />
      </FormField>

      <FormField label={t('login.passwordLabel')} error={errors.password?.message}>
        <div className="relative">
          <Input
            type={showPassword ? 'text' : 'password'}
            placeholder="******"
            {...register('password')}
            disabled={isPending}
            className="rounded-xl pr-10"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
            tabIndex={-1}
          >
            {showPassword ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            )}
          </button>
        </div>
      </FormField>

      <div className="flex items-center justify-between text-sm">
        <label className="inline-flex items-center gap-2 text-slate-600">
          <input type="checkbox" {...register('remember')} className="rounded border-slate-300" />
          {t('login.remember')}
        </label>
        <Link href="/forgot-password" className="text-emerald-700 hover:text-emerald-800">
          {t('login.forgot')}
        </Link>
      </div>

      <Button type="submit" className="w-full rounded-xl" disabled={isPending}>
        {isPending ? t('login.submitting') : t('login.submit')}
      </Button>

      <div className="relative py-2">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-slate-200" />
        </div>
        <div className="relative flex justify-center text-xs uppercase tracking-[0.2em] text-slate-400">
          <span className="bg-white px-3">{t('login.or')}</span>
        </div>
      </div>

      <div ref={googleButtonRef} className="flex justify-center" />

      <p className="text-center text-sm text-slate-500">
        {t('login.noAccount')}{' '}
        <Link href="/register" className="font-medium text-emerald-700 hover:text-emerald-800">
          {t('login.registerLink')}
        </Link>
      </p>
    </form>
  );
};
