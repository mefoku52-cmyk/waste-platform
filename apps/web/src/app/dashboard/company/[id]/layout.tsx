"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";

const GOLD = "#c9a84c";
const MUTED = "#9a8f7c";

const menuItems = [
  { href: "", label: "Prehľad", img: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=100&q=80" },
  { href: "/listings", label: "Ponuky", img: "https://images.unsplash.com/photo-1553413077-190dd305871c?w=100&q=80" },
  { href: "/inquiries", label: "Dopyty", img: "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=100&q=80" },
  { href: "/members", label: "Členovia", img: "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=100&q=80" },
  { href: "/photos", label: "Fotky", img: "https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=100&q=80" },
  { href: "/reviews", label: "Recenzie", img: "https://images.unsplash.com/photo-1512314889357-e157c22f938d?w=100&q=80" },
  { href: "/settings", label: "Nastavenia", img: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=100&q=80" },
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
                className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition"
                style={{
                  background: isActive ? "rgba(201,168,76,0.15)" : "transparent",
                  color: isActive ? GOLD : MUTED,
                }}
              >
                <img 
                  src={item.img} 
                  alt={item.label} 
                  className="h-6 w-6 rounded-full object-cover border border-[rgba(201,168,76,0.3)]" 
                />
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
