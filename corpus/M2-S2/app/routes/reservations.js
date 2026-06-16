const express = require('express');
const router = express.Router();
const db = require('../db');
const { requireAuth, requireManager } = require('../middleware');
const path = require('path');

// GET /reservations - my reservations
router.get('/', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/reservations.html'));
});

// GET /reservations/new?room_id=&date=&hour=
router.get('/new', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/reservation-form.html'));
});

// POST /reservations/new
router.post('/new', requireAuth, (req, res) => {
  const { room_id, date, hour, title } = req.body;
  const userId = req.session.userId;

  if (!room_id || !date || hour === undefined) {
    return res.redirect('/reservations/new?error=missing');
  }

  // Validate date format and not in past
  const dateObj = new Date(date + 'T' + String(hour).padStart(2, '0') + ':00:00');
  if (isNaN(dateObj.getTime()) || dateObj < new Date()) {
    return res.redirect('/reservations/new?error=date&room_id=' + room_id + '&date=' + date);
  }

  // Check conflict
  const conflict = db.prepare('SELECT id FROM reservations WHERE room_id=? AND date=? AND hour=? AND status=?').get(
    room_id, date, parseInt(hour), 'active'
  );
  if (conflict) {
    return res.redirect('/reservations/new?error=conflict&room_id=' + room_id + '&date=' + date);
  }

  const result = db.prepare(
    'INSERT INTO reservations (room_id, user_id, date, hour, title) VALUES (?, ?, ?, ?, ?)'
  ).run(room_id, userId, date, parseInt(hour), title || 'Réunion');

  // Create reminder notification (simulated - set for "approaching" check)
  db.prepare(
    'INSERT INTO notifications (user_id, reservation_id, message) VALUES (?, ?, ?)'
  ).run(userId, result.lastInsertRowid,
    `Rappel : votre réservation "${title || 'Réunion'}" approche (${date} à ${hour}h).`
  );

  res.redirect('/reservations');
});

// GET /reservations/:id/edit
router.get('/:id/edit', requireAuth, (req, res) => {
  const reservation = db.prepare('SELECT * FROM reservations WHERE id=?').get(parseInt(req.params.id));
  if (!reservation) return res.status(404).send('Réservation introuvable');
  if (reservation.user_id !== req.session.userId && req.session.userRole !== 'gestionnaire') {
    return res.status(403).send('Accès refusé');
  }
  res.sendFile(path.join(__dirname, '../views/reservation-form.html'));
});

// POST /reservations/:id/edit
router.post('/:id/edit', requireAuth, (req, res) => {
  const id = parseInt(req.params.id);
  const reservation = db.prepare('SELECT * FROM reservations WHERE id=?').get(id);
  if (!reservation) return res.status(404).send('Réservation introuvable');
  if (reservation.user_id !== req.session.userId && req.session.userRole !== 'gestionnaire') {
    return res.status(403).send('Accès refusé');
  }

  const { room_id, date, hour, title } = req.body;

  // Check conflict (exclude self)
  const conflict = db.prepare(
    'SELECT id FROM reservations WHERE room_id=? AND date=? AND hour=? AND status=? AND id!=?'
  ).get(room_id, date, parseInt(hour), 'active', id);
  if (conflict) {
    return res.redirect('/reservations/' + id + '/edit?error=conflict');
  }

  db.prepare('UPDATE reservations SET room_id=?, date=?, hour=?, title=? WHERE id=?').run(
    room_id, date, parseInt(hour), title || 'Réunion', id
  );

  // Update notification
  db.prepare('UPDATE notifications SET message=? WHERE reservation_id=?').run(
    `Rappel : votre réservation "${title || 'Réunion'}" approche (${date} à ${hour}h).`, id
  );

  if (req.session.userRole === 'gestionnaire') return res.redirect('/dashboard');
  res.redirect('/reservations');
});

// POST /reservations/:id/cancel
router.post('/:id/cancel', requireAuth, (req, res) => {
  const id = parseInt(req.params.id);
  const reservation = db.prepare('SELECT * FROM reservations WHERE id=?').get(id);
  if (!reservation) return res.status(404).send('Réservation introuvable');
  if (reservation.user_id !== req.session.userId && req.session.userRole !== 'gestionnaire') {
    return res.status(403).send('Accès refusé');
  }

  db.prepare("UPDATE reservations SET status='cancelled' WHERE id=?").run(id);
  db.prepare("UPDATE notifications SET message=? WHERE reservation_id=?").run(
    `Votre réservation "${reservation.title}" du ${reservation.date} à ${reservation.hour}h a été annulée.`,
    id
  );
  db.prepare("UPDATE notifications SET read=0 WHERE reservation_id=?").run(id);

  const referer = req.get('Referer') || '/reservations';
  res.redirect(referer);
});

module.exports = router;
