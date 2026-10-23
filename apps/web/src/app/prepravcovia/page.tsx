"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { config } from "@/lib/config";

const GOLD = "#c9a84c";
const MUTED = "#9a8f7c";

type Company = {
  id: string;
  tradingName?: string | null;
  legalName?: string | null;
  city?: string | null;
  logisticsCapability?: boolean | null;
};

type CompaniesResponse = {
  items: Company[];
  total: number;
};

async function fetchCarriers(): Promise<CompaniesResponse> {
  const token = localStorage.getItem("accessToken");
  const res = await fetch(`${config.apiBaseUrl}/companies?logisticsCapability=true&pageSize=50`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof body.detail === "string" ? body.detail : `HTTP ${res.status}`);
  }
  return body as CompaniesResponse;
}

export default function CarriersPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["carriers"],
    queryFn: fetchCarriers,
  });

  const items = data?.items || [];

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-2 font-serif text-3xl" style={{ color: GOLD }}>
        Prepravcovia
      </h1>
      <p className="mb-6 text-sm" style={{ color: MUTED }}>
        Firmy, ktoré poskytujú dopravu, skladovanie a logistické služby.
      </p>

      {isLoading ? (
        <p style={{ color: MUTED }}>Načítavam...</p>
      ) : error ? (
        <p style={{ color: "red" }}>{error.message}</p>
      ) : items.length === 0 ? (
        <p style={{ color: MUTED }}>Zatiaľ žiadni prepravcovia.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((c) => (
            <Link
              key={c.id}
              href={`/dashboard/companies/${c.id}`}
              className="block rounded-xl border p-4 transition hover:border-[#c9a84c]"
              style={{ borderColor: "rgba(201,168,76,0.25)" }}
            >
              <h2 className="font-semibold" style={{ color: GOLD }}>
                {c.tradingName || c.legalName || "Firma"}
              </h2>
              <p className="text-sm" style={{ color: MUTED }}>
                {c.city || "—"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
