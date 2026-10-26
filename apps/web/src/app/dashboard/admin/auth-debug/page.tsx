'use client';

import { useEffect, useState } from "react";

import { tokenStore } from "@/lib/auth/token-store";

export default function AuthDebugPage() {
  const [state, setState] = useState<{
    status: string;
    summary?: Record<string, unknown>;
    error?: string;
  }>({ status: "loading" });

  useEffect(() => {
    const token = tokenStore.getToken();

    if (!token) {
      setState({ status: "error", error: "NO_ACCESS_TOKEN" });
      return;
    }

    fetch("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        const data = await res.json().catch(() => null);
        setState({
          status: String(res.status),
          summary: data && {
            isPlatformAdmin: data.isPlatformAdmin,
            roleCodes: data.roleCodes,
            userRole: data.user?.role,
            userEmail: data.user?.email,
            membershipsCount: Array.isArray(data.memberships)
              ? data.memberships.length
              : null,
          },
          error: data ? undefined : "INVALID_JSON",
        });
      })
      .catch((error: unknown) => {
        setState({
          status: "error",
          error: error instanceof Error ? error.message : "FETCH_FAILED",
        });
      });
  }, []);

  return (
    <main className="min-h-screen bg-[#090807] p-4 text-[#e8d48b]">
      <h1 className="mb-4 text-lg font-bold">Auth debug</h1>
      <pre className="whitespace-pre-wrap break-words rounded border border-[#c9a84c]/30 p-3 text-sm">
{JSON.stringify(state, null, 2)}
      </pre>
    </main>
  );
}
