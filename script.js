const products = [
  ["Chocolate leather loafers","Shoes","EU 39",22,"Paper Bag Princess","https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=800&q=80"],
  ["Burnt orange linen shirt","Shirts","M",18,"Recycle Boutique","https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=800&q=80"],
  ["Speckled ceramic jug","Homeware","1.2L",14,"SPCA Op Shop","https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=800&q=80"],
  ["Mid-century bedside table","Furniture","Small",45,"Hospice West Auckland","https://images.unsplash.com/photo-1532372320572-cda25653a694?auto=format&fit=crop&w=800&q=80"],
  ["Forest wool coat","Outerwear","L",34,"Tatty’s Ponsonby","https://images.unsplash.com/photo-1539533018447-63fcce2678e3?auto=format&fit=crop&w=800&q=80"],
  ["Woven weekend tote","Bags","Large",16,"Red Cross Kingsland","https://images.unsplash.com/photo-1594223274512-ad4803739b7c?auto=format&fit=crop&w=800&q=80"],
  ["Vintage glass table lamp","Homeware","Medium",28,"Salvation Army","https://images.unsplash.com/photo-1540932239986-30128078f3c5?auto=format&fit=crop&w=800&q=80"],
  ["Straight-leg blue jeans","Clothing","10",20,"SaveMart K Road","https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=800&q=80"],
  ["Suede ankle boots","Shoes","EU 38",26,"St Vincent de Paul","https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=800&q=80"],
  ["Striped cotton overshirt","Shirts","L",17,"Grey Lynn Community","https://images.unsplash.com/photo-1603252109303-2751441dd157?auto=format&fit=crop&w=800&q=80"],
  ["Oak spindle chair","Furniture","Standard",39,"Hospice West Auckland","https://images.unsplash.com/photo-1598300053650-0d40971164e7?auto=format&fit=crop&w=800&q=80"],
  ["Stoneware dinner set","Homeware","6 place",32,"SPCA Op Shop","https://images.unsplash.com/photo-1603199506016-b9a594b593c0?auto=format&fit=crop&w=800&q=80"]
];

const shops = [["SPCA Op Shop Mt Eden","Mt Eden",48],["Hospice West Auckland","Henderson",62],["Red Cross Kingsland","Kingsland",37],["Salvation Army Newmarket","Newmarket",55],["Paper Bag Princess","Grey Lynn",71],["St Vincent de Paul","Ponsonby",42]];
const categories = ["All", ...new Set(products.map(product => product[1]))];
let activeCategory = "All";
let query = "";

function renderProducts() {
  const visible = products.filter(product => (activeCategory === "All" || product[1] === activeCategory) && product.join(" ").toLowerCase().includes(query.toLowerCase()));
  document.querySelector("#products").innerHTML = visible.map(product => `<article class="product"><div><img src="${product[5]}" alt="${product[0]}"><button aria-label="Save ${product[0]}">♡</button></div><small>${product[1]} · ${product[2]}</small><h3>${product[0]}</h3><p><strong>$${product[3]}</strong><span>${product[4]}</span></p></article>`).join("");
  document.querySelector("#empty").hidden = visible.length > 0;
}

document.querySelector("#filters").innerHTML = categories.map(category => `<button data-category="${category}">${category}</button>`).join("");
document.querySelector("#filters button").classList.add("active");
document.querySelector("#filters").addEventListener("click", event => { if (!event.target.dataset.category) return; activeCategory = event.target.dataset.category; document.querySelectorAll("#filters button").forEach(button => button.classList.toggle("active", button === event.target)); renderProducts(); });
document.querySelector("#catalogue-search").addEventListener("input", event => { query = event.target.value; renderProducts(); });
document.querySelector("#hero-search").addEventListener("submit", event => { event.preventDefault(); query = document.querySelector("#search-input").value; document.querySelector("#catalogue-search").value = query; renderProducts(); document.querySelector("#catalogue").scrollIntoView({ behavior: "smooth" }); });
document.querySelector("#shop-list").innerHTML = shops.map(shop => `<article><b>${shop[0]}</b><span>${shop[1]} · ${shop[2]} items online</span></article>`).join("");
renderProducts();
