"use client";

import { useMemo, useState } from "react";
import { categories, products, shops } from "./products";

const Arrow = () => <span aria-hidden="true">↗</span>;

export default function Home() {
  const [query, setQuery] = useState("");
  const [searched, setSearched] = useState(false);
  const matches = useMemo(() => {
    const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (!words.length) return products.slice(0, 8);
    const exact = products.filter((p) => words.some((word) => `${p.name} ${p.category} ${p.colour} ${p.shop}`.toLowerCase().includes(word)));
    return exact.length >= 6 ? exact : [...exact, ...products.filter((p) => !exact.includes(p))].slice(0, 8);
  }, [query]);

  function search(e) {
    e.preventDefault();
    setSearched(true);
    requestAnimationFrame(() => document.getElementById("matches")?.scrollIntoView({ behavior: "smooth" }));
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="ReFound home"><span className="brand-mark">R</span> ReFound</a>
        <nav aria-label="Main navigation">
          <a href="/about">What we do</a>
          <a href="/catalogue">Catalogue</a>
          <a href="#shops">Op shops</a>
        </nav>
        <a className="nav-cta" href="#search">Find a treasure</a>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span>●</span> Auckland’s op shops, in one place</p>
          <h1>Find it second hand, <em>first.</em></h1>
          <p className="hero-lede">Search real stock from local op shops before crossing the city. Spend less, save time, and keep good things in use.</p>
          <form className="search-box" id="search" onSubmit={search}>
            <label htmlFor="search-input">What are you looking for?</label>
            <div className="search-row">
              <input id="search-input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Try ‘brown boots’ or ‘vintage lamp’" />
              <button type="submit">Search nearby <span>→</span></button>
            </div>
            <div className="quick-searches"><span>Popular:</span>{["Winter coats", "Dining chairs", "Kids’ books"].map((x) => <button type="button" key={x} onClick={() => {setQuery(x); setSearched(true);}}>{x}</button>)}</div>
          </form>
          <a className="text-link" href="/about">See what ReFound does <Arrow /></a>
        </div>
        <div className="hero-image" aria-label="A curated collection of colourful second-hand finds">
          <img src="https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=1200&q=85" alt="Colourful vintage clothing on a rack" />
          <div className="floating-card"><span>Just listed</span><strong>Wool overcoat</strong><small>$24 · Grey Lynn</small></div>
          <div className="roundel">GOOD<br/>FINDS<br/><b>↘</b></div>
        </div>
      </section>

      <section className="proof-strip" aria-label="ReFound impact">
        <div><strong>480+</strong><span>local finds today</span></div>
        <div><strong>13</strong><span>partner op shops</span></div>
        <div><strong>Up to 80%</strong><span>less than buying new</span></div>
        <div><strong>One search</strong><span>instead of a city-wide hunt</span></div>
      </section>

      {searched && <section className="search-results section" id="matches">
        <div className="section-heading"><div><p className="eyebrow">Matches picked for you</p><h2>{query ? `Good finds for “${query}”` : "Fresh finds nearby"}</h2></div><a href={`/catalogue?q=${encodeURIComponent(query)}`}>See all results <Arrow /></a></div>
        <div className="product-grid compact">{matches.map((p) => <ProductCard key={p.id} product={p} />)}</div>
      </section>}

      <section className="section catalogue-preview">
        <div className="section-heading"><div><p className="eyebrow">Browse by shelf</p><h2>Explore our catalogue</h2><p>Swipe or scroll to wander through the good stuff.</p></div><a className="pill-link" href="/catalogue">View the full catalogue <span>→</span></a></div>
        <div className="category-rail" aria-label="Product categories">{categories.map((cat) => <a href={`/catalogue?category=${cat.name}`} className="category-card" key={cat.name}><img src={cat.image} alt=""/><span>{cat.name}</span><small>{cat.count} finds</small><b>→</b></a>)}</div>
      </section>

      <section className="how" id="how">
        <div className="how-intro"><p className="eyebrow">Less hunting. More finding.</p><h2>We make second hand the easy first choice.</h2><p>ReFound brings the shelves of local op shops online, so you can check what is available, compare nearby finds, and shop with purpose.</p><a className="light-button" href="/about">Discover our story <Arrow /></a></div>
        <ol className="steps"><li><span>01</span><div><h3>Tell us what you need</h3><p>Search by description, category, price, size, colour, or suburb.</p></div></li><li><span>02</span><div><h3>See what’s actually in store</h3><p>Browse current listings from op shops across Tāmaki Makaurau.</p></div></li><li><span>03</span><div><h3>Reserve it, then pick it up</h3><p>Save the trip, support a local cause, and give a good item another life.</p></div></li></ol>
      </section>

      <section className="section shops" id="shops">
        <div className="section-heading"><div><p className="eyebrow">Our local network</p><h2>Op shops under us</h2><p>One search connects you to trusted second-hand stores across Auckland.</p></div></div>
        <div className="shop-list">{shops.map((shop, i) => <a href={`/catalogue?shop=${encodeURIComponent(shop.name)}`} key={shop.name}><span className={`shop-icon i${i%4}`}>{shop.initials}</span><div><strong>{shop.name}</strong><small>{shop.location} · {shop.items} items online</small></div><b>Browse stock →</b></a>)}</div>
      </section>

      <section className="closing"><p className="eyebrow">A better way to buy</p><h2>Before you buy new,<br/><em>see what’s already here.</em></h2><a href="/catalogue">Explore all finds <span>→</span></a></section>
      <Footer />
    </main>
  );
}

export function ProductCard({ product: p }) {
  return <article className="product-card"><a href={`/catalogue?item=${p.id}`}><div className="product-image"><img src={p.image} alt={p.name}/><span>{p.condition}</span><button type="button" aria-label={`Save ${p.name}`}>♡</button></div><div className="product-info"><p>{p.category} · {p.size}</p><h3>{p.name}</h3><div><strong>${p.price}</strong><span>{p.shop}</span></div></div></a></article>;
}

export function Footer() { return <footer><a className="brand" href="/"><span className="brand-mark">R</span> ReFound</a><p>Good finds. Smaller footprints.<br/>Made in Tāmaki Makaurau.</p><div><a href="/about">What we do</a><a href="/catalogue">Catalogue</a><a href="/#shops">Partner op shops</a></div><small>© 2026 ReFound</small></footer> }
