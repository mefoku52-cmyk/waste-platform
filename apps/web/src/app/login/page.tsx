import { LoginForm } from "@/features/auth";
import { BrandLogo } from "@/components/brand/logo";

export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center px-4 py-10">
      <div className="mb-8 flex flex-col items-center gap-3 text-center">
        <BrandLogo size="lg" />
        <p className="max-w-xs text-sm text-slate-600">
          Platforma pre obchod s odpadmi, vedľajšími produktmi a sekundárnymi surovinami
        </p>
      </div>
      <LoginForm />
      <p className="mt-8 text-center text-[11px] text-slate-400">
        Circular Materials Exchange Platform
      </p>
    </div>
  );
}
