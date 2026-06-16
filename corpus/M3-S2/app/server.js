const express = require('express');
const session = require('express-session');
const path = require('path');
const ejs = require('ejs');
const db = require('./database');

const app = express();

// Configuration des middlewares essentiels
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Configuration des sessions utilisateur
app.use(session({
    secret: 'secret-key-corporate-booking-system',
    resave: false,
    saveUninitialized: false
}));

// Configuration du moteur de template pour lire les fichiers .html avec EJS
app.engine('html', ejs.renderFile);
app.set('view engine', 'html');
app.set('views', path.join(__dirname, 'views'));

// Middleware de vérification de l'authentification globale
function isAuthenticated(req, res, next) {
    if (req.session && req.session.user) return next();
    res.redirect('/auth/login');
}

// Importation et montage des routeurs
const authRoutes = require('./routes/auth');
const roomRoutes = require('./routes/rooms');
const bookingRoutes = require('./routes/bookings');
const managerRoutes = require('./routes/manager');

app.use('/auth', authRoutes);
app.use('/rooms', roomRoutes);
app.use('/bookings', bookingRoutes);
app.use('/manager', managerRoutes);

// Route principale : Accueil et liste des salles
app.get('/', isAuthenticated, (req, res) => {
    const today = new Date().toISOString().split('T')[0];
    
    // Simulation automatique de notification : si l'utilisateur a une réservation aujourd'hui
    const upcomingBookings = db.prepare(`
        SELECT b.*, r.name as room_name 
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE b.user_id = ? AND b.date = ?
    `).all(req.session.user.id, today);

    for (const b of upcomingBookings) {
        const msg = `Rappel : Votre réservation pour la "${b.room_name}" à ${b.start_hour}h00 commence aujourd'hui !`;
        // Éviter les doublons de notification
        const exists = db.prepare("SELECT id FROM notifications WHERE user_id = ? AND message = ?").get(req.session.user.id, msg);
        if (!exists) {
            db.prepare("INSERT INTO notifications (user_id, message) VALUES (?, ?)")
              .run(req.session.user.id, msg);
        }
    }

    const notifications = db.prepare("SELECT * FROM notifications WHERE user_id = ? AND is_read = 0").all(req.session.user.id);
    const rooms = db.prepare("SELECT * FROM rooms").all();

    res.render('index', { rooms, notifications, user: req.session.user });
});

// Route pour vider les notifications lues
app.post('/notifications/read', isAuthenticated, (req, res) => {
    db.prepare("UPDATE notifications SET is_read = 1 WHERE user_id = ?").run(req.session.user.id);
    res.redirect('/');
});

// Lancement du serveur informatique
const PORT = 3000;
app.listen(PORT, () => {
    console.log(`🚀 Serveur actif sur : http://localhost:${PORT}`);
});