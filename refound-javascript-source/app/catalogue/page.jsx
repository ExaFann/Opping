"use client";
import { useMemo, useState } from "react";
import { Footer, ProductCard } from "../page";
import { categories, products } from "../products";

export default function Catalogue() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All finds");
  const filtered = useMemo(() => products.filter(p => (category === "All finds" || p.category === category) && `${p.name} ${p.category} ${p.shop} ${p.colour}`.toLowerCase().includes(query.toLowerCase())), [query, category]);
  return <main>
    <header className="site-header inner-header"><a className="brand" href="/"><span className="brand-mark">R</span> ReFound</a><nav><a href="/about">What we do</a><a className="active" href="/catalogue">Catalogue</a><a href="/#shops">Op shops</a></nav><a className="nav-cta" href="#catalogue-grid">Browse finds</a></header>
    <section className="catalogue-hero"><p className="eyebrow"><span>●</span> In store now, around Auckland</p><h1>Good things,<br/><em>found again.</em></h1><p>One-of-a-kind pieces from local op shops, ready for their next chapter.</p><div className="catalogue-search"><input aria-label="Search catalogue" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search coats, chairs, lamps…"/><span>⌕</span></div></section>
    <div className="filters" aria-label="Catalogue filters"><button className={category === "All finds" ? "selected" : ""} onClick={() => setCategory("All finds")}>All finds</button>{categories.map(c => <button className={category === c.name ? "selected" : ""} onClick={() => setCategory(c.name)} key={c.name}>{c.name}</button>)}</div>
    <section className="catalogue-content section" id="catalogue-grid"><div className="results-title"><p><strong>{filtered.length}</strong> good finds</p><select aria-label="Sort products"><option>Newest first</option><option>Price: low to high</option><option>Price: high to low</option></select></div>{filtered.length ? <div className="product-grid">{filtered.map(p => <ProductCard key={p.id} product={p}/>)}</div> : <div className="empty"><h2>No exact matches yet</h2><p>Try a broader search or another shelf—new finds arrive every day.</p><button onClick={() => {setQuery(""); setCategory("All finds")}}>Show all finds</button></div>}</section>
    <section className="catalogue-note"><div><span>↻</span><h2>Fresh finds, every day.</h2></div><p>Op shop stock changes quickly. We update the catalogue as new pieces reach the floor, so there is always something new to discover.</p></section>
    <Footer />
  </main>
}
