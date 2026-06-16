const express = require('express');
const router = express.Router();
const db = require('../db');
const { requireAuth, requireManager } = require('../middleware');
const path = require('path');

// GET /rooms - list all rooms
router.get('/', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/rooms.html'));
});

// GET /rooms/:id - room detail + calendar
router.get('/:id', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/room-detail.html'));
});

// ---- Manager routes ----

// GET /rooms/manage/new
router.get('/manage/new', requireManager, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/room-form.html'));
});

// POST /rooms/manage/new
router.post('/manage/new', requireManager, (req, res) => {
  const { name, capacity, equipment, photo_url } = req.body;
  if (!name || !capacity) return res.redirect('/rooms/manage/new?error=1');
  db.prepare('INSERT INTO rooms (name, capacity, equipment, photo_url) VALUES (?, ?, ?, ?)').run(
    name, parseInt(capacity), equipment || '', photo_url || ''
  );
  res.redirect('/rooms');
});

// GET /rooms/manage/:id/edit
router.get('/manage/:id/edit', requireManager, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/room-form.html'));
});

// POST /rooms/manage/:id/edit
router.post('/manage/:id/edit', requireManager, (req, res) => {
  const { name, capacity, equipment, photo_url } = req.body;
  const id = parseInt(req.params.id);
  db.prepare('UPDATE rooms SET name=?, capacity=?, equipment=?, photo_url=? WHERE id=?').run(
    name, parseInt(capacity), equipment || '', photo_url || '', id
  );
  res.redirect('/rooms');
});

// POST /rooms/manage/:id/delete
router.post('/manage/:id/delete', requireManager, (req, res) => {
  const id = parseInt(req.params.id);
  db.prepare('UPDATE rooms SET active=0 WHERE id=?').run(id);
  res.redirect('/rooms');
});

module.exports = router;
