const express = require('express');
const router = express.Router();
const { getDatabase } = require('../database');
const { isAuthenticated } = require('../middleware/auth');

// Create booking form
router.get('/create/:roomId', isAuthenticated, (req, res) => {
  const db = getDatabase();
  const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(req.params.roomId);
  
  if (!room) {
    return res.status(404).render('error', { message: 'Salle non trouvée' });
  }

  res.render('bookings/create', { room, error: null });
});

// Create booking
router.post('/', isAuthenticated, (req, res) => {
  const { room_id, date, start_time, title } = req.body;
  const db = getDatabase();

  // Calculate end time (1 hour after start)
  const startHour = parseInt(start_time.split(':')[0]);
  const endHour = startHour + 1;
  const end_time = `${endHour.toString().padStart(2, '0')}:00`;

  // Check for conflicts
  const conflict = db.prepare(`
    SELECT * FROM bookings 
    WHERE room_id = ? 
    AND date = ? 
    AND status = 'confirmed'
    AND (
      (start_time <= ? AND end_time > ?) OR
      (start_time < ? AND end_time >= ?) OR
      (start_time >= ? AND end_time <= ?)
    )
  `).get(room_id, date, start_time, start_time, end_time, end_time, start_time, end_time);

  if (conflict) {
    const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(room_id);
    return res.render('bookings/create', { room, error: 'Ce créneau est déjà réservé' });
  }

  // Validate time (8h-18h)
  if (startHour < 8 || startHour >= 18) {
    const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(room_id);
    return res.render('bookings/create', { room, error: 'Les réservations sont possibles entre 8h et 18h' });
  }

  // Create booking
  const result = db.prepare(
    'INSERT INTO bookings (room_id, user_id, date, start_time, end_time, title) VALUES (?, ?, ?, ?, ?, ?)'
  ).run(room_id, req.session.user.id, date, start_time, end_time, title || 'Réunion');

  // Create notification for upcoming booking
  const bookingDate = new Date(date + 'T' + start_time);
  const now = new Date();
  const hoursUntilBooking = (bookingDate - now) / (1000 * 60 * 60);
  
  if (hoursUntilBooking <= 24 && hoursUntilBooking > 0) {
    db.prepare(
      'INSERT INTO notifications (user_id, booking_id, message) VALUES (?, ?, ?)'
    ).run(req.session.user.id, result.lastInsertRowid, 
      `Rappel : Votre réservation "${title || 'Réunion'}" commence dans ${Math.round(hoursUntilBooking)} heures`);
  }

  res.redirect('/bookings/my-bookings');
});

// View user's bookings
router.get('/my-bookings', isAuthenticated, (req, res) => {
  const db = getDatabase();
  const bookings = db.prepare(`
    SELECT bookings.*, rooms.name as room_name 
    FROM bookings 
    JOIN rooms ON bookings.room_id = rooms.id 
    WHERE bookings.user_id = ? 
    ORDER BY bookings.date DESC, bookings.start_time DESC
  `).all(req.session.user.id);

  res.render('bookings/my-bookings', { bookings });
});

// Edit booking form
router.get('/edit/:id', isAuthenticated, (req, res) => {
  const db = getDatabase();
  const booking = db.prepare('SELECT * FROM bookings WHERE id = ?').get(req.params.id);
  
  if (!booking) {
    return res.status(404).render('error', { message: 'Réservation non trouvée' });
  }

  if (booking.user_id !== req.session.user.id && req.session.user.role !== 'admin') {
    return res.status(403).render('error', { message: 'Non autorisé' });
  }

  const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(booking.room_id);
  res.render('bookings/edit', { booking, room, error: null });
});

// Update booking
router.post('/update/:id', isAuthenticated, (req, res) => {
  const { date, start_time, title } = req.body;
  const db = getDatabase();
  const booking = db.prepare('SELECT * FROM bookings WHERE id = ?').get(req.params.id);

  if (!booking) {
    return res.status(404).render('error', { message: 'Réservation non trouvée' });
  }

  if (booking.user_id !== req.session.user.id && req.session.user.role !== 'admin') {
    return res.status(403).render('error', { message: 'Non autorisé' });
  }

  const startHour = parseInt(start_time.split(':')[0]);
  const endHour = startHour + 1;
  const end_time = `${endHour.toString().padStart(2, '0')}:00`;

  // Check for conflicts (excluding current booking)
  const conflict = db.prepare(`
    SELECT * FROM bookings 
    WHERE room_id = ? 
    AND date = ? 
    AND id != ?
    AND status = 'confirmed'
    AND (
      (start_time <= ? AND end_time > ?) OR
      (start_time < ? AND end_time >= ?) OR
      (start_time >= ? AND end_time <= ?)
    )
  `).get(booking.room_id, date, booking.id, start_time, start_time, end_time, end_time, start_time, end_time);

  if (conflict) {
    const room = db.prepare('SELECT * FROM rooms WHERE id = ?').get(booking.room_id);
    return res.render('bookings/edit', { booking, room, error: 'Ce créneau est déjà réservé' });
  }

  db.prepare(
    'UPDATE bookings SET date = ?, start_time = ?, end_time = ?, title = ? WHERE id = ?'
  ).run(date, start_time, end_time, title, req.params.id);

  res.redirect('/bookings/my-bookings');
});

// Cancel booking
router.post('/cancel/:id', isAuthenticated, (req, res) => {
  const db = getDatabase();
  const booking = db.prepare('SELECT * FROM bookings WHERE id = ?').get(req.params.id);

  if (!booking) {
    return res.status(404).render('error', { message: 'Réservation non trouvée' });
  }

  if (booking.user_id !== req.session.user.id && req.session.user.role !== 'admin') {
    return res.status(403).render('error', { message: 'Non autorisé' });
  }

  db.prepare('UPDATE bookings SET status = ? WHERE id = ?').run('cancelled', req.params.id);
  res.redirect('/bookings/my-bookings');
});

module.exports = router;