const express = require('express');
const router = express.Router();
const Database = require('better-sqlite3');
const db = new Database('app.db');
const { requireAuth, requireAdmin } = require('../middleware');

router.get('/', (req, res) => {
    const rooms = db.prepare(`SELECT * FROM rooms ORDER BY name`).all();
    res.json({ rooms });
});

router.get('/:id', (req, res) => {
    const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(req.params.id);
    if (!room) {
        return res.status(404).json({ error: 'Salle non trouvée' });
    }
    res.json({ room });
});

router.get('/:id/calendar', (req, res) => {
    const { startDate, endDate } = req.query;
    const roomId = req.params.id;
    const start = startDate || new Date().toISOString().split('T')[0];
    const end = endDate || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    const bookings = db.prepare(`
        SELECT b.*, u.email, u.id as user_id, u.role as user_role
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.room_id = ?
        AND b.start_time >= ?
        AND b.start_time <= ?
        ORDER BY b.start_time
    `).all(roomId, start, end);

    res.json({ bookings });
});

router.post('/', requireAdmin, (req, res) => {
    const { name, capacity, equipment, photo_url } = req.body;

    if (!name || !capacity) {
        return res.status(400).json({ error: 'Le nom et la capacité sont obligatoires' });
    }

    const result = db.prepare('INSERT INTO rooms (name, capacity, equipment, photo_url) VALUES (?, ?, ?, ?)')
        .run(name, parseInt(capacity), equipment || '', photo_url || '');

    res.json({ success: true, roomId: result.lastInsertRowid });
});

router.put('/:id', requireAdmin, (req, res) => {
    const { name, capacity, equipment, photo_url } = req.body;
    const roomId = req.params.id;

    const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(roomId);
    if (!room) {
        return res.status(404).json({ error: 'Salle non trouvée' });
    }

    const updates = [];
    const values = [];

    if (name !== undefined) { updates.push('name = ?'); values.push(name); }
    if (capacity !== undefined) { updates.push('capacity = ?'); values.push(parseInt(capacity)); }
    if (equipment !== undefined) { updates.push('equipment = ?'); values.push(equipment); }
    if (photo_url !== undefined) { updates.push('photo_url = ?'); values.push(photo_url); }

    if (updates.length === 0) {
        return res.json({ success: true, message: 'Aucune modification' });
    }

    values.push(roomId);
    db.prepare(`UPDATE rooms SET ${updates.join(', ')} WHERE id = ?`).run(...values);

    res.json({ success: true });
});

router.delete('/:id', requireAdmin, (req, res) => {
    const roomId = req.params.id;

    const bookings = db.prepare('SELECT COUNT(*) as count FROM bookings WHERE room_id = ?').get(roomId);
    if (bookings.count > 0) {
        return res.status(400).json({ error: 'Impossible de supprimer : des réservations existent pour cette salle' });
    }

    db.prepare('DELETE FROM rooms WHERE id = ?').run(roomId);
    res.json({ success: true });
});

router.get('/available', (req, res) => {
    const { startTime, endTime, capacity } = req.query;

    if (!startTime || !endTime) {
        return res.status(400).json({ error: 'Les dates de début et de fin sont obligatoires' });
    }

    const availableRooms = db.prepare(`
        SELECT r.*
        FROM rooms r
        WHERE r.id NOT IN (
            SELECT DISTINCT b.room_id
            FROM bookings b
            WHERE NOT (b.end_time <= ? OR b.start_time >= ?)
        )
        ${capacity ? 'AND r.capacity >= ?' : ''}
        ORDER BY r.capacity
    `).all(startTime, endTime, capacity ? parseInt(capacity) : null);

    res.json({ rooms: availableRooms });
});

module.exports = router;