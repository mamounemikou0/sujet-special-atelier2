const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const views = path.join(__dirname, 'views');
const escapeHtml = (value = '') => String(value)
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#39;');

function flash(req, type, text) {
  req.session.flash = { type, text };
}
function popFlash(req) {
  const item = req.session.flash;
  delete req.session.flash;
  return item;
}
function csrfToken(req) {
  if (!req.session.csrfToken) req.session.csrfToken = crypto.randomBytes(24).toString('hex');
  return req.session.csrfToken;
}
function csrfField(req) {
  return `<input type="hidden" name="_csrf" value="${escapeHtml(csrfToken(req))}">`;
}
function verifyCsrf(req, res, next) {
  if (!req.body || req.body._csrf !== req.session.csrfToken) {
    return res.status(403).send('Jeton CSRF invalide. Rechargez la page et recommencez.');
  }
  next();
}
function nav(req, unreadCount) {
  const auth = req.session.user;
  const links = ['<a href="/rooms">Salles</a>'];
  if (auth) {
    links.push('<a href="/bookings/mine">Mes réservations</a>');
    links.push(`<a href="/notifications">Notifications <span class="badge">${unreadCount}</span></a>`);
    if (auth.role === 'manager') links.push('<a href="/manager/dashboard">Gestionnaire</a>');
    links.push(`<span class="identity">${escapeHtml(auth.email)}</span><form class="inline" method="post" action="/logout">${csrfField(req)}<button class="link-btn">Déconnexion</button></form>`);
  } else {
    links.push('<a href="/login">Connexion</a><a href="/register">Inscription</a>');
  }
  return links.join('');
}
function render(req, res, view, data = {}) {
  const body = fs.readFileSync(path.join(views, `${view}.html`), 'utf8');
  const layout = fs.readFileSync(path.join(views, 'layout.html'), 'utf8');
  const notice = popFlash(req);
  const unreadCount = req.locals?.unreadCount || 0;
  const replacements = {
    title: escapeHtml(data.title || 'Réservation de salles'),
    content: body,
    nav: nav(req, unreadCount),
    flash: notice ? `<div class="flash ${escapeHtml(notice.type)}">${escapeHtml(notice.text)}</div>` : '',
    csrf: csrfField(req),
    ...data
  };
  let html = layout;
  for (const [key, value] of Object.entries(replacements)) html = html.replaceAll(`{{${key}}}`, String(value));
  for (const [key, value] of Object.entries(replacements)) html = html.replaceAll(`{{${key}}}`, String(value));
  res.send(html);
}
module.exports = { render, escapeHtml, flash, csrfField, verifyCsrf };
