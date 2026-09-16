'use client';

import { useAuthRequired } from "@/features/auth";
import { useAdminStats } from "@/features/admin";
import { AdminUsersTable } from "@/features/admin";
import { CompaniesTable } from "@/features/companies";
import { redirect } from "next/navigation";

export default function AdminPage() {
  const { user, isLoading } = useAuthRequired();
  const { data: stats, isLoading: isLoadingStats } = useAdminStats();
  const safeStats = (stats || {}) as {
    total_users?: number;
    total_listings?: number;
    total_companies?: number;
    pending_verifications?: number;
  };

  if (isLoading) return null;


  // Ochrana: Iba admin môže pristupovať na túto stránku
  const roleCodes: string[] = ((user as any)?.roleCodes || []).map((r: string) => String(r).toLowerCase());
  const userEmail = String((user as any)?.email || (user as any)?.user?.email || '').toLowerCase();
  const adminEmails = String(process.env.NEXT_PUBLIC_PLATFORM_ADMIN_EMAILS || 'admin@cmep.dev')
    .split(',')
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean);
  const isAdmin =
    roleCodes.includes('admin') ||
    roleCodes.includes('platform_admin') ||
    adminEmails.includes(userEmail);

  if (user && !isAdmin) {
    redirect('/dashboard');
  }

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Administrácia systému</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Používatelia" value={safeStats.total_users} loading={isLoadingStats} />
        <StatCard title="Ponuky" value={safeStats.total_listings} loading={isLoadingStats} />
        <StatCard title="Firmy" value={safeStats.total_companies} loading={isLoadingStats} />
        <StatCard title="Čakajúce overenia" value={safeStats.pending_verifications} loading={isLoadingStats} color="text-orange-600" />
      </div>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">Firmy na overenie</h2>
        <p className="text-sm text-gray-500">
          Firmy, ktoré požiadali o overenie. Klikni <strong>Overiť</strong> pre schválenie alebo
          <strong>Zamietnuť</strong> pre odmietnutie.
        </p>
        <CompaniesTable />
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">Správa používateľov</h2>
        <AdminUsersTable />
      </section>
    </div>
  );
}

function StatCard({ title, value, loading, color = "text-blue-600" }: { title: string, value?: number, loading: boolean, color?: string }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">{title}</p>
      <p className={`mt-2 text-3xl font-bold ${color}`}>
        {loading ? '...' : value ?? 0}
      </p>
    </div>
  );
}
