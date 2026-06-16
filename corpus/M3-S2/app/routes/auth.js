const express = require('express');
const router = express.Router();
const db = require('../database');
const crypto = require('crypto');

const hashPassword = (p) => crypto.createHash('sha256').update(p).digest('hex');

router.get('/login', (req, res) => {
    if (req.session.user) return res.redirect('/');
    res.render('login', { error: null });
});

router.post('/login', (req, res) => {
    const { email, password } = req.body;
    const hashed = hashPassword(password);
    const user = db.prepare("SELECT * FROM users WHERE email = ? AND password = ?").get(email, hashed);
    
    if (user) {
        req.session.user = { id: user.id, email: user.email, role: user.role };
        res.redirect('/');
    } else {
        res.render('login', { error: "Identifiants invalides." });
    }
});

router.get('/register', (req, res) => {
    if (req.session.user) return res.redirect('/');
    res.render('register', { error: null });
});

router.post('/register', (req, res) => {
    const { email, password } = req.body;
    const hashed = hashPassword(password);
    try {
        db.prepare("INSERT INTO users (email, password, role) VALUES (?, ?, 'user')").run(email, hashed);
        res.redirect('/auth/login');
    } catch (err) {
        res.render('register', { error: "Cette adresse email est déjà prise." });
    }
});

router.get('/logout', (req, res) => {
    req.session.destroy();
    res.redirect('/auth/login');
});

module.exports = router;