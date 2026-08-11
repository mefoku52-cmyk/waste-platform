'use client';

import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { useLogout } from "@/features/auth/hooks/use-logout";
import { Button } from "@/components/ui/button";
import { ListingsTable } from "@/features/listings/components/listings-table";
import { MarketplaceTable } from "@/features/listings/components/marketplace-table";
import { InquiriesTable } from "@/features/inquiries/components/inquiries-table";
import { OpenInquiriesBadge } from "@/features/inquiries/components/open-inquiries-badge";
import { CompaniesTable } from "@/features/companies/components/companies-table";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const { user, isLoading } = useAuthRequired();
  const { mutate: logout, isPending: isLoggingOut } = useLogout();
  const router = useRouter();

  if (isLoading) return null;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Platforma pre obehové materiály</h1>
            {user?.role === 'admin' && (
              <button
                type="button"
                onClick={() => router.push('/dashboard/admin')}
                className="text-xs text-blue-600 hover:underline font-medium"
              >
                Vstúpiť do Admin panelu →
              </button>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{user?.email}</p>
              <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => logout()}
              disabled={isLoggingOut}
            >
              {isLoggingOut ? 'Odhlasujem...' : 'Odhlásiť sa'}
            </Button>
          </div>
        </div>

        <div className="grid gap-12">
          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Aktuálne ponuky</h2>
              <Button size="sm" onClick={() => router.push('/dashboard/listings/new')}>
                Pridať ponuku
              </Button>
            </div>
            <ListingsTable />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Trhovisko</h2>
            </div>
            <p className="mb-3 text-sm text-gray-500">Publikované ponuky od iných firiem</p>
            <MarketplaceTable />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Prijaté dopyty <OpenInquiriesBadge /></h2>
            </div>
            <p className="mb-3 text-sm text-gray-500">Záujem o tvoje ponuky</p>
            <InquiriesTable mode="received" />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Odoslané dopyty</h2>
            </div>
            <p className="mb-3 text-sm text-gray-500">Tvoj záujem o cudzie ponuky</p>
            <InquiriesTable mode="sent" />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Registrované firmy</h2>
              <Button size="sm" variant="secondary" onClick={() => router.push('/dashboard/companies/new')}>
                Pridať firmu
              </Button>
            </div>
            <CompaniesTable />
          </section>
        </div>
      </div>
    </div>
  );
}
