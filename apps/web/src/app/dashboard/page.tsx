"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useUnreadNotifications } from "@/features/notifications";
import { useMarketplace } from "@/features/listings";
import { useQuery } from "@tanstack/react-query";
import { http } from "@/lib/api/http";
import { useT } from "@/lib/i18n/context";
import { LanguageSwitcher } from "@/components/language-switcher";
import { useLogout, useCurrentUser, useIsPlatformAdmin } from "@/features/auth";

type Listing = {
  id: string;
  title: string;
  company: string;
  location: string;
  category: string;
  quantity: string;
  published: string;
  note: string;
  transport: string;
  images: string[];
};

const GOLD = "#c9a84c";
const GOLD_BRIGHT = "#e8d48b";
const BG = "#090807";
const FG = "#f3ead8";
const MUTED = "#9a8f7c";
const FAINT = "#6e6658";

const categoryKeys = ["all", "wood", "metal", "paper", "plastics", "bio"] as const;
const categorySkMap: Record<string, string> = {
  all: "Všetko", wood: "Drevo", metal: "Kov",
  paper: "Papier", plastics: "Plasty", bio: "Bioodpad",
};
const topLinkKeys = ["overview", "listings", "marketplace", "matches", "companies", "documents", "chat"] as const;
const PAGE_SIZE = 6;

function fixImageUrl(u: string | null | undefined): string | null {
  if (!u) return null;
  let s = String(u).trim();
  s = s.replace(/\/api\/v1\/api\/v1\//g, "/api/v1/");
  if (/^https?:\/\//.test(s)) {
    return s.replace(/\/api\/v1\/api\/v1\//g, "/api/v1/");
  }
  // Backend URL z env, nie hardcoded localhost
  const base = (process.env.NEXT_PUBLIC_API_BASE_URL || "https://waste-platform.onrender.com/api/v1")
    .replace(/\/api\/v1\/?$/, "");
  if (s.startsWith("/api/v1/")) return base + s;
  if (s.startsWith("/")) return base + "/api/v1" + s;
  return null;
}

function makeFormatRelative(t: (k: string, fb?: string) => string) {
  return (iso: string | null | undefined): string => {
    if (!iso) return "\u2014";
    const d = new Date(iso);
    if (isNaN(d.getTime())) return "\u2014";
    const diff = Date.now() - d.getTime();
    const day = 86400000;
    if (diff < day) return t("dashboard.dateToday");
    if (diff < 2 * day) return t("dashboard.dateYesterday");
    const days = Math.floor(diff / day);
    if (days < 7) return t("dashboard.dateDaysAgo").replace("{n}", String(days));
    return d.toLocaleDateString();
  };
}

export default function DashboardPage() {
  const { t } = useT();
  const { data: me } = useCurrentUser();
  const { data: unreadData } = useUnreadNotifications();
  const unreadChat = Number((unreadData as any)?.unread || 0);
  const isAdmin = useIsPlatformAdmin();
  const myEmail = String((me as any)?.email || (me as any)?.user?.email || '');
  const { mutateAsync: logout, isPending: logoutPending } = useLogout();
  const formatRelative = useMemo(() => makeFormatRelative(t), [t]);

  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [location, setLocation] = useState("");
  const [page, setPage] = useState(1);
  const [openId, setOpenId] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<Record<string, string>>({});

  const { data: apiResp, isLoading, error } = useMarketplace();

  const { data: companiesResp } = useQuery({
    queryKey: ["companies-for-dashboard"],
    queryFn: () => http.get<any>("/companies"),
  });

  const companiesMap = useMemo(() => {
    const raw: any = companiesResp;
    const items: any[] = Array.isArray(raw) ? raw : raw?.data ?? raw?.items ?? [];
    const m: Record<string, string> = {};
    for (const c of items) {
      const n = c.tradingName || c.trading_name || c.legalName || c.legal_name || "";
      if (c.id && n) m[String(c.id)] = n;
    }
    return m;
  }, [companiesResp]);

  const listings: Listing[] = useMemo(() => {
    const raw: any = apiResp;
    const items: any[] = Array.isArray(raw) ? raw : raw?.data ?? raw?.items ?? [];
    return items.map((it: any) => ({
      id: String(it.id),
      title: it.title ?? t("dashboard.titleNoName"),
      company:
        it.company?.name ??
        it.companyName ??
        companiesMap[String(it.companyId ?? it.company_id ?? "")] ??
        t("dashboard.companyUnknown"),
      location: it.location ?? "\u2014",
      category: it.materialType ?? it.material_type ?? "\u2014",
      quantity: [it.quantity, it.unit].filter(Boolean).join(" ") || "\u2014",
      published: formatRelative(it.createdAt ?? it.created_at),
      note: it.description ?? "",
      transport: it.transport ?? "\u2014",
      images: [fixImageUrl(it.imageUrl ?? it.image_url)].filter(Boolean) as string[],
    }));
  }, [apiResp, companiesMap, t, formatRelative]);

  const filtered = useMemo(() => {
    return listings.filter((item) => {
      const matchesQuery =
        query.trim() === "" ||
        `${item.title} ${item.company} ${item.location} ${item.category} ${item.note} ${item.transport}`
          .toLowerCase()
          .includes(query.toLowerCase());
      const selectedSk = categorySkMap[category] || "Všetko";
      const matchesCategory = category === "all" || item.category === selectedSk;
      const matchesLocation =
        location.trim() === "" ||
        item.location.toLowerCase().includes(location.toLowerCase());
      return matchesQuery && matchesCategory && matchesLocation;
    });
  }, [query, category, location, listings]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPageItems = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filtered.slice(start, start + PAGE_SIZE);
  }, [filtered, page]);

  function changeCategory(next: string) {
    setCategory(next);
    setPage(1);
  }
  function changePage(next: number) {
    if (next < 1 || next > pageCount) return;
    setPage(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const navHrefs: Record<string, string> = {
    listings: "/dashboard/listings",
    documents: "/dashboard/documents",
    companies: "/dashboard/companies",
    chat: "/dashboard/chat",
  };

  return (
    <div className="min-h-screen" style={{ background: BG, color: FG }}>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400;1,9..144,500&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />

      {/* HEADER */}
      <header className="sticky top-0 z-40 border-b backdrop-blur-md" style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)', background: 'rgba(9,8,7,0.85)' }}>
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <Link href="/" className="flex items-center gap-3">
            <img src="/trc-mark.jpg" alt="TRČ" className="h-10 w-10 rounded-full object-cover" />
            <div className="hidden sm:block">
              <p className="text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>CMEP · OBEHOVÉ MATERIÁLY</p>
              <p className="text-lg leading-none" style={{ fontFamily: 'Fraunces, serif' }}>Tržnica</p>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <MyListingsMenu label={t("dashboard.myListings")} />
            <span className="hidden text-sm md:inline" style={{ color: MUTED }}>{myEmail || "—"}</span>
            {isAdmin && (
              <Link
                href="/dashboard/admin"
                className="rounded-md border px-3 py-1.5 text-xs font-semibold"
                style={{ borderColor: GOLD, color: GOLD_BRIGHT }}
              >
                ⚙ Admin
              </Link>
            )}
            <LanguageSwitcher />
            <button
              type="button"
              onClick={async () => {
                try {
                  await logout(undefined as any);
                } finally {
                  window.location.href = "/login";
                }
              }}
              disabled={logoutPending}
              className="text-sm underline underline-offset-4"
              style={{ color: MUTED }}
            >
              {logoutPending ? "..." : t("dashboard.logout")}
            </button>
          </div>
        </div>

        {/* NAV */}
        <nav className="mx-auto flex max-w-6xl flex-wrap gap-5 px-4 pb-3">
          {topLinkKeys.map((k) => {
            const href = navHrefs[k];
            const label = t("dashboard.nav." + k, k === "chat" ? "Chat" : k);
            if (href) {
              return (
                <Link key={k} href={href} className="text-sm transition-colors hover:opacity-80" style={{ color: FG }}>
                  {label}
                  {k === "chat" && unreadChat > 0 && (
                    <span className="ml-1.5 inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-bold" style={{ background: '#c45c4a', color: FG }}>
                      {unreadChat}
                    </span>
                  )}
                </Link>
              );
            }
            return (
              <span key={k} className="text-sm" style={{ color: MUTED }}>{label}</span>
            );
          })}
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10">
        {/* HERO */}
        <section className="mb-10">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>TRŽNICA</p>
          <h1 className="text-4xl leading-[1.05] tracking-[-0.02em] md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
            Ponuky firiem a obehových materiálov
          </h1>
        </section>

        {/* FILTER */}
        <section className="mb-8">
          <div className="grid gap-3 md:grid-cols-[1.4fr_0.7fr_auto]">
            <input
              type="search"
              placeholder={t("dashboard.searchPlaceholder")}
              value={query}
              onChange={(e) => { setQuery(e.target.value); setPage(1); }}
              className="h-12 rounded-md border bg-transparent px-4 outline-none"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)', color: FG }}
            />
            <input
              type="text"
              placeholder={t("dashboard.locationPlaceholder")}
              value={location}
              onChange={(e) => { setLocation(e.target.value); setPage(1); }}
              className="h-12 rounded-md border bg-transparent px-4 outline-none"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)', color: FG }}
            />
            <button
              type="button"
              className="h-12 rounded-md px-6 font-semibold"
              style={{ background: GOLD, color: BG }}
            >
              {t("dashboard.searchBtn")}
            </button>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {categoryKeys.map((k) => {
              const active = k === category;
              return (
                <button
                  key={k}
                  type="button"
                  onClick={() => changeCategory(k)}
                  className="rounded-md border px-4 py-2 text-sm transition-colors"
                  style={{
                    borderColor: active ? GOLD : 'color-mix(in srgb, #c9a84c 30%, transparent)',
                    background: active ? GOLD : 'transparent',
                    color: active ? BG : FG,
                  }}
                >
                  {t("dashboard." + k)}
                </button>
              );
            })}
          </div>
        </section>

        {/* LIST HEAD */}
        <section className="mb-4 flex flex-wrap items-center justify-between gap-4 border-t pt-6" style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)' }}>
          <div style={{ color: MUTED }}>
            {isLoading ? (
              <span>{t("common.loading")}</span>
            ) : error ? (
              <span style={{ color: '#c45c4a' }}>
                {t("dashboard.loadError")} {(error as any)?.message || t("dashboard.loadErrorUnknown")}
              </span>
            ) : (
              <>
                <strong style={{ color: FG }}>{filtered.length}</strong> {t("dashboard.activeListings")}
              </>
            )}
          </div>
          <div className="flex flex-wrap gap-4 text-sm">
            <Link href="/dashboard/listings/new" style={{ color: GOLD_BRIGHT }}>+ Pridať ponuku</Link>
            <Link href="/dashboard/companies/new" style={{ color: GOLD_BRIGHT }}>+ Pridať firmu</Link>
            <Link href="/dashboard/documents/new" style={{ color: GOLD_BRIGHT }}>+ Pridať dokument</Link>
          </div>
        </section>

        {/* LISTING GRID */}
        <section>
          {currentPageItems.length === 0 && !isLoading ? (
            <div className="rounded-2xl border py-16 text-center" style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}>
              <h3 className="text-2xl" style={{ fontFamily: 'Fraunces, serif' }}>{t("dashboard.notFound")}</h3>
              <p className="mt-2 text-sm" style={{ color: MUTED }}>{t("dashboard.notFoundHint")}</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {currentPageItems.map((item) => {
                const isOpen = openId === item.id;
                const heroImage = selectedImage[item.id] || item.images[0];
                return (
                  <article
                    key={item.id}
                    className="overflow-hidden rounded-2xl border transition-colors"
                    style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}
                  >
                    <button
                      type="button"
                      onClick={() => setOpenId(isOpen ? null : item.id)}
                      className="w-full text-left"
                    >
                      {/* image */}
                      {heroImage ? (
                        <div className="relative aspect-[16/10] w-full">
                          <img src={heroImage} alt={item.title} className="h-full w-full object-cover opacity-90" />
                          <div className="absolute inset-0" style={{ background: 'linear-gradient(to top, rgba(9,8,7,0.95) 0%, rgba(9,8,7,0.3) 40%, transparent 75%)' }} />
                          <div className="absolute bottom-0 left-0 right-0 p-5">
                            <p className="text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>{item.category}</p>
                            <h3 className="mt-1 text-2xl leading-tight" style={{ fontFamily: 'Fraunces, serif', color: GOLD_BRIGHT }}>{item.title}</h3>
                          </div>
                        </div>
                      ) : (
                        <div className="relative aspect-[16/10] w-full" style={{ background: '#12100e' }}>
                          <div className="absolute bottom-0 left-0 right-0 p-5">
                            <p className="text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>{item.category}</p>
                            <h3 className="mt-1 text-2xl leading-tight" style={{ fontFamily: 'Fraunces, serif', color: GOLD_BRIGHT }}>{item.title}</h3>
                          </div>
                        </div>
                      )}

                      {/* summary */}
                      <div className="p-5">
                        <p className="line-clamp-2 text-sm" style={{ color: MUTED }}>{item.note || "\u2014"}</p>
                        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs" style={{ color: FAINT }}>
                          <span>{item.company}</span>
                          <span>· {item.location}</span>
                          <span>· {item.quantity}</span>
                          <span>· {item.published}</span>
                        </div>
                      </div>
                    </button>

                    {/* expanded detail */}
                    {isOpen && (
                      <div className="border-t p-5" style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)' }}>
                        <dl className="grid gap-3 text-sm">
                          {[
                            [t("dashboard.company"), item.company],
                            [t("dashboard.location"), item.location],
                            [t("dashboard.category"), item.category],
                            [t("dashboard.quantity"), item.quantity],
                            [t("dashboard.transport"), item.transport],
                            [t("dashboard.published"), item.published],
                          ].map(([k, v]) => (
                            <div key={String(k)} className="grid grid-cols-[130px_1fr] gap-3 border-b pb-2" style={{ borderColor: 'color-mix(in srgb, #c9a84c 10%, transparent)' }}>
                              <dt style={{ color: FAINT }}>{k}</dt>
                              <dd style={{ color: FG, fontWeight: 500 }}>{v}</dd>
                            </div>
                          ))}
                        </dl>

                        {/* thumbs */}
                        {item.images.length > 1 && (
                          <div className="mt-4 flex gap-2">
                            {item.images.map((image) => (
                              <button
                                key={image}
                                type="button"
                                onClick={() => setSelectedImage((prev) => ({ ...prev, [item.id]: image }))}
                                className="rounded-md border p-0"
                                style={{ borderColor: heroImage === image ? GOLD : 'transparent' }}
                              >
                                <img src={image} alt="" className="h-16 w-16 rounded-md object-cover" />
                              </button>
                            ))}
                          </div>
                        )}

                        <Link
                          href={`/dashboard/listings/${item.id}`}
                          className="mt-5 inline-block rounded-md px-5 py-2.5 text-sm font-semibold"
                          style={{ background: GOLD, color: BG }}
                        >
                          {t("dashboard.contactCompany")}
                        </Link>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </section>

        {/* PAGINATION */}
        {pageCount > 1 && (
          <nav className="mt-10 flex items-center justify-between border-t pt-6" style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)' }}>
            <button
              type="button"
              onClick={() => changePage(page - 1)}
              disabled={page === 1}
              className="rounded-md border px-4 py-2 text-sm disabled:opacity-40"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)', color: FG }}
            >
              {t("dashboard.prev")}
            </button>
            <div className="flex gap-2">
              {Array.from({ length: pageCount }, (_, i) => i + 1).map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => changePage(num)}
                  className="h-10 w-10 rounded-md border text-sm"
                  style={{
                    borderColor: num === page ? GOLD : 'color-mix(in srgb, #c9a84c 25%, transparent)',
                    background: num === page ? GOLD : 'transparent',
                    color: num === page ? BG : FG,
                  }}
                >
                  {num}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={() => changePage(page + 1)}
              disabled={page === pageCount}
              className="rounded-md border px-4 py-2 text-sm disabled:opacity-40"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)', color: FG }}
            >
              {t("dashboard.next")}
            </button>
          </nav>
        )}
      </main>
    </div>
  );
}

function MyListingsMenu({ label }: { label: string }) {
  const [open, setOpen] = useState(false);
  const { t } = useT();
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-semibold"
        style={{ borderColor: GOLD, color: GOLD_BRIGHT }}
        aria-expanded={open}
      >
        {label}
        <span className="text-xs" style={{ opacity: 0.7 }}>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div
          className="absolute right-0 top-full z-50 mt-2 min-w-[240px] rounded-xl border p-2"
          style={{ background: '#12100e', borderColor: 'color-mix(in srgb, #c9a84c 35%, transparent)', boxShadow: '0 12px 32px rgba(0,0,0,0.6)' }}
        >
          {[
            { href: "/dashboard/listings", ico: "👁", label: t("dashboard.viewAll") },
            { href: "/dashboard/listings/new", ico: "＋", label: t("dashboard.addNewListing") },
            { href: "/dashboard/listings?filter=draft", ico: "✎", label: t("dashboard.drafts") },
            { href: "/dashboard/listings?filter=published", ico: "✓", label: t("dashboard.publishedOnly") },
          ].map((it) => (
            <Link
              key={it.href}
              href={it.href}
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/5"
              style={{ color: FG }}
            >
              <span className="w-5 text-center" style={{ color: GOLD }}>{it.ico}</span>
              {it.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
