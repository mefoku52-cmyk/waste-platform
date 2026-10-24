"use client";

import { useQuery } from "@tanstack/react-query";
import { config } from "@/lib/config";

const GOLD = "#c9a84c";
const MUTED = "#9a8f7c";

type Stats = {
  daily: Record<string, number>;
  weekly: Record<string, number>;
  monthly: Record<string, number>;
  total: number;
};

export default function AdminAnalyticsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-analytics"],
    queryFn: async () => {
      const token = localStorage.getItem("accessToken");
      const res = await fetch(`${config.apiBaseUrl}/admin/analytics/stats`, {
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json() as Promise<Stats>;
    },
  });

  return (
    <div className="p-6">
      <h1 className="mb-6 font-serif text-3xl" style={{ color: GOLD }}>Návštevnosť</h1>
      
      {isLoading ? (
        <p style={{ color: MUTED }}>Načítavam...</p>
      ) : error ? (
        <p className="text-red-500">Chyba: {error.message}</p>
      ) : data ? (
        <>
          <div className="mb-8 rounded-xl border p-6" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
            <p className="text-sm" style={{ color: MUTED }}>Celková návštevnosť</p>
            <p className="text-4xl font-bold" style={{ color: GOLD }}>{data.total || 0}</p>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-xl border p-4" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
              <h2 className="mb-2 text-lg font-semibold" style={{ color: GOLD }}>Denná</h2>
              {Object.entries(data.daily || {}).slice(-7).map(([date, count]) => (
                <div key={date} className="flex justify-between text-sm">
                  <span style={{ color: MUTED }}>{date}</span>
                  <span style={{ color: "#f3e6c4" }}>{count}</span>
                </div>
              ))}
            </div>

            <div className="rounded-xl border p-4" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
              <h2 className="mb-2 text-lg font-semibold" style={{ color: GOLD }}>Týždenná</h2>
              {Object.entries(data.weekly || {}).slice(-4).map(([week, count]) => (
                <div key={week} className="flex justify-between text-sm">
                  <span style={{ color: MUTED }}>{week}</span>
                  <span style={{ color: "#f3e6c4" }}>{count}</span>
                </div>
              ))}
            </div>

            <div className="rounded-xl border p-4" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
              <h2 className="mb-2 text-lg font-semibold" style={{ color: GOLD }}>Mesačná</h2>
              {Object.entries(data.monthly || {}).slice(-12).map(([month, count]) => (
                <div key={month} className="flex justify-between text-sm">
                  <span style={{ color: MUTED }}>{month}</span>
                  <span style={{ color: "#f3e6c4" }}>{count}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
