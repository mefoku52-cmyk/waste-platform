"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useMarketplace } from "@/features/listings";
import { useQuery } from "@tanstack/react-query";
import { http } from "@/lib/api/http";
import { useT } from "@/lib/i18n/context";
import { LanguageSwitcher } from "@/components/language-switcher";
import { useLogout } from "@/features/auth";

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



const categoryKeys = ["all", "wood", "metal", "paper", "plastics", "bio"] as const;
const categorySkMap: Record<string, string> = {
  all: "Všetko", wood: "Drevo", metal: "Kov",
  paper: "Papier", plastics: "Plasty", bio: "Bioodpad",
};
const topLinkKeys = ["overview", "listings", "marketplace", "matches", "companies", "documents"] as const;
const PAGE_SIZE = 6;


function fixImageUrl(u: string | null | undefined): string | null {
  if (!u) return null;
  let s = String(u).trim();
  // zlepenec /api/v1/api/v1 -> /api/v1
  s = s.replace(/\/api\/v1\/api\/v1\//g, "/api/v1/");
  // ak uz je absolutna, skolabuj /api/v1/api/v1 v strede
  if (/^https?:\/\//.test(s)) {
    return s.replace(/\/api\/v1\/api\/v1\//g, "/api/v1/");
  }
  // NEXT_PUBLIC_API_BASE_URL je cele http://127.0.0.1:8001/api/v1
  // image_url z DB je /api/v1/uploads/xxx.png -> chceme http://127.0.0.1:8001/api/v1/uploads/xxx.png
  const base = "http://127.0.0.1:8001";
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
    const items: any[] = Array.isArray(raw)
      ? raw
      : raw?.data ?? raw?.items ?? [];
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
  }, [apiResp, companiesMap, t]);

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

  return (
    <main className="market-page">
      <header className="market-top">
        <div className="market-brand-wrap">
          <img src="/rc-logo.png" alt="CMEP" className="cmep-logo" />
          <div className="market-brand">
            <p className="market-mini">{t("dashboard.mini")}</p>
            <h1>{t("dashboard.title")}</h1>
          </div>
        </div>

        <div className="market-account">
          <MyListingsMenu label={t("dashboard.myListings")} />
          <span>admin@cmep.dev</span>
          <span>owner</span>
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
          >
            {logoutPending ? "..." : t("dashboard.logout")}
          </button>
        </div>
      </header>

      <nav className="top-nav" aria-label="Hlavná navigácia">
        {topLinkKeys.map((k) => {
          const hrefs: Record<string, string> = {
            listings: "/dashboard/listings",
            documents: "/dashboard/documents",
            companies: "/dashboard/companies",
          };
          const href = hrefs[k];
          return href ? (
            <Link key={k} href={href}>
              {t("dashboard.nav." + k)}
            </Link>
          ) : (
            <a key={k} href="#">
              {t("dashboard.nav." + k)}
            </a>
          );
        })}
      </nav>

      <section className="search-panel">
        <div className="search-panel-main">
          <div>
            <p className="market-mini">{t("dashboard.market")}</p>
            <h2>{t("dashboard.searchTitle")}</h2>
          </div>

          <div className="search-row">
            <input
              type="search"
              placeholder={t("dashboard.searchPlaceholder")}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
            />

            <input
              type="text"
              placeholder={t("dashboard.locationPlaceholder")}
              value={location}
              onChange={(e) => {
                setLocation(e.target.value);
                setPage(1);
              }}
            />

            <button type="button">{t("dashboard.searchBtn")}</button>
          </div>
        </div>

        <div className="categories">
          {categoryKeys.map((k) => (
            <button
              key={k}
              type="button"
              className={k === category ? "active" : ""}
              onClick={() => changeCategory(k)}
            >
              {t("dashboard." + k)}
            </button>
          ))}
        </div>
      </section>

      <section className="list-head">
        <div>
          {isLoading ? (
            <span>{t("common.loading")}</span>
          ) : error ? (
            <span style={{ color: "#b91c1c" }}>
              {t("dashboard.loadError")} {(error as any)?.message || t("dashboard.loadErrorUnknown")}
            </span>
          ) : (
            <>
              <strong>{filtered.length}</strong> {t("dashboard.activeListings")}
            </>
          )}
        </div>

        <div className="list-actions">
          <Link href="/dashboard/listings/new">{t("dashboard.addListing")}</Link>
          <Link href="/dashboard/companies/new">{t("dashboard.addCompany")}</Link>
          <Link href="/dashboard/documents/new">{t("dashboard.addDocument")}</Link>
        </div>
      </section>

      <section className="listing-list" aria-label="Zoznam ponúk">
        {currentPageItems.map((item) => {
          const isOpen = openId === item.id;
          const heroImage = selectedImage[item.id] || item.images[0];

          return (
            <article key={item.id} className={`listing-row ${isOpen ? "open" : ""}`}>
              <button
                type="button"
                className="listing-summary"
                onClick={() => setOpenId(isOpen ? null : item.id)}
                aria-expanded={isOpen}
              >
                <div className="listing-main">
                  <h3>{item.title}</h3>
                  <p className="listing-note">{item.note}</p>

                  <div className="listing-meta">
                    <span>{item.company}</span>
                    <span>{item.location}</span>
                    <span>{item.category}</span>
                    <span>{item.quantity}</span>
                    <span>{item.published}</span>
                  </div>
                </div>

                <div className="listing-side">
                  <img
                    src={item.images[0]}
                    alt={item.title}
                    width="84"
                    height="84"
                  />
                </div>
              </button>

              {isOpen && (
                <div className="listing-detail">
                  <div className="detail-gallery">
                    <img
                      className="detail-hero"
                      src={heroImage}
                      alt={item.title}
                      width="560"
                      height="360"
                    />

                    <div className="thumbs">
                      {item.images.map((image) => (
                        <button
                          key={image}
                          type="button"
                          className={heroImage === image ? "active" : ""}
                          onClick={() =>
                            setSelectedImage((prev) => ({ ...prev, [item.id]: image }))
                          }
                        >
                          <img src={image} alt={`${item.title} ${t("dashboard.preview")}`} width="72" height="72" />
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="detail-info">
                    <h4>{t("dashboard.detail")}</h4>

                    <dl>
                      <div>
                        <dt>{t("dashboard.company")}</dt>
                        <dd>{item.company}</dd>
                      </div>
                      <div>
                        <dt>{t("dashboard.location")}</dt>
                        <dd>{item.location}</dd>
                      </div>
                      <div>
                        <dt>{t("dashboard.category")}</dt>
                        <dd>{item.category}</dd>
                      </div>
                      <div>
                        <dt>{t("dashboard.quantity")}</dt>
                        <dd>{item.quantity}</dd>
                      </div>
                      <div>
                        <dt>{t("dashboard.transport")}</dt>
                        <dd>{item.transport}</dd>
                      </div>
                      <div>
                        <dt>{t("dashboard.published")}</dt>
                        <dd>{item.published}</dd>
                      </div>
                    </dl>

                    <p>{t("dashboard.sectionNote")}</p>

                    <div className="detail-actions">
                      <Link href={`/dashboard/listings/${item.id}`}>{t("dashboard.contactCompany")}</Link>
                    </div>
                  </div>
                </div>
              )}
            </article>
          );
        })}

        {currentPageItems.length === 0 && (
          <div className="empty-state">
            <h3>{t("dashboard.notFound")}</h3>
            <p>{t("dashboard.notFoundHint")}</p>
          </div>
        )}
      </section>

      <nav className="pagination" aria-label="Stránkovanie">
        <button type="button" onClick={() => changePage(page - 1)} disabled={page === 1}>
          {t("dashboard.prev")}
        </button>

        <div className="pages">
          {Array.from({ length: pageCount }, (_, index) => index + 1).map((num) => (
            <button
              key={num}
              type="button"
              className={num === page ? "active" : ""}
              onClick={() => changePage(num)}
            >
              {num}
            </button>
          ))}
        </div>

        <button type="button" onClick={() => changePage(page + 1)} disabled={page === pageCount}>
          {t("dashboard.next")}
        </button>
      </nav>

      <style jsx>{`
        :global(*) {
          box-sizing: border-box;
        }

        :global(body) {
          margin: 0;
          background: #0a0f11;
          color: #e6eceb;
          font-family: Arial, Helvetica, sans-serif;
        }

        :global(a) {
          color: inherit;
          text-decoration: none;
        }

        button,
        input {
          font: inherit;
        }

        .market-page {
          width: min(1380px, 100%);
          margin: 0 auto;
          padding: 18px 18px 60px;
        }

        .market-top {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 18px;
          padding: 4px 0 14px;
        }

        .market-mini {
          margin: 0 0 6px;
          color: #5d7c7e;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.12em;
          text-transform: uppercase;
        }

        .market-brand-wrap {
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .cmep-logo {
          width: 100px;
          height: 100px;
          object-fit: contain;
          background: transparent;
          border: 0;
          padding: 0;
          flex-shrink: 0;
          filter: drop-shadow(0 0 3px rgba(212, 160, 23, 0.25));
        }

        .market-brand h1,
        .search-panel h2,
        .listing-row h3,
        .empty-state h3,
        .detail-info h4 {
          margin: 0;
        }

        .market-brand h1 {
          font-size: clamp(28px, 4vw, 42px);
          line-height: 1.02;
          letter-spacing: -0.04em;
        }

        .market-account {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
          color: #5e6c70;
          font-size: 14px;
        }

        :global(.mylistings-wrap) {
          position: relative;
        }
        :global(.mylistings-btn) {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding: 18px 36px;
          border: 0;
          background: linear-gradient(180deg, #f0c14b 0%, #d4a017 100%);
          color: #1f2a2d;
          border-radius: 14px;
          font-size: 20px;
          font-weight: 900;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          cursor: pointer;
          box-shadow: 0 4px 0 #a67c00, 0 6px 20px rgba(212, 160, 23, 0.35);
          transition: transform 0.1s, box-shadow 0.1s;
          line-height: 1;
          white-space: nowrap;
        }
        :global(.mylistings-btn:hover) {
          background: linear-gradient(180deg, #f7cf5c 0%, #e6b32a 100%);
          transform: translateY(-2px);
          box-shadow: 0 6px 0 #a67c00, 0 8px 24px rgba(212, 160, 23, 0.5);
        }
        :global(.mylistings-btn:active) {
          transform: translateY(3px);
          box-shadow: 0 1px 0 #a67c00;
        }
        :global(.mylistings-arrow) {
          font-size: 14px;
          opacity: 0.8;
          transition: transform 0.15s;
        }
        :global(.mylistings-btn.open .mylistings-arrow) {
          transform: rotate(180deg);
        }
        :global(.mylistings-menu) {
          position: absolute;
          right: 0;
          top: calc(100% + 8px);
          min-width: 260px;
          background: #1a1e21;
          border: 1px solid rgba(212, 160, 23, 0.5);
          border-radius: 12px;
          padding: 8px;
          box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
          z-index: 100;
        }
        :global(.mylistings-menu a),
        :global(.mylistings-menu button) {
          display: flex;
          align-items: center;
          gap: 12px;
          width: 100%;
          padding: 12px 14px;
          border: 0;
          background: transparent;
          color: #e9eef0;
          border-radius: 8px;
          font-size: 15px;
          font-weight: 600;
          text-align: left;
          cursor: pointer;
          transition: background 0.1s;
        }
        :global(.mylistings-menu a:hover),
        :global(.mylistings-menu button:hover) {
          background: rgba(212, 160, 23, 0.15);
          color: #f0c14b;
        }
        :global(.mylistings-menu .ico) {
          width: 20px;
          text-align: center;
          font-size: 16px;
        }
        :global(.mylistings-menu .danger) {
          color: #f87171;
        }
        :global(.mylistings-menu .danger:hover) {
          background: rgba(248, 113, 113, 0.12);
          color: #fca5a5;
        }

        .market-account button {
          padding: 0;
          border: 0;
          background: transparent;
          color: #5e6c70;
          cursor: pointer;
          text-decoration: underline;
          text-underline-offset: 3px;
        }

        .top-nav {
          display: flex;
          gap: 18px;
          flex-wrap: wrap;
          padding: 10px 0 18px;
          border-bottom: 1px solid rgba(31, 42, 45, 0.12);
        }

        .top-nav a {
          color: #213136;
          font-size: 15px;
        }

        .search-panel {
          padding: 16px 0 14px;
          border-bottom: 1px solid rgba(31, 42, 45, 0.12);
        }

        .search-panel-main {
          display: grid;
          gap: 16px;
        }

        .search-panel h2 {
          font-size: clamp(22px, 3vw, 30px);
          line-height: 1.08;
          letter-spacing: -0.03em;
        }

        .search-row {
          display: grid;
          grid-template-columns: minmax(0, 1.4fr) minmax(180px, 0.7fr) 120px;
          gap: 10px;
        }

        .search-row input {
          min-height: 44px;
          padding: 10px 12px;
          border: 1px solid rgba(31, 42, 45, 0.16);
          background: #fbfdfc;
          color: #1f2a2d;
          outline: 0;
        }

        .search-row button {
          min-height: 44px;
          border: 1px solid #4f7d80;
          background: #5f8f92;
          color: #fff;
          cursor: pointer;
          font-weight: 700;
        }

        .categories {
          display: flex;
          gap: 10px 14px;
          flex-wrap: wrap;
          padding-top: 14px;
        }

        .categories button {
          padding: 0;
          border: 0;
          background: transparent;
          color: #617073;
          cursor: pointer;
          font-size: 15px;
        }

        .categories button.active {
          color: #1f2a2d;
          font-weight: 700;
          text-decoration: underline;
          text-underline-offset: 4px;
        }

        .list-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          padding: 14px 0 8px;
        }

        .list-head strong {
          font-size: 18px;
        }

        .list-actions {
          display: flex;
          gap: 16px;
          flex-wrap: wrap;
        }

        .list-actions a {
          color: #2f7278;
          font-size: 14px;
        }

        .listing-list {
          display: flex;
          flex-direction: column;
        }

        .listing-row {
          border-top: 1px solid rgba(31, 42, 45, 0.10);
        }

        .listing-summary {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 100px;
          gap: 18px;
          width: 100%;
          padding: 14px 0;
          border: 0;
          background: transparent;
          text-align: left;
          cursor: pointer;
        }

        .listing-main h3 {
          margin-bottom: 4px;
          font-size: 22px;
          line-height: 1.08;
          letter-spacing: -0.03em;
        }

        .listing-note {
          margin: 0 0 8px;
          color: #5f6d71;
          font-size: 14px;
          line-height: 1.42;
        }

        .listing-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 8px 14px;
          color: #738185;
          font-size: 13px;
        }

        .listing-side {
          display: flex;
          align-items: center;
          justify-content: flex-end;
        }

        .listing-side img {
          width: 84px;
          height: 84px;
          object-fit: cover;
          border-radius: 10px;
          background: #dbe6e4;
        }

        .listing-detail {
          display: grid;
          grid-template-columns: minmax(320px, 520px) minmax(260px, 1fr);
          gap: 22px;
          padding: 6px 0 18px;
        }

        .detail-gallery {
          display: grid;
          gap: 10px;
        }

        .detail-hero {
          width: 100%;
          height: auto;
          aspect-ratio: 16 / 10;
          object-fit: cover;
          border-radius: 14px;
          background: #dce7e5;
        }

        .thumbs {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .thumbs button {
          padding: 0;
          border: 2px solid transparent;
          background: transparent;
          cursor: pointer;
        }

        .thumbs button.active {
          border-color: #5f8f92;
        }

        .thumbs img {
          width: 72px;
          height: 72px;
          object-fit: cover;
          border-radius: 10px;
          background: #dce7e5;
        }

        .detail-info {
          padding-top: 2px;
        }

        .detail-info h4 {
          margin-bottom: 14px;
          font-size: 20px;
          letter-spacing: -0.02em;
        }

        .detail-info dl {
          display: grid;
          gap: 10px;
          margin: 0 0 16px;
        }

        .detail-info dl div {
          display: grid;
          grid-template-columns: 140px 1fr;
          gap: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid rgba(31, 42, 45, 0.08);
        }

        .detail-info dt {
          color: #6e7d80;
          font-size: 13px;
        }

        .detail-info dd {
          margin: 0;
          color: #243134;
          font-size: 14px;
          font-weight: 700;
        }

        .detail-info p {
          margin: 0 0 16px;
          color: #5d6b6f;
          font-size: 14px;
          line-height: 1.5;
        }

        .detail-actions {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }

        .detail-actions button, .detail-actions a {
          min-height: 42px;
          padding: 10px 14px;
          border: 1px solid #5f8f92;
          background: #5f8f92;
          color: #fff;
          cursor: pointer;
          font-weight: 700;
        }

        .detail-actions .ghost {
          background: transparent;
          color: #335b61;
        }

        .pagination {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
          padding-top: 22px;
          border-top: 1px solid rgba(31, 42, 45, 0.10);
          margin-top: 8px;
        }

        .pagination button {
          min-height: 40px;
          padding: 8px 12px;
          border: 1px solid rgba(31, 42, 45, 0.14);
          background: #fbfdfc;
          color: #213136;
          cursor: pointer;
        }

        .pagination button:disabled {
          opacity: 0.45;
          cursor: not-allowed;
        }

        .pages {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .pages button.active {
          border-color: #5f8f92;
          background: #5f8f92;
          color: #fff;
        }

        .empty-state {
          padding: 28px 0;
        }

        .empty-state h3 {
          margin-bottom: 6px;
          font-size: 20px;
        }

        .empty-state p {
          margin: 0;
          color: #6a787c;
        }

        @media (max-width: 980px) {
          .listing-detail {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 860px) {
          .market-top,
          .list-head,
          .pagination {
            flex-direction: column;
            align-items: flex-start;
          }

          .search-row {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 640px) {
          .market-page {
            padding: 18px 14px 48px;
          }

          .listing-summary {
            grid-template-columns: 1fr 78px;
            gap: 12px;
          }

          .listing-side img {
            width: 72px;
            height: 72px;
          }

          .listing-main h3 {
            font-size: 19px;
          }

          .detail-info dl div {
            grid-template-columns: 1fr;
            gap: 4px;
          }
        }
      `}</style>
    </main>
  );
}

function MyListingsMenu({ label }: { label: string }) {
  const [open, setOpen] = useState(false);
  const { t } = useT();
  return (
    <div className="mylistings-wrap">
      <button
        type="button"
        className={`mylistings-btn ${open ? "open" : ""}`}
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        {label}
        <span className="mylistings-arrow">▼</span>
      </button>
      {open && (
        <div className="mylistings-menu">
          <Link href="/dashboard/listings" onClick={() => setOpen(false)}>
            <span className="ico">👁️</span> {t("dashboard.viewAll")}
          </Link>
          <Link href="/dashboard/listings/new" onClick={() => setOpen(false)}>
            <span className="ico">➕</span> {t("dashboard.addNewListing")}
          </Link>
          <Link href="/dashboard/listings?filter=draft" onClick={() => setOpen(false)}>
            <span className="ico">📝</span> {t("dashboard.drafts")}
          </Link>
          <Link href="/dashboard/listings?filter=published" onClick={() => setOpen(false)}>
            <span className="ico">✅</span> {t("dashboard.publishedOnly")}
          </Link>
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              alert("Štatistiky (views, unikátni diváci, dopyty) – čoskoro v detaile ponuky.");
            }}
          >
            <span className="ico">📊</span> {t("dashboard.stats")}
          </button>
        </div>
      )}
    </div>
  );
}
