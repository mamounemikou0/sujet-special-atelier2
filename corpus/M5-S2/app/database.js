const Database = require('better-sqlite3');
const bcrypt = require('bcryptjs');
const path = require('path');

let db;

function getDatabase() {
  if (!db) {
    db = new Database('app.db');
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
  }
  return db;
}

function initDatabase() {
  const db = getDatabase();

  // Create tables
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      name TEXT NOT NULL,
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
      room_id INTEGER NOT NULL,
      user_id INTEGER NOT NULL,
      date DATE NOT NULL,
      start_time TIME NOT NULL,
      end_time TIME NOT NULL,
      title TEXT,
      status TEXT DEFAULT 'confirmed',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS notifications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      booking_id INTEGER NOT NULL,
      message TEXT NOT NULL,
      is_read BOOLEAN DEFAULT 0,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
    );
  `);

  // Insert default data if not exists
  const adminExists = db.prepare('SELECT id FROM users WHERE email = ?').get('admin@example.com');
  if (!adminExists) {
    const hashedPassword = bcrypt.hashSync('admin123', 10);
    db.prepare('INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)').run(
      'admin@example.com', hashedPassword, 'Administrateur', 'admin'
    );
  }

  const roomsCount = db.prepare('SELECT COUNT(*) as count FROM rooms').get();
  if (roomsCount.count === 0) {
    const insertRoom = db.prepare('INSERT INTO rooms (name, capacity, equipment, photo_url) VALUES (?, ?, ?, ?)');
    insertRoom.run('Salle A - Paris', 10, 'Vidéo-projecteur, Tableau blanc, Wi-Fi', 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=500');
    insertRoom.run('Salle B - Lyon', 20, 'Écran TV, Visioconférence, Paperboard', 'https://images.unsplash.com/photo-1497366754270-5b50d0a5c4ab?w=500');
    insertRoom.run('Salle C - Marseille', 6, 'Tableau blanc, Wi-Fi', 'https://images.unsplash.com/photo-1577412647305-991150c7d163?w=500');
  }
}

module.exports = { getDatabase, initDatabase };