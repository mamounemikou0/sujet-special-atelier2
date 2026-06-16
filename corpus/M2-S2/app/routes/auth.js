const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const db = require('../db');

// GET /login
router.get('/login', (req, res) => {
  if (req.session.userId) return res.redirect('/');
  const redirect = req.query.redirect || '/';
  res.sendFile(require('path').join(__dirname, '../views/login.html'));
});

// POST /login
router.post('/login', (req, res) => {
  const { email, password, redirect } = req.body;
  const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
  if (!user || !bcrypt.compareSync(password, user.password)) {
    return res.redirect('/login?error=1');
  }
  req.session.userId = user.id;
  req.session.userName = user.name;
  req.session.userEmail = user.email;
  req.session.userRole = user.role;
  res.redirect(redirect || '/');
});

// GET /register
router.get('/register', (req, res) => {
  if (req.session.userId) return res.redirect('/');
  res.sendFile(require('path').join(__dirname, '../views/register.html'));
});

// POST /register
router.post('/register', (req, res) => {
  const { email, password, name } = req.body;
  if (!email || !password || !name || password.length < 6) {
    return res.redirect('/register?error=1');
  }
  const existing = db.prepare('SELECT id FROM users WHERE email = ?').get(email);
  if (existing) {
    return res.redirect('/register?error=2');
  }
  const hash = bcrypt.hashSync(password, 10);
  const result = db.prepare('INSERT INTO users (email, password, name) VALUES (?, ?, ?)').run(email, hash, name);
  req.session.userId = result.lastInsertRowid;
  req.session.userName = name;
  req.session.userEmail = email;
  req.session.userRole = 'user';
  res.redirect('/');
});

// GET /logout
router.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/login');
});

module.exports = router;
