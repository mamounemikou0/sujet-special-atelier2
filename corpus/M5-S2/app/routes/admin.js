const express = require('express');
const router = express.Router();
const { getDatabase } = require('../database');
const { isAuthenticated, isAdmin } = require('../middleware/auth');

// Admin dashboard
router.get('/dashboard', isAuthenticated, isAdmin, (req, res) => {
  const db = getDatabase();
  
  // Occupancy rate for the last 30 days
  const stats = db.prepare(`
    SELECT 
      rooms.id,
      rooms.name,
      COUNT(bookings.id) as total_bookings,
      ROUND(COUNT(bookings.id) * 100.0 / 300, 2) as occupancy_rate
    FROM rooms
    LEFT JOIN bookings ON rooms.id = bookings.room_id 
      AND bookings.date >= date('now', '-30 days')
      AND bookings.status = 'confirmed'
    GROUP BY rooms.id
  `).all();

  const totalBookings = db.prepare(
    "SELECT COUNT(*) as count FROM bookings WHERE status = 'confirmed'"
  ).get();

  const totalUsers = db.prepare("SELECT COUNT(*) as count FROM users").get();
  const totalRooms = db.prepare("SELECT COUNT(*) as count FROM rooms").get();

  res.render('admin/dashboard', {
    stats,
    totalBookings: totalBookings.count,
    totalUsers: totalUsers.count,
    totalRooms: totalRooms.count
  });
});

// Manage rooms
router.get('/rooms', isAuthenticated, isAdmin, (req, res) => {
  const db = getDatabase();
  const rooms = db.prepare('SELECT * FROM rooms ORDER BY name').all();
  res.render('admin/rooms', { rooms });
});

// Add room form
router.get('/rooms/add', isAuthenticated, isAdmin, (req, res) => {
  res.render('admin/room-form', { room: null, error: null });
});

// Add room
router.post('/rooms', isAuthenticated, isAdmin, (req, res) => {
  const { name, capacity, equipment, photo_url } = req.body;
  const db = getDatabase();

  try {
    db.prepare(
      'INSERT INTO rooms (name, capacity, equipment, photo_url) VALUES (?, ?, ?, ?)'
    ).run(name, capacity, equipment, photo_url);
    res.redirect('/admin/rooms');
  } catch (error) {
    res.render('admin/room-form', { 
      room: null, 
      error: 'Erreur lors de l\'ajout de la salle' 
    });
  }
});

// Edit room form
router.get('/rooms/edit/:id', isAuthenticated, isAdmin, (req, res) => {
  const db = getDatabase();
  const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(req.params.id);
  
  if (!room) {
    return res.status(404).render('error', { message: 'Salle non trouvée' });
  }

  res.render('admin/room-form', { room, error: null });
});

// Update room
router.post('/rooms/update/:id', isAuthenticated, isAdmin, (req, res) => {
  const { name, capacity, equipment, photo_url } = req.body;
  const db = getDatabase();

  db.prepare(
    'UPDATE rooms SET name = ?, capacity = ?, equipment = ?, photo_url = ? WHERE id = ?'
  ).run(name, capacity, equipment, photo_url, req.params.id);

  res.redirect('/admin/rooms');
});

// Delete room
router.post('/rooms/delete/:id', isAuthenticated, isAdmin, (req, res) => {
  const db = getDatabase();
  db.prepare('DELETE FROM rooms WHERE id = ?').run(req.params.id);
  res.redirect('/admin/rooms');
});

// Cancel any booking (admin)
router.post('/bookings/cancel/:id', isAuthenticated, isAdmin, (req, res) => {
  const db = getDatabase();
  db.prepare('UPDATE bookings SET status = ? WHERE id = ?').run('cancelled', req.params.id);
  res.redirect('/admin/dashboard');
});

module.exports = router;