const express = require('express');
const router = express.Router();
const db = require('../database');

function isAuthenticated(req, res, next) {
    if (req.session && req.session.user) return next();
    res.redirect('/auth/login');
}

// Ajouter une réservation
router.post('/create', isAuthenticated, (req, res) => {
    const { room_id, date, start_hour } = req.body;
    try {
        db.prepare("INSERT INTO bookings (room_id, user_id, date, start_hour) VALUES (?, ?, ?, ?)")
          .run(room_id, req.session.user.id, date, parseInt(start_hour));
        res.redirect(`/rooms/${room_id}?date=${date}`);
    } catch (err) {
        res.status(400).send("Erreur : Ce créneau horaire est déjà occupé. <a href='javascript:history.back()'>Retour</a>");
    }
});

// Écran de modification de réservation
router.get('/edit/:id', isAuthenticated, (req, res) => {
    const booking = db.prepare("SELECT b.*, r.name as room_name FROM bookings b JOIN rooms r ON b.room_id = r.id WHERE b.id = ?").get(req.params.id);
    if (!booking) return res.status(404).send("Réservation introuvable.");

    // Protection de la ressource : auteur ou gestionnaire uniquement
    if (booking.user_id !== req.session.user.id && req.session.user.role !== 'manager') {
        return res.status(403).send("Droits insuffisants.");
    }

    res.render('booking-edit', { booking, user: req.session.user });
});

// Action de mise à jour de la réservation
router.post('/edit/:id', isAuthenticated, (req, res) => {
    const { date, start_hour } = req.body;
    const bookingId = req.params.id;

    const booking = db.prepare("SELECT * FROM bookings WHERE id = ?").get(bookingId);
    if (!booking) return res.status(404).send("Réservation introuvable.");

    if (booking.user_id !== req.session.user.id && req.session.user.role !== 'manager') {
        return res.status(403).send("Droits insuffisants.");
    }

    try {
        db.prepare("UPDATE bookings SET date = ?, start_hour = ? WHERE id = ?")
          .run(date, parseInt(start_hour), bookingId);
        res.redirect(`/rooms/${booking.room_id}?date=${date}`);
    } catch (err) {
        res.status(400).send("Erreur : Le créneau cible est indisponible. <a href='javascript:history.back()'>Retour</a>");
    }
});

// Supprimer/Annuler une réservation
router.post('/delete/:id', isAuthenticated, (req, res) => {
    const bookingId = req.params.id;
    const booking = db.prepare("SELECT * FROM bookings WHERE id = ?").get(bookingId);
    if (!booking) return res.status(404).send("Réservation introuvable.");

    if (booking.user_id !== req.session.user.id && req.session.user.role !== 'manager') {
        return res.status(403).send("Droits insuffisants.");
    }

    db.prepare("DELETE FROM bookings WHERE id = ?").run(bookingId);

    // Redirection adaptative selon l'origine du clic (Espace Gestionnaire vs Planning classique)
    if (req.headers.referer && req.headers.referer.includes('manager')) {
        res.redirect('/manager');
    } else {
        res.redirect(`/rooms/${booking.room_id}?date=${booking.date}`);
    }
});

module.exports = router;