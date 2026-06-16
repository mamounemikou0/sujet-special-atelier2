const express = require('express');
const router = express.Router();
const Database = require('better-sqlite3');
const db = new Database('app.db');
const { requireAuth, requireAdmin } = require('../middleware');

router.get('/my-bookings', requireAuth, (req, res) => {
    const bookings = db.prepare(`
        SELECT b.*, r.name as room_name, r.capacity, r.equipment, r.photo_url
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE b.user_id = ?
        ORDER BY b.start_time DESC
    `).all(req.session.userId);

    res.json({ bookings });
});

router.get('/:id', requireAuth, (req, res) => {
    const booking = db.prepare(`
        SELECT b.*, r.name as room_name, r.capacity, r.equipment, r.photo_url, u.email, u.id as user_id
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        JOIN users u ON b.user_id = u.id
        WHERE b.id = ?
    `).get(req.params.id);

    if (!booking) {
        return res.status(404).json({ error: 'Réservation non trouvée' });
    }

    if (booking.user_id !== req.session.userId && req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Accès non autorisé' });
    }

    res.json({ booking });
});

router.post('/', requireAuth, (req, res) => {
    const { room_id, start_time, end_time } = req.body;

    if (!room_id || !start_time || !end_time) {
        return res.status(400).json({ error: 'Tous les champs sont obligatoires' });
    }

    const start = new Date(start_time);
    const end = new Date(end_time);

    if (end <= start) {
        return res.status(400).json({ error: 'La date de fin doit être postérieure à la date de début' });
    }

    const durationMinutes = (end - start) / (1000 * 60);
    if (durationMinutes < 60) {
        return res.status(400).json({ error: 'La réservation doit durer au moins 1 heure' });
    }

    const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(room_id);
    if (!room) {
        return res.status(404).json({ error: 'Salle non trouvée' });
    }

    const existingBooking = db.prepare(`
        SELECT * FROM bookings
        WHERE room_id = ?
        AND NOT (end_time <= ? OR start_time >= ?)
        AND status = 'confirmed'
    `).get(room_id, start_time, end_time);

    if (existingBooking) {
        return res.status(400).json({ error: 'La salle est déjà réservée pour ce créneau' });
    }

    const roundedStart = new Date(Math.ceil(start.getTime() / (60 * 60 * 1000)) * (60 * 60 * 1000));
    const roundedEnd = new Date(Math.ceil(end.getTime() / (60 * 60 * 1000)) * (60 * 60 * 1000));

    const result = db.prepare('INSERT INTO bookings (user_id, room_id, start_time, end_time) VALUES (?, ?, ?, ?)')
        .run(req.session.userId, room_id, roundedStart.toISOString(), roundedEnd.toISOString());

    db.prepare('INSERT INTO notifications (user_id, booking_id, message) VALUES (?, ?, ?)')
        .run(req.session.userId, result.lastInsertRowid, `Nouvelle réservation créée pour ${room.name}`);

    res.json({ success: true, bookingId: result.lastInsertRowid });
});

router.put('/:id', requireAuth, (req, res) => {
    const { room_id, start_time, end_time } = req.body;
    const bookingId = req.params.id;

    const booking = db.prepare('SELECT * FROM bookings WHERE id = ?').get(bookingId);
    if (!booking) {
        return res.status(404).json({ error: 'Réservation non trouvée' });
    }

    if (booking.user_id !== req.session.userId && req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Accès