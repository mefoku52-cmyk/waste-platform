"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";

const GOLD = "#c9a84c";
const MUTED = "#9a8f7c";

const menuItems = [
  { href: "", label: "📊 Prehľad" },
  { href: "/listings", label: "📦 Ponuky" },
  { href: "/inquiries", label: "✉️ Dopyty" },
  { href: "/members", label: "👥 Členovia" },
  { href: "/photos", label: "📸 Fotky" },
  { href: "/settings", label: "⚙️ Nastavenia" },
];

export default function CompanyDashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams<{ id: string }>();
  const pathname = usePathname();
  const companyId = String(params?.id || "");

  return (
    <div className="flex min-h-screen bg-[#0b0b0b]">
      <aside
        className="w-64 shrink-0 border-r p-4"
        style={{ borderColor: "rgba(201,168,76,0.25)" }}
      >
        <Link
          href="/dashboard/companies"
          className="mb-6 block text-sm"
          style={{ color: GOLD }}
        >
          ← Späť na firmy
        </Link>
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const href = `/dashboard/company/${companyId}${item.href}`;
            const isActive = pathname === href;
            return (
              <Link
                key={item.href}
                href={href}
                className="block rounded-lg px-3 py-2 text-sm transition"
                style={{
                  background: isActive ? "rgba(201,168,76,0.15)" : "transparent",
                  color: isActive ? GOLD : MUTED,
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
