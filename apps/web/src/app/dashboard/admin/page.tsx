'use client';

import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { useAdminStats } from "@/features/admin/hooks/use-admin-stats";
import { AdminUsersTable } from "@/features/admin/components/admin-users-table";
import { redirect } from "next/navigation";

export default function AdminPage() {
  const { user, isLoading } = useAuthRequired();
  const { data: stats, isLoading: isLoadingStats } = useAdminStats();

  if (isLoading) return null;

  // Ochrana: Iba admin môže pristupovať na túto stránku
  if (user && user.role !== 'admin') {
    redirect('/dashboard');
  }

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Administrácia systému</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Používatelia" value={stats?.total_users} loading={isLoadingStats} />
        <StatCard title="Ponuky" value={stats?.total_listings} loading={isLoadingStats} />
        <StatCard title="Firmy" value={stats?.total_companies} loading={isLoadingStats} />
        <StatCard title="Čakajúce overenia" value={stats?.pending_verifications} loading={isLoadingStats} color="text-orange-600" />
      </div>

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
