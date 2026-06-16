const express = require('express');
const { db } = require('../db');
const { render, escapeHtml, flash, csrfField, verifyCsrf } = require('../view-engine');
const { requireManager } = require('../middleware');
const router = express.Router();
router.use(requireManager);
function validateRoom(body) {
  const name = String(body.name || '').trim().slice(0, 80);
  const capacity = Number(body.capacity);
  const equipment = String(body.equipment || '').trim().slice(0, 250);
  const photoUrl = String(body.photo_url || '').trim().slice(0, 500);
  if (!name || !Number.isInteger(capacity) || capacity < 1 || !/^https?:\/\//.test(photoUrl)) return null;
  return { name, capacity, equipment, photoUrl };
}
router.get('/manager/dashboard', (req, res) => {
  const rooms = db.prepare('SELECT * FROM rooms ORDER BY name').all();
  const start = new Date();
  const end = new Date(start.getTime() + 30 * 86400000);
  const pad = n => String(n).padStart(2, '0');
  const iso = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  const occupancy = rooms.map(room => {
    const total = db.prepare('SELECT COUNT(*) AS total FROM reservations WHERE room_id = ? AND start_time >= ? AND start_time < ?').get(room.id, iso(start), iso(end)).total;
    const rate = Math.min(100, (total / 300) * 100).toFixed(1);
    return `<tr><td>${escapeHtml(room.name)}</td><td>${total} h</td><td><progress max="100" value="${rate}"></progress> ${rate} %</td></tr>`;
  }).join('');
  const reservations = db.prepare(`SELECT reservations.id, reservations.start_time, rooms.name AS room_name, users.email FROM reservations JOIN rooms ON rooms.id = reservations.room_id JOIN users ON users.id = reservations.user_id WHERE datetime(reservations.start_time) >= datetime('now', 'localtime') ORDER BY reservations.start_time LIMIT 20`).all();
  const upcoming = reservations.map(r => `<tr><td>${escapeHtml(r.room_name)}</td><td>${escapeHtml(r.email)}</td><td>${escapeHtml(r.start_time.replace('T', ' à '))}</td><td><form method="post" action="/manager/bookings/${r.id}/cancel" data-confirm="Annuler cette réservation ?">${csrfField(req)}<button class="danger">Annuler</button></form></td></tr>`).join('');
  render(req, res, 'dashboard', { title: 'Tableau de bord', occupancy, upcoming: upcoming || '<tr><td colspan="4">Aucune réservation à venir.</td></tr>' });
});
router.get('/manager/rooms', (req, res) => {
  const rows = db.prepare('SELECT * FROM rooms ORDER BY name').all().map(room => `<tr><td>${escapeHtml(room.name)}</td><td>${room.capacity}</td><td>${escapeHtml(room.equipment)}</td><td class="actions"><a class="button secondary" href="/manager/rooms/${room.id}/edit">Modifier</a><form method="post" action="/manager/rooms/${room.id}/delete" data-confirm="Supprimer cette salle et ses réservations ?">${csrfField(req)}<button class="danger">Supprimer</button></form></td></tr>`).join('');
  render(req, res, 'manage-rooms', { title: 'Gestion des salles', roomRows: rows || '<tr><td colspan="4">Aucune salle.</td></tr>' });
});
router.get('/manager/rooms/new', (req, res) => render(req, res, 'room-form', { title: 'Ajouter une salle', heading: 'Ajouter une salle', action: '/manager/rooms', name: '', capacity: '', equipment: '', photoUrl: '' }));
router.post('/manager/rooms', verifyCsrf, (req, res) => {
  const room = validateRoom(req.body);
  if (!room) { flash(req, 'error', 'Données de salle invalides. La photo doit être une URL HTTP(S).'); return res.redirect('/manager/rooms/new'); }
  db.prepare('INSERT INTO rooms (name, capacity, equipment, photo_url) VALUES (?, ?, ?, ?)').run(room.name, room.capacity, room.equipment, room.photoUrl);
  flash(req, 'success', 'Salle ajoutée.');
  res.redirect('/manager/rooms');
});
router.get('/manager/rooms/:id/edit', (req, res) => {
  const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(req.params.id);
  if (!room) return res.status(404).send('Salle introuvable.');
  render(req, res, 'room-form', { title: 'Modifier une salle', heading: 'Modifier une salle', action: `/manager/rooms/${room.id}/edit`, name: escapeHtml(room.name), capacity: room.capacity, equipment: escapeHtml(room.equipment), photoUrl: escapeHtml(room.photo_url) });
});
router.post('/manager/rooms/:id/edit', verifyCsrf, (req, res) => {
  const room = validateRoom(req.body);
  if (!room) { flash(req, 'error', 'Données de salle invalides.'); return res.redirect(`/manager/rooms/${req.params.id}/edit`); }
  const result = db.prepare('UPDATE rooms SET name = ?, capacity = ?, equipment = ?, photo_url = ? WHERE id = ?').run(room.name, room.capacity, room.equipment, room.photoUrl, req.params.id);
  flash(req, result.changes ? 'success' : 'error', result.changes ? 'Salle modifiée.' : 'Salle introuvable.');
  res.redirect('/manager/rooms');
});
router.post('/manager/rooms/:id/delete', verifyCsrf, (req, res) => {
  const result = db.prepare('DELETE FROM rooms WHERE id = ?').run(req.params.id);
  flash(req, result.changes ? 'success' : 'error', result.changes ? 'Salle supprimée.' : 'Salle introuvable.');
  res.redirect('/manager/rooms');
});
router.post('/manager/bookings/:id/cancel', verifyCsrf, (req, res) => {
  const result = db.prepare('DELETE FROM reservations WHERE id = ?').run(req.params.id);
  flash(req, result.changes ? 'success' : 'error', result.changes ? 'Réservation annulée par le gestionnaire.' : 'Réservation introuvable.');
  res.redirect('/manager/dashboard');
});
module.exports = router;
