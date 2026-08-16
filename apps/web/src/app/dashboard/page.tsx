'use client';

import { MatchesPanel } from "@/features/listings/components/matches-panel";

import { ComplianceTable } from "@/features/compliance/components/compliance-table";

import { AuditTable } from "@/features/admin/components/audit-table";
import { DocumentsTable } from "@/features/documents/components/documents-table";

import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { useLogout } from "@/features/auth/hooks/use-logout";
import { Button } from "@/components/ui/button";
import { ListingsTable } from "@/features/listings/components/listings-table";
import { NotificationsPanel } from "@/features/notifications/components/notifications-panel";
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

        
        <nav className="mb-6 flex flex-wrap gap-2 rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
          <a href="#ponuky" className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800 hover:bg-blue-50 hover:text-blue-700">Ponuky</a>
          <a href="#trhovisko" className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800 hover:bg-blue-50 hover:text-blue-700">Trhovisko</a>
          <a href="#zhody" className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800 hover:bg-blue-50 hover:text-blue-700">Zhody</a>
          <a href="#prijate" className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800 hover:bg-blue-50 hover:text-blue-700">Prijaté dopyty</a>
          <a href="#odoslane" className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800 hover:bg-blue-50 hover:text-blue-700">Odoslané</a>
          <a href="#firmy" className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800 hover:bg-blue-50 hover:text-blue-700">Firmy</a>
          <a href="#dokumenty" className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800 hover:bg-blue-50 hover:text-blue-700">Dokumenty</a>
          <a href="#audit" className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800 hover:bg-blue-50 hover:text-blue-700">Audit</a>
          <a href="#compliance" className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800 hover:bg-blue-50 hover:text-blue-700">Compliance</a>
        </nav>

        <div className="grid gap-12">
          <section>
            <NotificationsPanel />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 id="ponuky" className="text-xl font-semibold text-gray-800">Aktuálne ponuky</h2>
              <Button size="sm" onClick={() => router.push('/dashboard/listings/new')}>
                Pridať ponuku
              </Button>
            </div>
            <ListingsTable />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 id="trhovisko" className="text-xl font-semibold text-gray-800">Trhovisko</h2>
            </div>
            <p className="mb-3 text-sm text-gray-500">Publikované ponuky od iných firiem</p>
            <MarketplaceTable />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 id="zhody" className="text-xl font-semibold text-gray-800">Odporúčané zhody</h2>
            </div>
            <p className="mb-3 text-sm text-gray-500">Publikované ponuky s rovnakým typom materiálu (bez tvojich firiem)</p>
            <MatchesPanel />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 id="prijate" className="text-xl font-semibold text-gray-800">Prijaté dopyty <OpenInquiriesBadge /></h2>
            </div>
            <p className="mb-3 text-sm text-gray-500">Záujem o tvoje ponuky</p>
            <InquiriesTable mode="received" />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 id="odoslane" className="text-xl font-semibold text-gray-800">Odoslané dopyty</h2>
            </div>
            <p className="mb-3 text-sm text-gray-500">Tvoj záujem o cudzie ponuky</p>
            <InquiriesTable mode="sent" />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 id="firmy" className="text-xl font-semibold text-gray-800">Registrované firmy</h2>
              <Button size="sm" variant="secondary" onClick={() => router.push('/dashboard/companies/new')}>
                Pridať firmu
              </Button>
            </div>
            <CompaniesTable />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 id="dokumenty" className="text-xl font-semibold text-gray-800">Dokumenty</h2>
              <Button size="sm" variant="secondary" onClick={() => router.push('/dashboard/documents/new')}>
                Pridať dokument
              </Button>
            </div>
            <DocumentsTable />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 id="audit" className="text-xl font-semibold text-gray-800">Audit log</h2>
            </div>
            <AuditTable />
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 id="compliance" className="text-xl font-semibold text-gray-800">Compliance</h2>
            </div>
            <ComplianceTable />
          </section>
        </div>
      </div>
    </div>
  );
}
