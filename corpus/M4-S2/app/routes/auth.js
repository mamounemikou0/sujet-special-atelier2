const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const Database = require('better-sqlite3');
const db = new Database('app.db');

router.post('/register', (req, res) => {
    const { email, password, confirmPassword } = req.body;

    if (!email || !password || !confirmPassword) {
        return res.status(400).json({ error: 'Tous les champs sont obligatoires' });
    }

    if (password !== confirmPassword) {
        return res.status(400).json({ error: 'Les mots de passe ne correspondent pas' });
    }

    const existingUser = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
    if (existingUser) {
        return res.status(400).json({ error: 'Cet email est déjà utilisé' });
    }

    const hashedPassword = bcrypt.hashSync(password, 10);
    const result = db.prepare('INSERT INTO users (email, password) VALUES (?, ?)').run(email, hashedPassword);

    res.json({ success: true, userId: result.lastInsertRowid });
});

router.post('/login', (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({ error: 'Email et mot de passe sont obligatoires' });
    }

    const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
    if (!user) {
        return res.status(401).json({ error: 'Identifiants invalides' });
    }

    const passwordMatch = bcrypt.compareSync(password, user.password);
    if (!passwordMatch) {
        return res.status(401).json({ error: 'Identifiants invalides' });
    }

    req.session.userId = user.id;
    req.session.save(() => {
        res.json({ success: true, user: { id: user.id, email: user.email, role: user.role } });
    });
});

router.post('/logout', (req, res) => {
    req.session.destroy(err => {
        if (err) {
            return res.status(500).json({ error: 'Erreur lors de la déconnexion' });
        }
        res.clearCookie('connect.sid');
        res.json({ success: true });
    });
});

router.get('/me', (req, res) => {
    if (!req.session.userId) {
        return res.json({ user: null });
    }
    const user = db.prepare('SELECT id, email, role FROM users WHERE id = ?').get(req.session.userId);
    res.json({ user });
});

module.exports = router;