const express = require('express');
const { db } = require('../db');
const { render, escapeHtml, csrfField } = require('../view-engine');
const { requireAuth } = require('../middleware');

const router = express.Router();
const pad = (n) => String(n).padStart(2, '0');
const dateOnly = (d = new Date()) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const validDate = (value) => /^\d{4}-\d{2}-\d{2}$/.test(value || '') ? value : dateOnly();

router.get('/rooms', (req, res) => {
  const rooms = db.prepare('SELECT * FROM rooms ORDER BY name').all();
  const cards = rooms.map(room => `<article class="room-card"><img src="${escapeHtml(room.photo_url)}" alt="${escapeHtml(room.name)}"><div class="room-details"><h2>${escapeHtml(room.name)}</h2><p><strong>Capacité :</strong> ${room.capacity} personnes</p><p><strong>Équipements :</strong> ${escapeHtml(room.equipment)}</p><a class="button" href="/rooms/${room.id}/calendar">Voir le calendrier</a></div></article>`).join('');
  render(req, res, 'rooms', { title: 'Salles disponibles', rooms: cards || '<p>Aucune salle enregistrée.</p>' });
});
router.get('/rooms/:id/calendar', (req, res) => {
  const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(req.params.id);
  if (!room) return res.status(404).send('Salle introuvable.');
  const date = validDate(req.query.date);
  const reservations = db.prepare(`SELECT reservations.*, users.email FROM reservations JOIN users ON users.id = reservations.user_id WHERE room_id = ? AND start_time LIKE ? ORDER BY start_time`).all(room.id, `${date}%`);
  const byStart = new Map(reservations.map(r => [r.start_time, r]));
  const rows = [];
  for (let hour = 8; hour < 18; hour += 1) {
    const start = `${date}T${pad(hour)}:00`;
    const end = `${date}T${pad(hour + 1)}:00`;
    const booking = byStart.get(start);
    if (booking) {
      rows.push(`<tr class="occupied"><td>${pad(hour)}:00–${pad(hour + 1)}:00</td><td>Réservé par ${escapeHtml(booking.email)}</td><td>${escapeHtml(booking.purpose || 'Réunion')}</td></tr>`);
    } else if (new Date(start) <= new Date()) {
      rows.push(`<tr class="occupied"><td>${pad(hour)}:00–${pad(hour + 1)}:00</td><td>Créneau passé</td><td>Indisponible</td></tr>`);
    } else if (req.session.user) {
      rows.push(`<tr><td>${pad(hour)}:00–${pad(hour + 1)}:00</td><td>Disponible</td><td><form method="post" action="/bookings">${csrfField(req)}<input type="hidden" name="room_id" value="${room.id}"><input type="hidden" name="start_time" value="${start}"><input type="hidden" name="end_time" value="${end}"><input name="purpose" maxlength="120" placeholder="Objet de la réunion" required><button>Réserver</button></form></td></tr>`);
    } else {
      rows.push(`<tr><td>${pad(hour)}:00–${pad(hour + 1)}:00</td><td>Disponible</td><td><a href="/login">Se connecter pour réserver</a></td></tr>`);
    }
  }
  render(req, res, 'calendar', { title: `Calendrier - ${room.name}`, roomName: escapeHtml(room.name), roomId: room.id, date, calendarRows: rows.join('') });
});
module.exports = router;
