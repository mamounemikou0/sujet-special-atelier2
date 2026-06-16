const express = require('express');
const session = require('express-session');
const path = require('path');

// Init DB (creates tables + seeds data)
require('./db');

const app = express();
const PORT = process.env.PORT || 3000;

// Session store with SQLite
const SQLiteStore = require('connect-sqlite3')(session);

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.use(session({
  store: new SQLiteStore({ db: 'sessions.db', dir: __dirname }),
  secret: 'salle-resa-secret-2024',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 7 * 24 * 60 * 60 * 1000 }
}));

// Inject session info into all responses via locals (for HTML templates we use API calls)
app.use((req, res, next) => {
  res.locals.userId = req.session.userId;
  res.locals.userName = req.session.userName;
  res.locals.userRole = req.session.userRole;
  next();
});

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// Routes
app.use('/', require('./routes/auth'));
app.use('/rooms', require('./routes/rooms'));
app.use('/reservations', require('./routes/reservations'));
app.use('/dashboard', require('./routes/dashboard'));
app.use('/api', require('./routes/api'));

// Home redirect
app.get('/', (req, res) => {
  if (!req.session.userId) return res.redirect('/login');
  res.redirect('/rooms');
});

// Notification cron simulation: check every minute for reservations in <24h
function checkUpcomingReservations() {
  const db = require('./db');
  const now = new Date();
  const in24h = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  const today = now.toISOString().slice(0, 10);
  const tomorrow = in24h.toISOString().slice(0, 10);
  const currentHour = now.getHours();

  // Find reservations in next 24h that haven't been notified yet
  const upcoming = db.prepare(
    `SELECT r.*, u.name as user_name, ro.name as room_name
     FROM reservations r
     JOIN users u ON u.id = r.user_id
     JOIN rooms ro ON ro.id = r.room_id
     WHERE r.status='active'
       AND ((r.date=? AND r.hour > ?) OR (r.date=? AND r.hour <= ?))
       AND NOT EXISTS (
         SELECT 1 FROM notifications n
         WHERE n.reservation_id = r.id AND n.message LIKE 'RAPPEL24H%'
       )`
  ).all(today, currentHour, tomorrow, currentHour);

  for (const res of upcoming) {
    db.prepare('INSERT INTO notifications (user_id, reservation_id, message) VALUES (?, ?, ?)').run(
      res.user_id, res.id,
      `RAPPEL24H : Votre réservation "${res.title}" dans la salle "${res.room_name}" est dans moins de 24h (${res.date} à ${res.hour}h00).`
    );
  }
}

// Run notification check every 5 minutes
setInterval(checkUpcomingReservations, 5 * 60 * 1000);
checkUpcomingReservations(); // run once on start

app.listen(PORT, () => {
  console.log(`\n✅ Serveur démarré sur http://localhost:${PORT}`);
  console.log(`   Gestionnaire : admin@example.com / admin1234`);
  console.log(`   Arrêt : Ctrl+C\n`);
});
