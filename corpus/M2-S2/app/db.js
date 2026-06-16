const Database = require('better-sqlite3');
const bcrypt = require('bcryptjs');
const path = require('path');

const db = new Database(path.join(__dirname, 'app.db'));

// Enable WAL mode for better performance
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

function init() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      name TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'user',
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS rooms (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      capacity INTEGER NOT NULL,
      equipment TEXT NOT NULL DEFAULT '',
      photo_url TEXT NOT NULL DEFAULT '',
      active INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS reservations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      room_id INTEGER NOT NULL,
      user_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      hour INTEGER NOT NULL,
      title TEXT NOT NULL DEFAULT 'Réunion',
      status TEXT NOT NULL DEFAULT 'active',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (room_id) REFERENCES rooms(id),
      FOREIGN KEY (user_id) REFERENCES users(id),
      UNIQUE(room_id, date, hour)
    );

    CREATE TABLE IF NOT EXISTS notifications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      reservation_id INTEGER,
      message TEXT NOT NULL,
      read INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (user_id) REFERENCES users(id)
    );
  `);

  // Seed admin if not exists
  const admin = db.prepare('SELECT id FROM users WHERE email = ?').get('admin@example.com');
  if (!admin) {
    const hash = bcrypt.hashSync('admin1234', 10);
    db.prepare(`INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)`).run(
      'admin@example.com', hash, 'Administrateur', 'gestionnaire'
    );
  }

  // Seed rooms if empty
  const roomCount = db.prepare('SELECT COUNT(*) as c FROM rooms').get().c;
  if (roomCount === 0) {
    const insertRoom = db.prepare(`INSERT INTO rooms (name, capacity, equipment, photo_url) VALUES (?, ?, ?, ?)`);
    insertRoom.run('Salle Horizon', 10, 'Projecteur, Tableau blanc, Visioconférence, Climatisation', 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80');
    insertRoom.run('Salle Zénith', 6, 'Écran TV 65", Tableau blanc, WiFi renforcé', 'https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=800&q=80');
    insertRoom.run('Salle Atrium', 20, 'Scène, Sono, Projecteur HD, Caméra, Climatisation', 'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=800&q=80');
  }
}

init();

module.exports = db;
