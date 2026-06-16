const express = require('express');
const router = express.Router();
const { getDatabase } = require('../database');
const { isAuthenticated } = require('../middleware/auth');

// List all rooms
router.get('/', isAuthenticated, (req, res) => {
  const db = getDatabase();
  const rooms = db.prepare('SELECT * FROM rooms ORDER BY name').all();
  res.render('rooms/list', { rooms });
});

// View room details with calendar
router.get('/:id', isAuthenticated, (req, res) => {
  const db = getDatabase();
  const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(req.params.id);
  
  if (!room) {
    return res.status(404).render('error', { message: 'Salle non trouvée' });
  }

  // Get bookings for the next 7 days
  const today = new Date();
  const endDate = new Date(today);
  endDate.setDate(endDate.getDate() + 7);

  const bookings = db.prepare(`
    SELECT bookings.*, users.name as user_name 
    FROM bookings 
    JOIN users ON bookings.user_id = users.id 
    WHERE bookings.room_id = ? 
    AND bookings.date BETWEEN ? AND ? 
    AND bookings.status = 'confirmed'
    ORDER BY bookings.date, bookings.start_time
  `).all(room.id, today.toISOString().split('T')[0], endDate.toISOString().split('T')[0]);

  res.render('rooms/detail', { room, bookings });
});

module.exports = router;