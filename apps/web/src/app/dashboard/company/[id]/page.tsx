"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { http } from "@/lib/api/http";

const GOLD = "#c9a84c";
const MUTED = "#9a8f7c";

export default function CompanyOverviewPage() {
  const params = useParams<{ id: string }>();
  const companyId = String(params?.id || "");

  const companyQuery = useQuery({
    queryKey: ["company", companyId],
    queryFn: () => http.get<{ data: any }>(`/companies/${companyId}`),
    enabled: Boolean(companyId),
  });

  const company = companyQuery.data?.data;

  return (
    <div>
      <h1 className="mb-6 font-serif text-3xl" style={{ color: GOLD }}>
        {company?.tradingName || company?.legalName || "Firemný dashboard"}
      </h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="cmep-panel rounded-xl p-4">
          <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>
            Stav
          </p>
          <p className="mt-1 text-xl font-semibold">{company?.status || "—"}</p>
        </div>
        <div className="cmep-panel rounded-xl p-4">
          <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>
            Tier
          </p>
          <p className="mt-1 text-xl font-semibold">{company?.subscriptionTier || "FREE"}</p>
        </div>
        <div className="cmep-panel rounded-xl p-4">
          <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>
            IČO
          </p>
          <p className="mt-1 text-xl font-semibold">{company?.registrationNumber || "—"}</p>
        </div>
      </div>
      <p className="mt-8 text-sm" style={{ color: MUTED }}>
        Vitajte vo firemnom dashboarde. Použite menu vľavo na správu ponúk, dopytov,
        členov a fotiek.
      </p>
    </div>
  );
}
