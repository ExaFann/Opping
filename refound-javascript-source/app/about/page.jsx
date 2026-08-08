import { Footer } from "../page";

export default function About() {
  return <main>
    <header className="site-header inner-header"><a className="brand" href="/"><span className="brand-mark">R</span> ReFound</a><nav><a className="active" href="/about">What we do</a><a href="/catalogue">Catalogue</a><a href="/#shops">Op shops</a></nav><a className="nav-cta" href="/catalogue">Find a treasure</a></header>
    <section className="about-hero"><p className="eyebrow"><span>●</span> Our reason for being</p><h1>Op shopping shouldn’t<br/>feel like a <em>treasure hunt.</em></h1><p>We bring local second-hand stock together online, making it simple to find what you need for a fraction of its original price.</p></section>
    <section className="about-image"><img src="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=1800&q=85" alt="A bright, carefully arranged second-hand store"/><div><strong>Good for your wallet.</strong><strong>Good for local causes.</strong><strong>Good for the planet.</strong></div></section>
    <section className="mission section"><div><p className="eyebrow">Convenience with a conscience</p><h2>Everything worth finding.<br/>Without visiting every shop.</h2></div><div><p>Great second-hand items are already sitting on shelves across our cities. The problem is knowing where to look. ReFound shows current in-store availability from op shops in one simple catalogue.</p><p>That means fewer wasted trips, more affordable choices, and less perfectly useful stuff heading to landfill. You can compare, reserve, and collect locally—while supporting the community organisations behind each shop.</p></div></section>
    <section className="values section"><article><span>01</span><h3>Save money</h3><p>Get quality clothing, furniture and homeware at a fraction of the price of buying new.</p></article><article><span>02</span><h3>Save the runaround</h3><p>Check stock across the city from your sofa, then make one trip to the right shop.</p></article><article><span>03</span><h3>Save good things</h3><p>Every second-hand purchase extends an item’s life and reduces demand for new resources.</p></article></section>
    <section className="closing about-closing"><p className="eyebrow">Your next find is already out there</p><h2>Start with what’s<br/><em>already here.</em></h2><a href="/catalogue">Explore the catalogue <span>→</span></a></section>
    <Footer />
  </main>
}
