const express = require('express');
const router = express.Router();
const db = require('../db');
const { requireAuth, requireManager } = require('../middleware');

// GET /api/rooms
router.get('/rooms', requireAuth, (req, res) => {
  const rooms = db.prepare('SELECT * FROM rooms WHERE active=1 ORDER BY name').all();
  res.json(rooms);
});

// GET /api/rooms/:id
router.get('/rooms/:id', requireAuth, (req, res) => {
  const room = db.prepare('SELECT * FROM rooms WHERE id=? AND active=1').get(parseInt(req.params.id));
  if (!room) return res.status(404).json({ error: 'Salle introuvable' });
  res.json(room);
});

// GET /api/rooms/:id/slots?date=YYYY-MM-DD
router.get('/rooms/:id/slots', requireAuth, (req, res) => {
  const { date } = req.query;
  if (!date) return res.status(400).json({ error: 'Date requise' });
  const reservations = db.prepare(
    `SELECT r.*, u.name as user_name, u.email as user_email
     FROM reservations r
     JOIN users u ON u.id = r.user_id
     WHERE r.room_id=? AND r.date=? AND r.status='active'
     ORDER BY r.hour`
  ).all(parseInt(req.params.id), date);
  res.json(reservations);
});

// GET /api/reservations - current user's reservations
router.get('/reservations', requireAuth, (req, res) => {
  const reservations = db.prepare(
    `SELECT r.*, ro.name as room_name, ro.capacity as room_capacity
     FROM reservations r
     JOIN rooms ro ON ro.id = r.room_id
     WHERE r.user_id=?
     ORDER BY r.date DESC, r.hour DESC`
  ).all(req.session.userId);
  res.json(reservations);
});

// GET /api/reservations/:id
router.get('/reservations/:id', requireAuth, (req, res) => {
  const reservation = db.prepare(
    `SELECT r.*, ro.name as room_name, ro.capacity
     FROM reservations r
     JOIN rooms ro ON ro.id = r.room_id
     WHERE r.id=?`
  ).get(parseInt(req.params.id));
  if (!reservation) return res.status(404).json({ error: 'Introuvable' });
  if (reservation.user_id !== req.session.userId && req.session.userRole !== 'gestionnaire') {
    return res.status(403).json({ error: 'Accès refusé' });
  }
  res.json(reservation);
});

// GET /api/notifications
router.get('/notifications', requireAuth, (req, res) => {
  const notifs = db.prepare(
    'SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 20'
  ).all(req.session.userId);
  res.json(notifs);
});

// POST /api/notifications/:id/read
router.post('/notifications/:id/read', requireAuth, (req, res) => {
  db.prepare('UPDATE notifications SET read=1 WHERE id=? AND user_id=?').run(
    parseInt(req.params.id), req.session.userId
  );
  res.json({ ok: true });
});

// POST /api/notifications/read-all
router.post('/notifications/read-all', requireAuth, (req, res) => {
  db.prepare('UPDATE notifications SET read=1 WHERE user_id=?').run(req.session.userId);
  res.json({ ok: true });
});

// GET /api/session
router.get('/session', (req, res) => {
  if (!req.session.userId) return res.json({ authenticated: false });
  res.json({
    authenticated: true,
    userId: req.session.userId,
    userName: req.session.userName,
    userEmail: req.session.userEmail,
    userRole: req.session.userRole
  });
});

// ---- Manager API ----

// GET /api/dashboard/stats
router.get('/dashboard/stats', requireManager, (req, res) => {
  const totalRooms = db.prepare('SELECT COUNT(*) as c FROM rooms WHERE active=1').get().c;
  const totalUsers = db.prepare('SELECT COUNT(*) as c FROM users').get().c;
  const totalReservations = db.prepare("SELECT COUNT(*) as c FROM reservations WHERE status='active'").get().c;

  // Occupancy per room this week
  const today = new Date();
  const weekStart = new Date(today);
  weekStart.setDate(today.getDate() - today.getDay() + 1);
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  const fmt = d => d.toISOString().slice(0, 10);

  const occupancy = db.prepare(
    `SELECT ro.name, ro.capacity,
       COUNT(r.id) as reserved_slots,
       ROUND(COUNT(r.id) * 100.0 / (5 * 9), 1) as occupancy_pct
     FROM rooms ro
     LEFT JOIN reservations r ON r.room_id = ro.id
       AND r.date >= ? AND r.date <= ? AND r.status='active'
     WHERE ro.active=1
     GROUP BY ro.id`
  ).all(fmt(weekStart), fmt(weekEnd));

  const recentReservations = db.prepare(
    `SELECT r.*, u.name as user_name, u.email as user_email, ro.name as room_name
     FROM reservations r
     JOIN users u ON u.id = r.user_id
     JOIN rooms ro ON ro.id = r.room_id
     WHERE r.status='active'
     ORDER BY r.created_at DESC LIMIT 10`
  ).all();

  const topUsers = db.prepare(
    `SELECT u.name, u.email, COUNT(r.id) as count
     FROM users u
     JOIN reservations r ON r.user_id = u.id
     WHERE r.status='active'
     GROUP BY u.id ORDER BY count DESC LIMIT 5`
  ).all();

  res.json({ totalRooms, totalUsers, totalReservations, occupancy, recentReservations, topUsers });
});

// GET /api/dashboard/all-reservations
router.get('/dashboard/all-reservations', requireManager, (req, res) => {
  const { date, room_id } = req.query;
  let query = `SELECT r.*, u.name as user_name, u.email as user_email, ro.name as room_name
               FROM reservations r
               JOIN users u ON u.id = r.user_id
               JOIN rooms ro ON ro.id = r.room_id
               WHERE 1=1`;
  const params = [];
  if (date) { query += ' AND r.date=?'; params.push(date); }
  if (room_id) { query += ' AND r.room_id=?'; params.push(room_id); }
  query += ' ORDER BY r.date DESC, r.hour ASC';
  const reservations = db.prepare(query).all(...params);
  res.json(reservations);
});

module.exports = router;
