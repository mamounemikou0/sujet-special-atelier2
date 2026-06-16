const express = require('express');
const router = express.Router();
const db = require('../database');

function isManager(req, res, next) {
    if (req.session && req.session.user && req.session.user.role === 'manager') return next();
    res.status(403).send("Accès restreint aux gestionnaires.");
}

// Dashboard principal du gestionnaire
router.get('/', isManager, (req, res) => {
    const rooms = db.prepare("SELECT * FROM rooms").all();
    
    const allBookings = db.prepare(`
        SELECT b.*, r.name as room_name, u.email as user_email 
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        JOIN users u ON b.user_id = u.id
        ORDER BY b.date DESC, b.start_hour ASC
    `).all();

    // Calcul du taux d'occupation simulé par salle (Total réservations / Capacité théorique de 40 créneaux)
    const stats = rooms.map(room => {
        const bookedCount = db.prepare("SELECT COUNT(*) as count FROM bookings WHERE room_id = ?").get(room.id).count;
        const totalCapacitySlots = 40; 
        const rate = Math.min(Math.round((bookedCount / totalCapacitySlots) * 100), 100);
        return {
            ...room,
            bookedCount,
            occupancyRate: rate
        };
    });

    res.render('manager', { rooms, allBookings, stats, user: req.session.user });
});

// Ajouter une salle
router.post('/rooms/add', isManager, (req, res) => {
    const { name, capacity, equipment, photo_url } = req.body;
    db.prepare("INSERT INTO rooms (name, capacity, equipment, photo_url) VALUES (?, ?, ?, ?)")
      .run(name, parseInt(capacity), equipment, photo_url);
    res.redirect('/manager');
});

// Vue modification de salle
router.get('/rooms/edit/:id', isManager, (req, res) => {
    const room = db.prepare("SELECT * FROM rooms WHERE id = ?").get(req.params.id);
    if (!room) return res.status(404).send("Salle introuvable.");
    res.render('room-edit', { room, user: req.session.user });
});

// Enregistrer la modification de salle
router.post('/rooms/edit/:id', isManager, (req, res) => {
    const { name, capacity, equipment, photo_url } = req.body;
    db.prepare("UPDATE rooms SET name = ?, capacity = ?, equipment = ?, photo_url = ? WHERE id = ?")
      .run(name, parseInt(capacity), equipment, photo_url, req.params.id);
    res.redirect('/manager');
});

// Supprimer une salle
router.post('/rooms/delete/:id', isManager, (req, res) => {
    db.prepare("DELETE FROM rooms WHERE id = ?").run(req.params.id);
    res.redirect('/manager');
});

module.exports = router;