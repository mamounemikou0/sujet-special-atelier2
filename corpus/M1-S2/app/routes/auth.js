const express = require('express');
const bcrypt = require('bcryptjs');
const { db } = require('../db');
const { render, escapeHtml, flash, verifyCsrf } = require('../view-engine');

const router = express.Router();
router.get('/register', (req, res) => render(req, res, 'register', { title: 'Inscription' }));
router.post('/register', verifyCsrf, (req, res) => {
  const email = String(req.body.email || '').trim().toLowerCase();
  const password = String(req.body.password || '');
  if (!/^\S+@\S+\.\S+$/.test(email) || password.length < 8) {
    flash(req, 'error', 'Saisissez un email valide et un mot de passe de 8 caractères minimum.');
    return res.redirect('/register');
  }
  try {
    const result = db.prepare('INSERT INTO users (email, password_hash) VALUES (?, ?)').run(email, bcrypt.hashSync(password, 12));
    req.session.user = { id: result.lastInsertRowid, email, role: 'user' };
    flash(req, 'success', 'Compte créé. Bienvenue !');
    return res.redirect('/rooms');
  } catch (err) {
    if (err.code === 'SQLITE_CONSTRAINT_UNIQUE') flash(req, 'error', 'Cet email est déjà utilisé.');
    else flash(req, 'error', 'Impossible de créer le compte.');
    return res.redirect('/register');
  }
});
router.get('/login', (req, res) => render(req, res, 'login', { title: 'Connexion' }));
router.post('/login', verifyCsrf, (req, res) => {
  const email = String(req.body.email || '').trim().toLowerCase();
  const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
  if (!user || !bcrypt.compareSync(String(req.body.password || ''), user.password_hash)) {
    flash(req, 'error', 'Email ou mot de passe incorrect.');
    return res.redirect('/login');
  }
  req.session.user = { id: user.id, email: user.email, role: user.role };
  flash(req, 'success', `Connexion réussie : ${escapeHtml(user.email)}.`);
  res.redirect('/rooms');
});
router.post('/logout', verifyCsrf, (req, res) => req.session.destroy(() => res.redirect('/login')));
module.exports = router;
