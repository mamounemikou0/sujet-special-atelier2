const express = require('express');
const session = require('express-session');
const path = require('path');
const Database = require('better-sqlite3');
const bcrypt = require('bcryptjs');
const multer = require('multer');
const { requireAuth, requireAdmin } = require('./middleware');

const app = express();
const PORT = process.env.PORT || 3000;

const db = new Database('app.db');

function initDatabase() {
    db.exec(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            equipment TEXT,
            photo_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            booking_id INTEGER,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        );

        CREATE INDEX IF NOT EXISTS idx_bookings_room ON bookings(room_id);
        CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
        CREATE INDEX IF NOT EXISTS idx_bookings_time ON bookings(start_time, end_time);
    `);

    const adminExists = db.prepare('SELECT * FROM users WHERE email = ?').get('admin@example.com');
    if (!adminExists) {
        const hashedPassword = bcrypt.hashSync('admin123', 10);
        db.prepare('INSERT INTO users (email, password, role) VALUES (?, ?, ?)')
            .run('admin@example.com', hashedPassword, 'admin');
    }

    const roomCount = db.prepare('SELECT COUNT(*) as count FROM rooms').get().count;
    if (roomCount === 0) {
        const rooms = [
            { name: 'Salle de Réunion A', capacity: 10, equipment: 'Projecteur, Tableau blanc, WiFi', photo_url: 'https://images.unsplash.com/photo-1556761175-4b46a572b786?w=400&h=300&fit=crop' },
            { name: 'Salle de Conférence', capacity: 25, equipment: 'Écran géant, Sonorisation, WiFi, Tableau interactif', photo_url: 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=400&h=300&fit=crop' },
            { name: 'Salle de Brainstorming', capacity: 8, equipment: 'Tableau blanc, Post-it, WiFi', photo_url: 'https://images.unsplash.com/photo-1552664730-d307ca884978?w=400&h=300&fit=crop' }
        ];

        const insertRoom = db.prepare('INSERT INTO rooms (name, capacity, equipment, photo_url) VALUES (?, ?, ?, ?)');
        rooms.forEach(room => {
            insertRoom.run(room.name, room.capacity, room.equipment, room.photo_url);
        });
    }

    setInterval(() => {
        const now = new Date();
        const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000);

        const bookings = db.prepare(`
            SELECT b.id as booking_id, b.user_id, b.start_time, u.email, r.name as room_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN rooms r ON b.room_id = r.id
            WHERE b.start_time BETWEEN ? AND ?
            AND b.status = 'confirmed'
            AND NOT EXISTS (
                SELECT 1 FROM notifications n
                WHERE n.booking_id = b.id
                AND n.message LIKE '%approche%'
            )
        `).all(now.toISOString(), oneHourLater.toISOString());

        bookings.forEach(booking => {
            const message = `Votre réservation pour ${booking.room_name} approche (début à ${new Date(booking.start_time).toLocaleString('fr-CA')})`;
            db.prepare('INSERT INTO notifications (user_id, booking_id, message) VALUES (?, ?, ?)')
                .run(booking.user_id, booking.booking_id, message);
        });
    }, 300000);
}

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(session({
    secret: 'secret-key-reservation-app',
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false, maxAge: 24 * 60 * 60 * 1000 }
}));

const upload = multer({ dest: 'public/uploads/' });

app.use((req, res, next) => {
    res.locals.user = req.session.userId ? db.prepare('SELECT * FROM users WHERE id = ?').get(req.session.userId) : null;
    res.locals.notifications = req.session.userId ?
        db.prepare('SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC').all(req.session.userId) : [];
    next();
});

app.use('/public', express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
    if (req.session.userId) {
        res.redirect('/rooms');
    } else {
        res.redirect('/login');
    }
});

app.get('/login', (req, res) => {
    if (req.session.userId) {
        return res.redirect('/rooms');
    }
    res.sendFile(path.join(__dirname, 'views', 'login.html'));
});

app.get('/register', (req, res) => {
    if (req.session.userId) {
        return res.redirect('/rooms');
    }
    res.sendFile(path.join(__dirname, 'views', 'register.html'));
});

app.get('/rooms', requireAuth, (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'rooms.html'));
});

app.get('/bookings', requireAuth, (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'bookings.html'));
});

app.get('/room/:id', requireAuth, (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'room-calendar.html'));
});

app.get('/notifications', requireAuth, (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'notifications.html'));
});

app.get('/admin/dashboard', requireAdmin, (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'admin-dashboard.html'));
});

app.get('/admin/rooms', requireAdmin, (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'admin-rooms.html'));
});

app.get('/admin/users', requireAdmin, (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'admin-users.html'));
});

app.get('/admin/bookings', requireAdmin, (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'admin-bookings.html'));
});

app.get('/api/notifications', requireAuth, (req, res) => {
    const notifications = db.prepare('SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC').all(req.session.userId);
    res.json({ notifications });
});

app.post('/notifications/mark-all-read', requireAuth, (req, res) => {
    db.prepare('UPDATE notifications SET is_read = 1 WHERE user_id = ?').run(req.session.userId);
    res.json({ success: true });
});

app.use('/auth', require('./routes/auth'));
app.use('/rooms', require('./routes/rooms'));
app.use('/bookings', require('./routes/bookings'));
app.use('/admin', require('./routes/admin'));

app.post('/notifications/:id/read', requireAuth, (req, res) => {
    db.prepare('UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?')
        .run(req.params.id, req.session.userId);
    res.json({ success: true });
});

initDatabase();

app.listen(PORT, () => {
    console.log(`Serveur démarré sur http://localhost:${PORT}`);
    console.log(`Compte administrateur: admin@example.com / admin123`);
});

module.exports = { app, db, initDatabase };