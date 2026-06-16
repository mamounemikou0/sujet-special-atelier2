const express = require('express');
const router = express.Router();
const db = require('../database');

function isAuthenticated(req, res, next) {
    if (req.session && req.session.user) return next();
    res.redirect('/auth/login');
}

router.get('/:id', isAuthenticated, (req, res) => {
    const roomId = req.params.id;
    const date = req.query.date || new Date().toISOString().split('T')[0];
    
    const room = db.prepare("SELECT * FROM rooms WHERE id = ?").get(roomId);
    if (!room) return res.status(404).send("Salle introuvable.");

    // Récupérer toutes les réservations de la salle pour le jour sélectionné
    const bookings = db.prepare(`
        SELECT b.*, u.email 
        FROM bookings b 
        JOIN users u ON b.user_id = u.id 
        WHERE b.room_id = ? AND b.date = ?
    `).all(roomId, date);

    // Modélisation de la journée de travail (de 8h00 à 18h00 - blocs d'1 heure)
    const hours = [];
    for (let h = 8; h <= 17; h++) {
        const foundBooking = bookings.find(b => b.start_hour === h);
        hours.push({
            hour: h,
            booking: foundBooking || null
        });
    }

    res.render('room', { room, date, hours, user: req.session.user });
});

module.exports = router;