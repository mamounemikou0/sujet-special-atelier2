const path = require('path');
const Database = require('better-sqlite3');
const bcrypt = require('bcryptjs');

const db = new Database(path.join(__dirname, 'app.db'));
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

function initDatabase() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT NOT NULL UNIQUE COLLATE NOCASE,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user', 'manager')),
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS rooms (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      capacity INTEGER NOT NULL CHECK(capacity > 0),
      equipment TEXT NOT NULL DEFAULT '',
      photo_url TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS reservations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      start_time TEXT NOT NULL,
      end_time TEXT NOT NULL,
      purpose TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      CHECK(end_time > start_time),
      UNIQUE(room_id, start_time)
    );
    CREATE TABLE IF NOT EXISTS notifications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      reservation_id INTEGER NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
      type TEXT NOT NULL,
      message TEXT NOT NULL,
      is_read INTEGER NOT NULL DEFAULT 0 CHECK(is_read IN (0, 1)),
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, reservation_id, type)
    );
    CREATE INDEX IF NOT EXISTS idx_reservations_start ON reservations(start_time);
    CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
  `);

  const manager = db.prepare('SELECT id FROM users WHERE email = ?').get('admin@example.com');
  if (!manager) {
    db.prepare('INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)')
      .run('admin@example.com', bcrypt.hashSync('Admin123!', 12), 'manager');
  }

  const roomCount = db.prepare('SELECT COUNT(*) AS total FROM rooms').get().total;
  if (roomCount === 0) {
    const insert = db.prepare('INSERT INTO rooms (name, capacity, equipment, photo_url) VALUES (?, ?, ?, ?)');
    const seed = db.transaction(() => {
      insert.run('Salle Horizon', 8, 'Écran 4K, visioconférence, tableau blanc', 'https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=900&q=80');
      insert.run('Salle Atlas', 14, 'Projecteur, visioconférence, paperboard', 'https://images.unsplash.com/photo-1517502884422-41eaead166d4?auto=format&fit=crop&w=900&q=80');
      insert.run('Salle Nova', 4, 'TV, câble HDMI, tableau blanc', 'https://images.unsplash.com/photo-1497366412874-3415097a27e7?auto=format&fit=crop&w=900&q=80');
    });
    seed();
  }
}

function createUpcomingNotifications() {
  db.prepare(`
    INSERT OR IGNORE INTO notifications (user_id, reservation_id, type, message)
    SELECT r.user_id, r.id, 'UPCOMING',
           'Votre réservation de la salle ' || rooms.name || ' commence le ' || replace(r.start_time, 'T', ' à ') || '.'
    FROM reservations r
    JOIN rooms ON rooms.id = r.room_id
    WHERE datetime(r.start_time) > datetime('now', 'localtime')
      AND datetime(r.start_time) <= datetime('now', 'localtime', '+24 hours')
  `).run();
}

module.exports = { db, initDatabase, createUpcomingNotifications };
