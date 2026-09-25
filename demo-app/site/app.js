// Gen-e2 Demo Shop - a small, deterministic app with KNOWN ground truth, used to test the harness
// itself (evals/) and as an offline demo target. Behaviour switches come from /config.js, which
// serve.py maps to variants/<v1|v2>/config.js - v1 is the "legacy" oracle, v2 the "replacement"
// with planted regressions. See ../GROUND_TRUTH.md for every planted defect and ../SPEC.md for the
// rules (REQ-*). All state lives in localStorage, so a fresh browser context is a fresh shop.
(function () {
  const CFG = window.GENE2_DEMO || {};
  const USERS = { standard_user: "demo_pass", locked_user: "demo_pass", admin_user: "demo_pass" };
  const ADMIN = "admin_user";
  const SAVED_ADDRESS = { standard_user: "12 Harbour Road, #04-11", admin_user: "1 Depot Lane" };
  // p1-p6 are the Featured products (catalog.html): ids, names and prices never change.
  const PRODUCTS = [
    { id: "p1", name: "Canvas Tote", price: 18.0, category: "Outdoor", stock: 40, desc: "Heavy cotton canvas tote with an inside pocket. Carries a week of groceries." },
    { id: "p2", name: "Desk Lamp", price: 42.5, category: "Home", stock: 25, desc: "Adjustable arm, warm LED, three brightness levels." },
    { id: "p3", name: "Espresso Cups", price: 9.99, category: "Kitchen", stock: 60, desc: "Set of two stoneware cups, 90 ml each." },
    { id: "p4", name: "Field Notebook", price: 7.5, category: "Outdoor", stock: 80, desc: "Pocket notebook with a water-resistant cover, 48 dotted pages." },
    { id: "p5", name: "Wool Throw", price: 120.0, category: "Home", stock: 12, desc: "Merino wool throw, 130 x 170 cm, woven in Portugal." },
    { id: "p6", name: "Ceramic Planter", price: 24.0, category: "Home", stock: 30, desc: "Matte glazed planter with a drainage hole and saucer." },
    { id: "p7", name: "Cast Iron Skillet", price: 34.0, category: "Kitchen", stock: 15, desc: "Pre-seasoned 26 cm skillet for stovetop and oven." },
    { id: "p8", name: "Chef's Knife", price: 58.0, category: "Kitchen", stock: 9, desc: "20 cm stainless steel blade with a full tang." },
    { id: "p9", name: "Cutting Board", price: 22.5, category: "Kitchen", stock: 18, desc: "End-grain acacia board with a juice groove." },
    { id: "p10", name: "Salad Bowl", price: 16.0, category: "Kitchen", stock: 22, desc: "Large bamboo bowl with matching servers." },
    { id: "p11", name: "Tea Kettle", price: 39.9, category: "Kitchen", stock: 7, desc: "1.7 litre enamel kettle, works on induction." },
    { id: "p12", name: "Linen Apron", price: 14.5, category: "Kitchen", stock: 2, desc: "Washed linen apron with adjustable straps." },
    { id: "p13", name: "Olive Oil Cruet", price: 11.25, category: "Kitchen", stock: 14, desc: "500 ml glass cruet with a drip-free spout." },
    { id: "p14", name: "Spice Rack", price: 27.0, category: "Kitchen", stock: 0, desc: "Wall-mounted rack with twelve glass jars." },
    { id: "p15", name: "Scented Candle", price: 12.0, category: "Home", stock: 3, desc: "Soy wax candle, cedar and fig, about 40 hours." },
    { id: "p16", name: "Wall Clock", price: 45.0, category: "Home", stock: 0, desc: "Silent sweep movement, 30 cm oak frame." },
    { id: "p17", name: "Picnic Blanket", price: 36.0, category: "Outdoor", stock: 11, desc: "Waterproof backing, folds into a carry strap." },
    { id: "p18", name: "Hiking Flask", price: 21.0, category: "Outdoor", stock: 20, desc: "Insulated 750 ml flask, keeps drinks cold for 24 hours." },
  ];
  const FEATURED = ["p1", "p2", "p3", "p4", "p5", "p6"];
  const SEED_REVIEWS = {
    p2: [{ user: "Mira", rating: 5, text: "Bright enough for late work and the arm stays where you put it." },
         { user: "Joel", rating: 4, text: "Good lamp. The switch is a little stiff at first." }],
    p3: [{ user: "Priya", rating: 3, text: "Nice glaze, but smaller than they look in the photo." }],
    p5: [{ user: "Tom", rating: 5, text: "Very warm and does not shed. Worth the price." },
         { user: "Aisha", rating: 5, text: "Lovely colour, washed well on the wool cycle." },
         { user: "Ken", rating: 4, text: "Soft and heavy, a bit shorter than I expected." }],
  };
  const PROMOS = { SAVE10: "percent", WELCOME5: "fixed", FREESHIP: "shipping" };
  const PAGE_SIZE = 8;
  const TAX_RATE = CFG.taxRate ?? 0.08;
  const FREE_SHIPPING_OVER = 7500; // cents, measured after discounts
  const SHIPPING = 650;
  const REGIONAL_SURCHARGE = 500;
  const REMOTE_SHIPPING = 1400;
  const WELCOME5_MIN = 3000;

  const $ = (sel) => document.querySelector(sel);
  const read = (k, d) => JSON.parse(localStorage.getItem(k) || JSON.stringify(d));
  const write = (k, v) => localStorage.setItem(k, JSON.stringify(v));
  const store = {
    get user() { return localStorage.getItem("demo_user"); },
    set user(v) { v ? localStorage.setItem("demo_user", v) : localStorage.removeItem("demo_user"); },
    get cart() { return read("demo_cart", []).map((x) => (typeof x === "string" ? { id: x, qty: 1 } : x)); },
    set cart(v) { write("demo_cart", v); },
    get orders() { return read("demo_orders", []); },
    set orders(v) { write("demo_orders", v); },
    get promos() { return read("demo_promos", []); },
    set promos(v) { write("demo_promos", v); },
    get reviews() { return read("demo_reviews", {}); },
    set reviews(v) { write("demo_reviews", v); },
    // Admin overrides (REQ-ADMIN-01/02) survive logout within one browser context.
    get stock() { return read("demo_stock", {}); },
    set stock(v) { write("demo_stock", v); },
    get promoOff() { return read("demo_promo_off", []); },
    set promoOff(v) { write("demo_promo_off", v); },
  };
  const money = (n) => `$${n.toFixed(2)}`;
  const cents = (c) => money(c / 100);
  const product = (id) => PRODUCTS.find((p) => p.id === id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function requireLogin() {
    if (!store.user) { location.href = "index.html?error=login-required"; return false; }
    return true;
  }

  // ------------------------------------------------------------------ stock and cart
  function stockOf(p) { const o = store.stock; return p.id in o ? o[p.id] : p.stock; }
  function stockLabel(n) { return n === 0 ? "Out of stock" : n <= 3 ? `Only ${n} left` : "In stock"; }
  // DB-10 (v2): the out-of-stock check is skipped, so a product with 0 stock can be added.
  function canAdd(p) { return CFG.allowOutOfStockAdd || stockOf(p) > 0; }
  const cartCount = () => store.cart.reduce((s, l) => s + l.qty, 0);

  function addToCart(id, qty) {
    const lines = store.cart;
    const line = lines.find((l) => l.id === id);
    if (line) line.qty = Math.min(5, line.qty + qty); else lines.push({ id, qty: Math.min(5, qty) });
    store.cart = lines;
  }

  function renderBadge() {
    const badge = $("[data-test='cart-badge']");
    if (!badge) return;
    // DB-02 (v2): the badge is only ever updated upward, so removing an item leaves it stale.
    const count = cartCount();
    if (CFG.badgeNeverDecrements) {
      const shown = Number(badge.dataset.max || 0);
      const next = Math.max(shown, count);
      badge.dataset.max = String(next);
      badge.textContent = next ? String(next) : "";
    } else {
      badge.textContent = count ? String(count) : "";
    }
    badge.hidden = !badge.textContent;
  }

  function nav() {
    const out = $("[data-test='logout']");
    if (out) out.addEventListener("click", () => { store.user = null; store.cart = []; store.promos = []; location.href = "index.html"; });
    const admin = $("[data-test='nav-admin']");
    if (admin) admin.hidden = store.user !== ADMIN;
    renderBadge();
  }

  function login() {
    const params = new URLSearchParams(location.search);
    const err = $("[data-test='error']");
    if (params.get("error") === "login-required") {
      err.textContent = "You must log in to view that page.";
      err.hidden = false;
    }
    $("[data-test='login-form']").addEventListener("submit", (e) => {
      e.preventDefault();
      const u = $("[data-test='username']").value.trim();
      const p = $("[data-test='password']").value;
      if (!u || !p) { err.textContent = "Username and password are required."; err.hidden = false; return; }
      if (u === "locked_user" && p === USERS[u]) { err.textContent = "This account is locked. Contact support."; err.hidden = false; return; }
      if (USERS[u] !== p) { err.textContent = "Username and password do not match."; err.hidden = false; return; }
      store.user = u;
      location.href = "catalog.html";
    });
  }

  // ------------------------------------------------------------------ catalogue
  function sortProducts(list, mode) {
    const copy = [...list];
    if (mode === "name-asc") copy.sort((a, b) => a.name.localeCompare(b.name));
    if (mode === "name-desc") copy.sort((a, b) => b.name.localeCompare(a.name));
    // DB-01 (v2): price sorts as TEXT, so "$120.00" lands before "$18.00".
    const key = (p) => (CFG.priceSortAsText ? money(p.price) : p.price);
    if (mode === "price-asc") copy.sort((a, b) => (key(a) > key(b) ? 1 : key(a) < key(b) ? -1 : 0));
    if (mode === "price-desc") copy.sort((a, b) => (key(a) < key(b) ? 1 : key(a) > key(b) ? -1 : 0));
    return copy;
  }

  // REQ-SEARCH-01: case-insensitive substring match on the name.
  // DB-07 (v2): the match is case-sensitive, so "lamp" does not find "Desk Lamp".
  function matchesSearch(p, q) {
    if (!q) return true;
    return CFG.caseSensitiveSearch ? p.name.includes(q) : p.name.toLowerCase().includes(q.toLowerCase());
  }

  function productCard(p, onChange) {
    const inCart = store.cart.some((l) => l.id === p.id);
    const card = document.createElement("div");
    card.className = "card";
    card.dataset.test = "product";
    card.innerHTML = `<h3><a href="product.html?id=${p.id}" data-test="product-link-${p.id}"><span data-test="product-name">${p.name}</span></a></h3>
      <p data-test="product-price">${money(p.price)}</p>
      <p class="stock" data-test="product-stock">${stockLabel(stockOf(p))}</p>`;
    const btn = document.createElement("button");
    btn.dataset.test = `${inCart ? "remove" : "add"}-${p.id}`;
    btn.textContent = inCart ? "Remove" : canAdd(p) ? "Add to cart" : "Out of stock";
    btn.disabled = !inCart && !canAdd(p);
    btn.addEventListener("click", () => {
      store.cart = inCart ? store.cart.filter((l) => l.id !== p.id) : [...store.cart, { id: p.id, qty: 1 }];
      onChange();
      renderBadge();
    });
    card.appendChild(btn);
    return card;
  }

  function catalog() {
    if (!requireLogin()) return;
    nav();
    const grid = $("[data-test='product-list']");
    const featured = PRODUCTS.filter((p) => FEATURED.includes(p.id));
    const draw = () => {
      const mode = $("[data-test='sort']").value;
      const q = $("[data-test='search']").value.trim();
      const items = sortProducts(featured, mode).filter((p) => matchesSearch(p, q));
      grid.innerHTML = "";
      for (const p of items) grid.appendChild(productCard(p, draw));
      $("[data-test='empty-results']").hidden = items.length > 0;
    };
    $("[data-test='sort']").addEventListener("change", draw);
    $("[data-test='search']").addEventListener("input", draw);
    // A deliberately flaky promo: the server alternates it on every request (/promo.json).
    fetch("promo.json").then((r) => r.json()).then((d) => { $("[data-test='promo']").hidden = !d.show; }).catch(() => {});
    draw();
  }

  function products() {
    if (!requireLogin()) return;
    nav();
    const grid = $("[data-test='product-list']");
    let page = 1;
    const draw = () => {
      const mode = $("[data-test='sort']").value;
      const q = $("[data-test='search-input']").value.trim();
      const cat = $("[data-test='filter-category']").value;
      const inStockOnly = $("[data-test='filter-in-stock']").checked;
      // REQ-SEARCH-02: search, category and in-stock filters combine with AND.
      const matches = sortProducts(PRODUCTS, mode)
        .filter((p) => matchesSearch(p, q))
        .filter((p) => !cat || p.category === cat)
        .filter((p) => !inStockOnly || stockOf(p) > 0);
      // REQ-SEARCH-03: 8 per page, ceil(matches / 8) pages, every match exactly once.
      const pages = Math.ceil(matches.length / PAGE_SIZE);
      page = Math.min(Math.max(1, page), Math.max(1, pages));
      let start = (page - 1) * PAGE_SIZE;
      // DB-08 (v2): off by one - every page after the first starts one product early,
      // so page 2 repeats the last product of page 1.
      if (CFG.pagerRepeatsLast && page > 1) start -= 1;
      grid.innerHTML = "";
      for (const p of matches.slice(start, start + PAGE_SIZE)) grid.appendChild(productCard(p, draw));
      $("[data-test='empty-results']").hidden = matches.length > 0;
      $("[data-test='pager']").hidden = matches.length === 0;
      $("[data-test='page-indicator']").textContent = `Page ${page} of ${pages}`;
      $("[data-test='page-prev']").hidden = page <= 1;
      $("[data-test='page-next']").hidden = page >= pages;
    };
    const reset = () => { page = 1; draw(); };
    $("[data-test='sort']").addEventListener("change", reset);
    $("[data-test='search-input']").addEventListener("input", reset);
    $("[data-test='filter-category']").addEventListener("change", reset);
    $("[data-test='filter-in-stock']").addEventListener("change", reset);
    $("[data-test='page-next']").addEventListener("click", () => { page += 1; draw(); });
    $("[data-test='page-prev']").addEventListener("click", () => { page -= 1; draw(); });
    draw();
  }

  // ------------------------------------------------------------------ product detail and reviews
  function reviewsFor(pid) { return [...(SEED_REVIEWS[pid] || []), ...(store.reviews[pid] || [])]; }

  function productDetail() {
    if (!requireLogin()) return;
    nav();
    const p = product(new URLSearchParams(location.search).get("id"));
    if (!p) { $("[data-test='pdp-missing']").hidden = false; $("[data-test='pdp']").hidden = true; return; }
    document.title = `Gen-e2 Demo Shop - ${p.name}`;
    $("[data-test='pdp-name']").textContent = p.name;
    $("[data-test='pdp-price']").textContent = money(p.price);
    $("[data-test='pdp-category']").textContent = p.category;
    $("[data-test='pdp-description']").textContent = p.desc;
    $("[data-test='pdp-stock']").textContent = stockLabel(stockOf(p));
    const add = $("[data-test='add-to-cart']");
    add.disabled = !canAdd(p);
    add.textContent = canAdd(p) ? "Add to cart" : "Out of stock";
    add.addEventListener("click", () => {
      addToCart(p.id, Number($("[data-test='qty']").value));
      renderBadge();
      $("[data-test='added']").hidden = false;
    });

    const drawReviews = () => {
      const list = reviewsFor(p.id);
      // REQ-PDP-01: mean of the ratings, one decimal; "No reviews yet" when there are none.
      const rating = $("[data-test='pdp-rating']");
      if (!list.length) rating.textContent = "No reviews yet";
      else {
        const avg = list.reduce((s, r) => s + r.rating, 0) / list.length;
        rating.textContent = `${avg.toFixed(1)} out of 5 (${list.length} ${list.length === 1 ? "review" : "reviews"})`;
      }
      const ul = $("[data-test='review-list']");
      ul.innerHTML = "";
      for (const r of list) {
        const li = document.createElement("li");
        li.className = "review";
        li.dataset.test = "review-item";
        li.innerHTML = `<b data-test="review-stars">${r.rating}/5</b> <span data-test="review-body">${esc(r.text)}</span> <span class="who">by ${esc(r.user)}</span>`;
        ul.appendChild(li);
      }
    };
    const err = $("[data-test='review-error']");
    $("[data-test='review-form']").addEventListener("submit", (e) => {
      e.preventDefault();
      const rating = Number($("[data-test='review-rating']").value);
      const text = $("[data-test='review-text']").value.trim();
      const all = store.reviews;
      const mine = all[p.id] || [];
      // REQ-REVIEW-02: one review per customer per product. REQ-REVIEW-01: 1-5 stars, 10-500 chars.
      let msg = "";
      if (mine.some((r) => r.user === store.user)) msg = "You have already reviewed this product.";
      else if (!(rating >= 1 && rating <= 5)) msg = "Choose a rating from 1 to 5 stars.";
      else if (text.length < 10 || text.length > 500) msg = "Review text must be 10 to 500 characters.";
      if (msg) { err.textContent = msg; err.hidden = false; return; }
      err.hidden = true;
      all[p.id] = [...mine, { user: store.user, rating, text }];
      store.reviews = all;
      $("[data-test='review-form']").reset();
      drawReviews();
    });
    drawReviews();
  }

  // ------------------------------------------------------------------ cart
  function cart() {
    if (!requireLogin()) return;
    nav();
    const list = $("[data-test='cart-list']");
    const draw = () => {
      list.innerHTML = "";
      for (const line of store.cart) {
        const p = product(line.id);
        const row = document.createElement("li");
        row.dataset.test = "cart-item";
        const opts = [1, 2, 3, 4, 5].map((q) => `<option value="${q}"${q === line.qty ? " selected" : ""}>${q}</option>`).join("");
        row.innerHTML = `<span data-test="cart-item-name">${p.name}</span> <span>${money(p.price)}</span>
          <label class="inline">Qty <select data-test="cart-qty-${p.id}">${opts}</select></label>
          <span data-test="cart-line-total">${money(p.price * line.qty)}</span>
          <button data-test="cart-remove-${p.id}">Remove</button>`;
        // REQ-CART-02: quantity per line is 1-5; a line can be changed or removed.
        row.querySelector("select").addEventListener("change", (e) => {
          store.cart = store.cart.map((l) => (l.id === line.id ? { ...l, qty: Number(e.target.value) } : l));
          draw();
          renderBadge();
        });
        row.querySelector("button").addEventListener("click", () => {
          store.cart = store.cart.filter((l) => l.id !== line.id);
          draw();
          renderBadge();
        });
        list.appendChild(row);
      }
      $("[data-test='cart-empty']").hidden = store.cart.length > 0;
      $("[data-test='checkout']").disabled = store.cart.length === 0;
    };
    $("[data-test='checkout']").addEventListener("click", () => { location.href = "checkout.html"; });
    draw();
  }

  // ------------------------------------------------------------------ promotions, tax, shipping
  const activeCodes = () => store.promos.filter((c) => PROMOS[c] && !store.promoOff.includes(c));

  function discountFor(sub, codes) {
    const pct = codes.includes("SAVE10") ? Math.round(sub * 0.1) : 0;
    if (CFG.stackDiscounts) {
      // DB-06 (v2): the STRUCK rule - two discount codes stack, WELCOME5 after the percentage.
      const w5 = codes.includes("WELCOME5") && sub - pct >= WELCOME5_MIN ? 500 : 0;
      return pct + w5;
    }
    // REQ-PROMO-02: one discount code per order (enforced when applying). REQ-PROMO-03: $30 minimum.
    if (pct) return pct;
    return codes.includes("WELCOME5") && sub >= WELCOME5_MIN ? 500 : 0;
  }

  function totals(region) {
    const sub = store.cart.reduce((s, l) => s + Math.round(product(l.id).price * 100) * l.qty, 0);
    const codes = activeCodes();
    const discount = discountFor(sub, codes);
    const after = sub - discount;
    // REQ-TAX / REQ-TAX-02: 8% of the subtotal after discounts, rounded to the cent; no tax on shipping.
    const tax = Math.round(after * TAX_RATE);
    let shipping;
    if (region === "Remote") shipping = REMOTE_SHIPPING; // REQ-SHIP-03: never free
    else {
      // REQ-SHIP / REQ-SHIP-04: free over $75 after discounts, or with FREESHIP.
      const base = after > FREE_SHIPPING_OVER || codes.includes("FREESHIP") ? 0 : SHIPPING;
      // REQ-SHIP-02: Regional adds $5.00 on top of the base fee. DB-09 (v2): surcharge missing.
      const surcharge = region === "Regional" && !CFG.regionalSurchargeMissing ? REGIONAL_SURCHARGE : 0;
      shipping = base + surcharge;
    }
    return { sub, discount, tax, shipping, total: after + tax + shipping, codes };
  }

  function applyCode(raw, region) {
    const code = raw.trim().toUpperCase();
    const applied = store.promos;
    if (!PROMOS[code] || store.promoOff.includes(code)) return "This code is not valid.";
    if (applied.includes(code)) return "This code is already applied.";
    const isDiscount = PROMOS[code] !== "shipping";
    if (isDiscount && !CFG.stackDiscounts && applied.some((c) => PROMOS[c] !== "shipping"))
      return "Only one discount code can be used per order.";
    if (code === "WELCOME5") {
      const t = totals(region);
      const base = CFG.stackDiscounts ? t.sub - t.discount : t.sub;
      if (base < WELCOME5_MIN) return "WELCOME5 needs a subtotal of $30 or more.";
    }
    store.promos = [...applied, code];
    return "";
  }

  function checkout() {
    if (!requireLogin()) return;
    nav();
    const region = $("[data-test='region']");
    // REQ-ADDR-01: the address line is required; it starts filled from the account's saved address.
    $("[data-test='address']").value = SAVED_ADDRESS[store.user] || "";
    const draw = () => {
      const t = totals(region.value);
      $("[data-test='subtotal']").textContent = cents(t.sub);
      $("[data-test='discount']").textContent = t.discount ? `-${cents(t.discount)}` : "$0.00";
      $("[data-test='tax']").textContent = cents(t.tax);
      $("[data-test='shipping']").textContent = t.shipping ? cents(t.shipping) : "Free";
      $("[data-test='total']").textContent = cents(t.total);
      const applied = $("[data-test='promo-applied']");
      applied.textContent = t.codes.join(", ");
      applied.hidden = !t.codes.length;
      return t;
    };
    region.addEventListener("change", draw);
    const promoErr = $("[data-test='promo-error']");
    $("[data-test='promo-apply']").addEventListener("click", () => {
      const msg = applyCode($("[data-test='promo-input']").value, region.value);
      promoErr.textContent = msg;
      promoErr.hidden = !msg;
      if (!msg) $("[data-test='promo-input']").value = "";
      draw();
    });
    const err = $("[data-test='checkout-error']");
    $("[data-test='checkout-form']").addEventListener("submit", (e) => {
      e.preventDefault();
      const name = $("[data-test='full-name']").value.trim();
      const postcode = $("[data-test='postcode']").value.trim();
      const address = $("[data-test='address']").value.trim();
      if (!name) { err.textContent = "Full name is required."; err.hidden = false; return; }
      if (name.length < 2 || name.length > 60) { err.textContent = "Full name must be 2 to 60 characters."; err.hidden = false; return; }
      // DB-04 (v1 AND v2): the requirement says the postcode is required; neither build checks it.
      if (CFG.validatePostcode && !/^\d{6}$/.test(postcode)) { err.textContent = "A 6-digit postcode is required."; err.hidden = false; return; }
      if (!address) { err.textContent = "Address is required."; err.hidden = false; return; }
      const t = draw();
      // DB-05 (v1 AND v2): no in-flight guard - a double click records two orders.
      setTimeout(() => {
        const orders = store.orders;
        orders.push({
          no: `SO-${1001 + orders.length}`, at: new Date().toLocaleDateString("en-CA"), user: store.user,
          items: store.cart.reduce((s, l) => s + l.qty, 0), total: t.total, region: region.value, status: "Placed",
        });
        store.orders = orders;
        store.cart = [];
        store.promos = [];
        location.href = "confirmation.html";
      }, 150);
    });
    draw();
  }

  function myOrders() { return store.orders.filter((o) => o.user === store.user); }

  function confirmation() {
    if (!requireLogin()) return;
    nav();
    const mine = myOrders();
    $("[data-test='order-count']").textContent = String(mine.length);
    if (mine.length) $("[data-test='order-number']").textContent = mine[mine.length - 1].no;
  }

  // ------------------------------------------------------------------ orders and admin
  function orders() {
    if (!requireLogin()) return;
    nav();
    const body = $("[data-test='order-list']");
    // REQ-ORDER-02: the customer's own orders, newest first.
    const mine = myOrders().slice().reverse();
    for (const o of mine) {
      const tr = document.createElement("tr");
      tr.dataset.test = "order-row";
      tr.innerHTML = `<td data-test="order-no">${o.no}</td><td data-test="order-date">${o.at}</td><td data-test="order-items">${o.items}</td>
        <td data-test="order-total">${cents(o.total)}</td><td data-test="order-status">${o.status}</td>`;
      body.appendChild(tr);
    }
    $("[data-test='orders-empty']").hidden = mine.length > 0;
    $("[data-test='orders-table']").hidden = mine.length === 0;
  }

  function admin() {
    if (!requireLogin()) return;
    nav();
    // REQ-AUTH-02: only admin_user sees the controls.
    if (store.user !== ADMIN) { $("[data-test='admin-denied']").hidden = false; return; }
    $("[data-test='admin-panel']").hidden = false;
    const saved = $("[data-test='admin-saved']");
    const err = $("[data-test='admin-error']");
    const body = $("[data-test='admin-stock-list']");
    for (const p of PRODUCTS) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${p.name}</td><td><input type="number" min="0" max="99" step="1" value="${stockOf(p)}"
        data-test="admin-stock-${p.id}" aria-label="Stock for ${p.name}"></td>`;
      const input = tr.querySelector("input");
      // REQ-ADMIN-01: stock 0-99; the catalogue reflects it at once.
      input.addEventListener("change", () => {
        const n = Number(input.value);
        if (input.value.trim() === "" || !Number.isInteger(n) || n < 0 || n > 99) {
          err.textContent = "Stock must be a whole number from 0 to 99."; err.hidden = false; saved.hidden = true;
          input.value = stockOf(p);
          return;
        }
        store.stock = { ...store.stock, [p.id]: n };
        err.hidden = true; saved.hidden = false;
      });
      body.appendChild(tr);
    }
    // REQ-ADMIN-02: a disabled code behaves as unknown.
    for (const code of Object.keys(PROMOS)) {
      const box = $(`[data-test='admin-promo-${code}']`);
      box.checked = !store.promoOff.includes(code);
      box.addEventListener("change", () => {
        const off = store.promoOff.filter((c) => c !== code);
        store.promoOff = box.checked ? off : [...off, code];
        err.hidden = true; saved.hidden = false;
      });
    }
  }

  window.GENE2_PAGES = { login, catalog, products, product: productDetail, cart, checkout, confirmation, orders, admin };
})();
