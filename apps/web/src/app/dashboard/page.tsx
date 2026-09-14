"use client";

import { useMemo, useState } from "react";

type Listing = {
  id: number;
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

const listings: Listing[] = [
  {
    id: 1,
    title: "Piliny z drevovýroby",
    company: "Drevo SN, s.r.o.",
    location: "Snina",
    category: "Drevo",
    quantity: "120 kg / týždeň",
    published: "Dnes",
    note: "Pravidelný odber, vhodné na ďalšie spracovanie.",
    transport: "Big bag / dodávka",
    images: [
      "https://picsum.photos/seed/piliny-1/300/300",
      "https://picsum.photos/seed/piliny-2/300/300",
      "https://picsum.photos/seed/piliny-3/300/300",
    ],
  },
  {
    id: 2,
    title: "Kovový odpad z výroby",
    company: "KOVO Prešov, s.r.o.",
    location: "Prešov",
    category: "Kov",
    quantity: "850 kg",
    published: "Dnes",
    note: "Dostupné ihneď, opakovaný výskyt každý mesiac.",
    transport: "Paleta / nákladné vozidlo",
    images: [
      "https://picsum.photos/seed/kov-1/300/300",
      "https://picsum.photos/seed/kov-2/300/300",
      "https://picsum.photos/seed/kov-3/300/300",
    ],
  },
  {
    id: 3,
    title: "Kartónové obaly",
    company: "Východ Packaging",
    location: "Humenné",
    category: "Papier",
    quantity: "300 kg",
    published: "Včera",
    note: "Čistý triedený materiál pripravený na odber.",
    transport: "Dodávka / zberové auto",
    images: [
      "https://picsum.photos/seed/karton-1/300/300",
      "https://picsum.photos/seed/karton-2/300/300",
      "https://picsum.photos/seed/karton-3/300/300",
    ],
  },
  {
    id: 4,
    title: "LDPE fólie",
    company: "Recyklo SK",
    location: "Michalovce",
    category: "Plasty",
    quantity: "450 kg",
    published: "Včera",
    note: "Vhodné na recykláciu alebo ďalšie dotriedenie.",
    transport: "Lisovaný balík / dodávka",
    images: [
      "https://picsum.photos/seed/folie-1/300/300",
      "https://picsum.photos/seed/folie-2/300/300",
      "https://picsum.photos/seed/folie-3/300/300",
    ],
  },
  {
    id: 5,
    title: "Použitá drevená štiepka",
    company: "BioHeat Vranov",
    location: "Vranov nad Topľou",
    category: "Drevo",
    quantity: "1,2 t",
    published: "Pred 2 dňami",
    note: "Väčší objem, dlhodobá spolupráca možná.",
    transport: "Kontajner / sklápacie vozidlo",
    images: [
      "https://picsum.photos/seed/stiepka-1/300/300",
      "https://picsum.photos/seed/stiepka-2/300/300",
      "https://picsum.photos/seed/stiepka-3/300/300",
    ],
  },
  {
    id: 6,
    title: "PET pretlaky a zvyšky",
    company: "Plastmont",
    location: "Košice",
    category: "Plasty",
    quantity: "220 kg",
    published: "Pred 3 dňami",
    note: "Pravidelné zvyšky z výrobných liniek.",
    transport: "Big bag / paleta",
    images: [
      "https://picsum.photos/seed/pet-1/300/300",
      "https://picsum.photos/seed/pet-2/300/300",
      "https://picsum.photos/seed/pet-3/300/300",
    ],
  },
  {
    id: 7,
    title: "Papierové dutinky",
    company: "RollPack",
    location: "Bardejov",
    category: "Papier",
    quantity: "180 kg",
    published: "Pred 4 dňami",
    note: "Zvyšky po výrobe obalového materiálu.",
    transport: "Dodávka",
    images: [
      "https://picsum.photos/seed/dutinky-1/300/300",
      "https://picsum.photos/seed/dutinky-2/300/300",
      "https://picsum.photos/seed/dutinky-3/300/300",
    ],
  },
  {
    id: 8,
    title: "Hliníkové odrezky",
    company: "ALU Tech",
    location: "Poprad",
    category: "Kov",
    quantity: "640 kg",
    published: "Pred 5 dňami",
    note: "Triedené odrezky, pravidelný mesačný objem.",
    transport: "Paleta / nákladné vozidlo",
    images: [
      "https://picsum.photos/seed/alu-1/300/300",
      "https://picsum.photos/seed/alu-2/300/300",
      "https://picsum.photos/seed/alu-3/300/300",
    ],
  },
  {
    id: 9,
    title: "Drevené palety na repas",
    company: "LogiWood",
    location: "Trebišov",
    category: "Drevo",
    quantity: "75 ks",
    published: "Pred 6 dňami",
    note: "Palety vhodné na opravu alebo opätovné použitie.",
    transport: "Kamión / odvoz po dohode",
    images: [
      "https://picsum.photos/seed/palety-1/300/300",
      "https://picsum.photos/seed/palety-2/300/300",
      "https://picsum.photos/seed/palety-3/300/300",
    ],
  },
];

const categories = ["Všetko", "Drevo", "Kov", "Papier", "Plasty", "Bioodpad"];
const topLinks = ["Prehľad", "Ponuky", "Trhovisko", "Zhody", "Firmy", "Dokumenty"];
const PAGE_SIZE = 6;

export default function DashboardPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("Všetko");
  const [location, setLocation] = useState("");
  const [page, setPage] = useState(1);
  const [openId, setOpenId] = useState<number | null>(1);
  const [selectedImage, setSelectedImage] = useState<Record<number, string>>(
    Object.fromEntries(listings.map((item) => [item.id, item.images[0]]))
  );

  const filtered = useMemo(() => {
    return listings.filter((item) => {
      const matchesQuery =
        query.trim() === "" ||
        `${item.title} ${item.company} ${item.location} ${item.category} ${item.note} ${item.transport}`
          .toLowerCase()
          .includes(query.toLowerCase());

      const matchesCategory =
        category === "Všetko" || item.category === category;

      const matchesLocation =
        location.trim() === "" ||
        item.location.toLowerCase().includes(location.toLowerCase());

      return matchesQuery && matchesCategory && matchesLocation;
    });
  }, [query, category, location]);

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
        <div className="market-brand">
          <p className="market-mini">CMEP · Circular Materials Exchange Platform</p>
          <h1>Obehové materiály</h1>
        </div>

        <div className="market-account">
          <span>admin@cmep.dev</span>
          <span>owner</span>
          <button type="button">Odhlásiť</button>
        </div>
      </header>

      <nav className="top-nav" aria-label="Hlavná navigácia">
        {topLinks.map((item) => (
          <a key={item} href="#">
            {item}
          </a>
        ))}
      </nav>

      <section className="search-panel">
        <div className="search-panel-main">
          <div>
            <p className="market-mini">Tržnica</p>
            <h2>Ponuky firiem a obehových materiálov</h2>
          </div>

          <div className="search-row">
            <input
              type="search"
              placeholder="Materiál, firma alebo poznámka"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
            />

            <input
              type="text"
              placeholder="Lokalita"
              value={location}
              onChange={(e) => {
                setLocation(e.target.value);
                setPage(1);
              }}
            />

            <button type="button">Hľadať</button>
          </div>
        </div>

        <div className="categories">
          {categories.map((item) => (
            <button
              key={item}
              type="button"
              className={item === category ? "active" : ""}
              onClick={() => changeCategory(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </section>

      <section className="list-head">
        <div>
          <strong>{filtered.length}</strong> aktívnych ponúk
        </div>

        <div className="list-actions">
          <a href="#">+ Pridať ponuku</a>
          <a href="#">+ Pridať firmu</a>
          <a href="#">+ Pridať dokument</a>
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
                          <img src={image} alt={`${item.title} náhľad`} width="72" height="72" />
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="detail-info">
                    <h4>Detail ponuky</h4>

                    <dl>
                      <div>
                        <dt>Firma</dt>
                        <dd>{item.company}</dd>
                      </div>
                      <div>
                        <dt>Lokalita</dt>
                        <dd>{item.location}</dd>
                      </div>
                      <div>
                        <dt>Kategória</dt>
                        <dd>{item.category}</dd>
                      </div>
                      <div>
                        <dt>Množstvo</dt>
                        <dd>{item.quantity}</dd>
                      </div>
                      <div>
                        <dt>Vhodná preprava</dt>
                        <dd>{item.transport}</dd>
                      </div>
                      <div>
                        <dt>Publikované</dt>
                        <dd>{item.published}</dd>
                      </div>
                    </dl>

                    <p>
                      Táto sekcia je pripravená na budúce doplnenie kontaktov, presných parametrov,
                      dostupnosti, certifikátov a odporúčaných dopravcov.
                    </p>

                    <div className="detail-actions">
                      <button type="button">Kontaktovať firmu</button>
                      <button type="button" className="ghost">Zobraziť dopravu</button>
                    </div>
                  </div>
                </div>
              )}
            </article>
          );
        })}

        {currentPageItems.length === 0 && (
          <div className="empty-state">
            <h3>Nenašli sa žiadne ponuky</h3>
            <p>Skús zmeniť hľadaný výraz, kategóriu alebo lokalitu.</p>
          </div>
        )}
      </section>

      <nav className="pagination" aria-label="Stránkovanie">
        <button type="button" onClick={() => changePage(page - 1)} disabled={page === 1}>
          Predchádzajúca
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
          Ďalšia
        </button>
      </nav>

      <style jsx>{`
        :global(*) {
          box-sizing: border-box;
        }

        :global(body) {
          margin: 0;
          background: #eef3f1;
          color: #1f2a2d;
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

        .detail-actions button {
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
