const express = require('express');
const { db } = require('../db');
const { render, escapeHtml, flash, csrfField, verifyCsrf } = require('../view-engine');
const { requireAuth } = require('../middleware');
const router = express.Router();

function validSlot(start, end) {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:00$/.test(start) || !/^\d{4}-\d{2}-\d{2}T\d{2}:00$/.test(end)) return false;
  const startDate = new Date(start);
  const endDate = new Date(end);
  const hour = startDate.getHours();
  return endDate - startDate === 3600000 && hour >= 8 && hour < 18 && startDate > new Date();
}
function ownBooking(id, userId) {
  return db.prepare('SELECT * FROM reservations WHERE id = ? AND user_id = ?').get(id, userId);
}
router.use(requireAuth);
router.get('/bookings/mine', (req, res) => {
  const bookings = db.prepare(`SELECT reservations.*, rooms.name AS room_name FROM reservations JOIN rooms ON rooms.id = reservations.room_id WHERE user_id = ? ORDER BY start_time DESC`).all(req.session.user.id);
  const cards = bookings.map(b => `<article class="booking"><h2>${escapeHtml(b.room_name)}</h2><p>${escapeHtml(b.start_time.replace('T', ' à '))} – ${escapeHtml(b.end_time.slice(11))}</p><p>${escapeHtml(b.purpose)}</p><div class="actions"><a class="button secondary" href="/bookings/${b.id}/edit">Modifier</a><form method="post" action="/bookings/${b.id}/cancel" data-confirm="Annuler cette réservation ?">${csrfField(req)}<button class="danger">Annuler</button></form></div></article>`).join('');
  render(req, res, 'my-bookings', { title: 'Mes réservations', bookings: cards || '<p>Vous n’avez aucune réservation.</p>' });
});
router.post('/bookings', verifyCsrf, (req, res) => {
  const roomId = Number(req.body.room_id);
  const start = String(req.body.start_time || '');
  const end = String(req.body.end_time || '');
  const purpose = String(req.body.purpose || '').trim().slice(0, 120);
  if (!db.prepare('SELECT id FROM rooms WHERE id = ?').get(roomId) || !purpose || !validSlot(start, end)) {
    flash(req, 'error', 'Créneau invalide ou déjà passé.');
    return res.redirect('/rooms');
  }
  try {
    db.prepare('INSERT INTO reservations (room_id, user_id, start_time, end_time, purpose) VALUES (?, ?, ?, ?, ?)').run(roomId, req.session.user.id, start, end, purpose);
    flash(req, 'success', 'Réservation créée.');
  } catch (err) {
    flash(req, 'error', err.code === 'SQLITE_CONSTRAINT_UNIQUE' ? 'Ce créneau vient d’être réservé.' : 'Création impossible.');
  }
  res.redirect(`/rooms/${roomId}/calendar?date=${start.slice(0, 10)}`);
});
router.get('/bookings/:id/edit', (req, res) => {
  const booking = ownBooking(req.params.id, req.session.user.id);
  if (!booking) return res.status(404).send('Réservation introuvable.');
  const rooms = db.prepare('SELECT * FROM rooms ORDER BY name').all().map(r => `<option value="${r.id}" ${r.id === booking.room_id ? 'selected' : ''}>${escapeHtml(r.name)}</option>`).join('');
  render(req, res, 'edit-booking', { title: 'Modifier une réservation', bookingId: booking.id, rooms, startTime: escapeHtml(booking.start_time), purpose: escapeHtml(booking.purpose) });
});
router.post('/bookings/:id/edit', verifyCsrf, (req, res) => {
  const booking = ownBooking(req.params.id, req.session.user.id);
  if (!booking) return res.status(404).send('Réservation introuvable.');
  const roomId = Number(req.body.room_id);
  const start = String(req.body.start_time || '');
  const startDate = new Date(start);
  const endDate = new Date(startDate.getTime() + 3600000);
  const pad = n => String(n).padStart(2, '0');
  const end = `${endDate.getFullYear()}-${pad(endDate.getMonth()+1)}-${pad(endDate.getDate())}T${pad(endDate.getHours())}:00`;
  const purpose = String(req.body.purpose || '').trim().slice(0, 120);
  if (!purpose || !validSlot(start, end) || !db.prepare('SELECT id FROM rooms WHERE id = ?').get(roomId)) {
    flash(req, 'error', 'Modification invalide. Choisissez un créneau futur d’une heure.');
    return res.redirect(`/bookings/${booking.id}/edit`);
  }
  try {
    db.prepare('UPDATE reservations SET room_id = ?, start_time = ?, end_time = ?, purpose = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?').run(roomId, start, end, purpose, booking.id);
    db.prepare('DELETE FROM notifications WHERE reservation_id = ?').run(booking.id);
    flash(req, 'success', 'Réservation modifiée.');
    res.redirect('/bookings/mine');
  } catch (err) {
    flash(req, 'error', err.code === 'SQLITE_CONSTRAINT_UNIQUE' ? 'Cette salle est déjà réservée sur ce créneau.' : 'Modification impossible.');
    res.redirect(`/bookings/${booking.id}/edit`);
  }
});
router.post('/bookings/:id/cancel', verifyCsrf, (req, res) => {
  const result = db.prepare('DELETE FROM reservations WHERE id = ? AND user_id = ?').run(req.params.id, req.session.user.id);
  flash(req, result.changes ? 'success' : 'error', result.changes ? 'Réservation annulée.' : 'Réservation introuvable.');
  res.redirect('/bookings/mine');
});
module.exports = router;
