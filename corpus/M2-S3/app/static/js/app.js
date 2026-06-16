/* ── STATE ── */
let currentUser = null;
let cart = [];
let products = [];
let categories = [];

/* ── UTILS ── */
const $ = id => document.getElementById(id);
const fmt = n => new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD' }).format(n);

function showToast(msg, type = 'success') {
  const c = $('toast-container');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${type === 'success' ? '✓' : '✕'}</span> ${msg}`;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

async function api(method, url, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' }, credentials: 'include' };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  if (!r.ok) {
    const e = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(e.detail || 'Erreur serveur');
  }
  return r.json().catch(() => null);
}

/* ── NAV ── */
function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const el = $(`page-${page}`);
  if (el) el.classList.add('active');
  document.querySelectorAll('.nav-links a, .nav-links button').forEach(a => {
    a.classList.toggle('active', a.dataset.page === page);
  });
  // Load page data
  if (page === 'shop') loadProducts();
  if (page === 'orders') loadOrders();
  if (page === 'account') loadAccount();
  if (page === 'admin') loadAdmin();
  if (page === 'checkout') loadCheckout();
  window.scrollTo(0, 0);
}

/* ── AUTH ── */
async function loadUser() {
  try {
    currentUser = await api('GET', '/api/auth/me');
  } catch { currentUser = null; }
  renderNav();
}

function renderNav() {
  const links = $('nav-links');
  const right = $('nav-right');
  let html = `
    <a href="#" data-page="shop" onclick="navigate('shop');return false">Boutique</a>
  `;
  if (currentUser) {
    html += `
      <a href="#" data-page="orders" onclick="navigate('orders');return false">Commandes</a>
      <a href="#" data-page="account" onclick="navigate('account');return false">Mon compte</a>
    `;
    if (currentUser.is_admin) {
      html += `<a href="#" data-page="admin" onclick="navigate('admin');return false">Admin</a>`;
    }
  }
  links.innerHTML = html;

  right.innerHTML = `
    <button id="cart-btn" onclick="openCart()">
      🛒 Panier <span id="cart-count">0</span>
    </button>
    ${currentUser
      ? `<button class="btn-secondary" style="font-size:0.85rem;padding:0.45rem 0.9rem" onclick="logout()">Déconnexion</button>`
      : `<button class="btn-primary" onclick="navigate('login')">Connexion</button>`
    }
  `;
  updateCartCount();
}

async function logout() {
  await api('POST', '/api/auth/logout');
  currentUser = null;
  cart = [];
  renderNav();
  navigate('shop');
  showToast('Déconnecté');
}

/* ── LOGIN ── */
function initLogin() {
  $('login-form').onsubmit = async e => {
    e.preventDefault();
    const email = $('login-email').value;
    const password = $('login-password').value;
    try {
      currentUser = await api('POST', '/api/auth/login', { email, password });
      await loadCart();
      renderNav();
      navigate('shop');
      showToast(`Bienvenue, ${currentUser.full_name} !`);
    } catch (err) {
      $('login-error').textContent = err.message;
    }
  };
}

function initRegister() {
  $('register-form').onsubmit = async e => {
    e.preventDefault();
    const data = {
      full_name: $('reg-name').value,
      email: $('reg-email').value,
      password: $('reg-password').value,
    };
    try {
      currentUser = await api('POST', '/api/auth/register', data);
      renderNav();
      navigate('shop');
      showToast('Compte créé !');
    } catch (err) {
      $('register-error').textContent = err.message;
    }
  };
}

/* ── PRODUCTS ── */
async function loadProducts() {
  const grid = $('products-grid');
  grid.innerHTML = '<div class="spinner"></div>';

  const q = $('search-input')?.value || '';
  const catId = $('category-filter')?.value || '';
  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (catId) params.set('category_id', catId);

  try {
    products = await api('GET', `/api/products?${params}`);
    if (!categories.length) {
      categories = await api('GET', '/api/products/categories');
      renderCategoryFilter();
    }
    renderProducts(products);
  } catch (err) {
    grid.innerHTML = `<p class="form-error" style="padding:2rem">${err.message}</p>`;
  }
}

function renderCategoryFilter() {
  const sel = $('category-filter');
  if (!sel) return;
  let html = '<option value="">Toutes catégories</option>';
  categories.forEach(c => {
    html += `<option value="${c.id}">${c.name}</option>`;
  });
  sel.innerHTML = html;
}

function renderProducts(list) {
  const grid = $('products-grid');
  if (!list.length) {
    grid.innerHTML = `<div class="empty-state"><div class="icon">📦</div><p>Aucun produit trouvé</p></div>`;
    return;
  }
  grid.innerHTML = list.map(p => `
    <div class="product-card" onclick="openProduct(${p.id})">
      <img src="${p.image_url || 'https://via.placeholder.com/600x400?text=No+Image'}" alt="${p.name}" loading="lazy">
      <div class="product-card-body">
        ${p.category ? `<div class="category-badge">${p.category.name}</div>` : ''}
        <h3>${p.name}</h3>
        <p class="description">${p.description || ''}</p>
        <div class="product-card-footer">
          <span class="product-price">${fmt(p.price)}</span>
          <span class="stock-label ${p.stock < 5 ? 'low' : ''}">
            ${p.stock === 0 ? 'Épuisé' : p.stock < 5 ? `Plus que ${p.stock}` : `${p.stock} dispo`}
          </span>
        </div>
        <button
          class="add-to-cart-btn"
          style="width:100%;margin-top:0.75rem"
          onclick="event.stopPropagation();addToCart(${p.id})"
          ${p.stock === 0 ? 'disabled' : ''}
        >
          ${p.stock === 0 ? 'Épuisé' : 'Ajouter au panier'}
        </button>
      </div>
    </div>
  `).join('');
}

function openProduct(id) {
  const p = products.find(x => x.id === id);
  if (!p) return;
  const modal = $('product-modal');
  $('product-modal-content').innerHTML = `
    <img src="${p.image_url || ''}" alt="${p.name}" style="width:100%;height:220px;object-fit:cover;border-radius:8px;margin-bottom:1rem;background:var(--bg3)">
    ${p.category ? `<div class="category-badge" style="margin-bottom:0.5rem">${p.category.name}</div>` : ''}
    <h3 style="font-family:var(--font-display);font-size:1.6rem;margin-bottom:0.5rem">${p.name}</h3>
    <p style="color:var(--muted);margin-bottom:1rem">${p.description || ''}</p>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
      <span style="font-family:var(--font-display);font-size:1.8rem;color:var(--accent)">${fmt(p.price)}</span>
      <span class="stock-label ${p.stock < 5 ? 'low' : ''}">${p.stock === 0 ? 'Épuisé' : `${p.stock} en stock`}</span>
    </div>
    <button class="btn-primary" style="width:100%" onclick="addToCart(${p.id});closeModal('product-modal')" ${p.stock === 0 ? 'disabled' : ''}>
      ${p.stock === 0 ? 'Épuisé' : 'Ajouter au panier'}
    </button>
  `;
  modal.classList.add('open');
}

function closeModal(id) {
  $(id)?.classList.remove('open');
}

/* ── CART ── */
async function loadCart() {
  if (!currentUser) { cart = []; updateCartCount(); return; }
  try {
    cart = await api('GET', '/api/cart');
    updateCartCount();
  } catch { cart = []; }
}

function updateCartCount() {
  const el = $('cart-count');
  if (el) {
    const total = cart.reduce((s, i) => s + i.quantity, 0);
    el.textContent = total;
  }
}

function openCart() {
  if (!currentUser) { navigate('login'); return; }
  renderCartSidebar();
  $('cart-overlay').classList.add('open');
  $('cart-sidebar').classList.add('open');
}

function closeCart() {
  $('cart-overlay').classList.remove('open');
  $('cart-sidebar').classList.remove('open');
}

function renderCartSidebar() {
  const container = $('cart-items');
  if (!cart.length) {
    container.innerHTML = `<div class="empty-state"><div class="icon">🛒</div><p>Votre panier est vide</p></div>`;
    $('cart-checkout-btn').style.display = 'none';
    $('cart-footer-total').textContent = '';
    return;
  }
  const total = cart.reduce((s, i) => s + i.quantity * i.product.price, 0);
  container.innerHTML = cart.map(item => `
    <div class="cart-item">
      <img src="${item.product.image_url || ''}" alt="${item.product.name}">
      <div class="cart-item-info">
        <h4>${item.product.name}</h4>
        <div class="price">${fmt(item.product.price)} × ${item.quantity} = ${fmt(item.product.price * item.quantity)}</div>
        <div class="qty-control">
          <button onclick="updateCartItem(${item.id}, ${item.quantity - 1})">−</button>
          <span class="qty-num">${item.quantity}</span>
          <button onclick="updateCartItem(${item.id}, ${item.quantity + 1})">+</button>
          <button class="btn-danger" style="margin-left:0.3rem" onclick="updateCartItem(${item.id}, 0)">✕</button>
        </div>
      </div>
    </div>
  `).join('');
  $('cart-footer-total').innerHTML = `Total : <strong>${fmt(total)}</strong>`;
  $('cart-checkout-btn').style.display = 'block';
}

async function addToCart(productId) {
  if (!currentUser) { navigate('login'); return; }
  try {
    cart = await api('POST', '/api/cart', { product_id: productId, quantity: 1 });
    updateCartCount();
    showToast('Produit ajouté au panier');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function updateCartItem(itemId, qty) {
  try {
    if (qty <= 0) {
      cart = await api('DELETE', `/api/cart/${itemId}`);
    } else {
      cart = await api('PUT', `/api/cart/${itemId}`, { quantity: qty });
    }
    updateCartCount();
    renderCartSidebar();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

/* ── CHECKOUT ── */
function loadCheckout() {
  if (!currentUser) { navigate('login'); return; }
  const total = cart.reduce((s, i) => s + i.quantity * i.product.price, 0);

  const summary = $('checkout-summary');
  summary.innerHTML = cart.map(i => `
    <div class="order-summary-item">
      <span>${i.product.name} × ${i.quantity}</span>
      <span>${fmt(i.product.price * i.quantity)}</span>
    </div>
  `).join('') + `<div class="order-total-row"><span>Total</span><span>${fmt(total)}</span></div>`;

  // Pre-fill address
  if (currentUser.address) {
    $('checkout-address').value = `${currentUser.address}, ${currentUser.city || ''} ${currentUser.postal_code || ''}, ${currentUser.country || ''}`;
  }

  // Format card number input
  $('card-number').addEventListener('input', function() {
    let v = this.value.replace(/\D/g, '').substring(0, 16);
    this.value = v.replace(/(.{4})/g, '$1 ').trim();
  });

  $('checkout-form').onsubmit = async e => {
    e.preventDefault();
    const cardRaw = $('card-number').value.replace(/\s/g, '');
    const address = $('checkout-address').value;
    $('checkout-error').textContent = '';
    try {
      const order = await api('POST', '/api/orders/checkout', {
        shipping_address: address,
        card_number: cardRaw,
      });
      cart = [];
      updateCartCount();
      navigate('order-success');
      $('success-order-id').textContent = `#${order.id}`;
    } catch (err) {
      $('checkout-error').textContent = err.message;
    }
  };
}

/* ── ORDERS ── */
async function loadOrders() {
  if (!currentUser) { navigate('login'); return; }
  const container = $('orders-list');
  container.innerHTML = '<div class="spinner"></div>';
  try {
    const orders = await api('GET', '/api/orders/my');
    if (!orders.length) {
      container.innerHTML = `<div class="empty-state"><div class="icon">📋</div><p>Aucune commande pour l'instant</p></div>`;
      return;
    }
    container.innerHTML = orders.map(o => `
      <div class="order-card">
        <div class="order-card-header">
          <div>
            <h4>Commande #${o.id}</h4>
            <span class="date">${new Date(o.created_at).toLocaleDateString('fr-CA', { year:'numeric', month:'long', day:'numeric' })}</span>
          </div>
          <span class="status-badge status-${o.status}">${statusLabel(o.status)}</span>
        </div>
        <div class="order-items-list">
          ${o.items.map(i => `
            <div class="order-item-row">
              <span><strong>${i.product_name}</strong> × ${i.quantity}</span>
              <span>${fmt(i.unit_price * i.quantity)}</span>
            </div>
          `).join('')}
        </div>
        <div class="order-total">
          <span>Total</span>
          <span>${fmt(o.total)}</span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<p class="form-error" style="padding:2rem">${err.message}</p>`;
  }
}

function statusLabel(s) {
  return { pending: 'En cours', shipped: 'Expédiée', delivered: 'Livrée' }[s] || s;
}

/* ── ACCOUNT ── */
function loadAccount() {
  if (!currentUser) { navigate('login'); return; }
  $('acc-name').value = currentUser.full_name || '';
  $('acc-address').value = currentUser.address || '';
  $('acc-city').value = currentUser.city || '';
  $('acc-postal').value = currentUser.postal_code || '';
  $('acc-country').value = currentUser.country || 'Canada';
  $('acc-email-display').textContent = currentUser.email;

  $('account-form').onsubmit = async e => {
    e.preventDefault();
    try {
      await api('PUT', '/api/auth/profile', {
        full_name: $('acc-name').value,
        address: $('acc-address').value,
        city: $('acc-city').value,
        postal_code: $('acc-postal').value,
        country: $('acc-country').value,
      });
      currentUser.full_name = $('acc-name').value;
      showToast('Profil mis à jour');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };
}

/* ── ADMIN ── */
let adminTab = 'products';

function loadAdmin() {
  if (!currentUser?.is_admin) { navigate('shop'); return; }
  showAdminTab(adminTab);
}

function showAdminTab(tab) {
  adminTab = tab;
  document.querySelectorAll('.admin-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tab);
  });
  if (tab === 'products') loadAdminProducts();
  if (tab === 'orders') loadAdminOrders();
}

async function loadAdminProducts() {
  const c = $('admin-content');
  c.innerHTML = `
    <div class="admin-toolbar">
      <span style="color:var(--muted);font-size:0.9rem">Tous les produits</span>
      <button class="btn-primary" onclick="openProductModal()">+ Ajouter</button>
    </div>
    <div class="admin-table-wrap">
      <table>
        <thead><tr><th></th><th>Nom</th><th>Catégorie</th><th>Prix</th><th>Stock</th><th>Actions</th></tr></thead>
        <tbody id="admin-products-tbody"><tr><td colspan="6"><div class="spinner"></div></td></tr></tbody>
      </table>
    </div>
  `;
  try {
    const prods = await api('GET', '/api/products');
    const tbody = $('admin-products-tbody');
    if (!prods.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="color:var(--muted);text-align:center;padding:2rem">Aucun produit</td></tr>';
      return;
    }
    tbody.innerHTML = prods.map(p => `
      <tr>
        <td><img class="product-thumb" src="${p.image_url || ''}" alt="${p.name}"></td>
        <td><strong>${p.name}</strong></td>
        <td>${p.category?.name || '—'}</td>
        <td>${fmt(p.price)}</td>
        <td>${p.stock}</td>
        <td>
          <div class="admin-actions">
            <button class="btn-secondary" style="font-size:0.8rem;padding:0.35rem 0.7rem" onclick='openProductModal(${JSON.stringify(p)})'>Modifier</button>
            <button class="btn-danger" onclick="deleteProduct(${p.id})">Supprimer</button>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    c.innerHTML += `<p class="form-error">${err.message}</p>`;
  }
}

async function loadAdminOrders() {
  const c = $('admin-content');
  c.innerHTML = `
    <div class="admin-table-wrap">
      <table>
        <thead><tr><th>#</th><th>Client</th><th>Total</th><th>Date</th><th>Statut</th></tr></thead>
        <tbody id="admin-orders-tbody"><tr><td colspan="5"><div class="spinner"></div></td></tr></tbody>
      </table>
    </div>
  `;
  try {
    const orders = await api('GET', '/api/orders/all');
    const tbody = $('admin-orders-tbody');
    if (!orders.length) {
      tbody.innerHTML = '<tr><td colspan="5" style="color:var(--muted);text-align:center;padding:2rem">Aucune commande</td></tr>';
      return;
    }
    tbody.innerHTML = orders.map(o => `
      <tr>
        <td><strong>#${o.id}</strong></td>
        <td>${o.user?.full_name || '?'}<br><span style="color:var(--muted);font-size:0.78rem">${o.user?.email || ''}</span></td>
        <td>${fmt(o.total)}</td>
        <td style="color:var(--muted);font-size:0.82rem">${new Date(o.created_at).toLocaleDateString('fr-CA')}</td>
        <td>
          <select class="status-select" onchange="updateOrderStatus(${o.id}, this.value)">
            <option value="pending" ${o.status === 'pending' ? 'selected' : ''}>En cours</option>
            <option value="shipped" ${o.status === 'shipped' ? 'selected' : ''}>Expédiée</option>
            <option value="delivered" ${o.status === 'delivered' ? 'selected' : ''}>Livrée</option>
          </select>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    c.innerHTML += `<p class="form-error">${err.message}</p>`;
  }
}

async function updateOrderStatus(orderId, status) {
  try {
    await api('PUT', `/api/orders/${orderId}/status`, { status });
    showToast('Statut mis à jour');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openProductModal(product = null) {
  const modal = $('product-modal-form');
  $('product-modal-title').textContent = product ? 'Modifier le produit' : 'Ajouter un produit';

  // Populate category options
  const catSel = $('pm-category');
  catSel.innerHTML = '<option value="">— Aucune —</option>' +
    categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

  // Fill form
  $('pm-id').value = product?.id || '';
  $('pm-name').value = product?.name || '';
  $('pm-description').value = product?.description || '';
  $('pm-price').value = product?.price || '';
  $('pm-stock').value = product?.stock ?? '';
  $('pm-image').value = product?.image_url || '';
  $('pm-active').checked = product ? product.is_active : true;
  if (product?.category) catSel.value = product.category.id;

  modal.classList.add('open');
}

$('product-form').onsubmit = async function(e) {
  e.preventDefault();
  const id = $('pm-id').value;
  const data = {
    name: $('pm-name').value,
    description: $('pm-description').value,
    price: parseFloat($('pm-price').value),
    stock: parseInt($('pm-stock').value),
    image_url: $('pm-image').value,
    category_id: $('pm-category').value ? parseInt($('pm-category').value) : null,
    is_active: $('pm-active').checked,
  };
  try {
    if (id) {
      await api('PUT', `/api/products/${id}`, data);
      showToast('Produit mis à jour');
    } else {
      await api('POST', '/api/products', data);
      showToast('Produit ajouté');
    }
    closeModal('product-modal-form');
    loadAdminProducts();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

async function deleteProduct(id) {
  if (!confirm('Supprimer ce produit ?')) return;
  try {
    await api('DELETE', `/api/products/${id}`);
    showToast('Produit supprimé');
    loadAdminProducts();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

/* ── SEARCH ── */
let searchTimer;
function onSearchInput() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadProducts, 350);
}

/* ── INIT ── */
async function init() {
  await loadUser();
  if (currentUser) await loadCart();
  navigate('shop');
  initLogin();
  initRegister();
}

document.addEventListener('DOMContentLoaded', init);
