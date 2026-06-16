const express = require('express');
const bcrypt = require('bcryptjs');
const router = express.Router();
const { getDatabase } = require('../database');

// Login page
router.get('/login', (req, res) => {
  res.render('login', { error: null });
});

// Login process
router.post('/login', (req, res) => {
  const { email, password } = req.body;
  const db = getDatabase();
  
  const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
  
  if (!user || !bcrypt.compareSync(password, user.password)) {
    return res.render('login', { error: 'Email ou mot de passe incorrect' });
  }

  req.session.user = {
    id: user.id,
    email: user.email,
    name: user.name,
    role: user.role
  };

  res.redirect('/');
});

// Register page
router.get('/register', (req, res) => {
  res.render('register', { error: null });
});

// Register process
router.post('/register', (req, res) => {
  const { email, password, name } = req.body;
  const db = getDatabase();

  try {
    const hashedPassword = bcrypt.hashSync(password, 10);
    const result = db.prepare('INSERT INTO users (email, password, name) VALUES (?, ?, ?)').run(email, hashedPassword, name);
    
    req.session.user = {
      id: result.lastInsertRowid,
      email: email,
      name: name,
      role: 'user'
    };

    res.redirect('/');
  } catch (error) {
    if (error.code === 'SQLITE_CONSTRAINT_UNIQUE') {
      return res.render('register', { error: 'Cet email est déjà utilisé' });
    }
    res.render('register', { error: 'Erreur lors de l\'inscription' });
  }
});

// Logout
router.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/');
});

module.exports = router;