const Database = require('better-sqlite3');
const crypto = require('crypto');
const db = new Database('app.db');

// Activer les clés étrangères pour les suppressions en cascade
db.pragma('foreign_keys = ON');

// Création des tables
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user'
  );

  CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    equipment TEXT,
    photo_url TEXT
  );

  CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    start_hour INTEGER NOT NULL,
    FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(room_id, date, start_hour)
  );

  CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
  );
`);

// Fonction utilitaire pour hasher les mots de passe (SHA256 pour rester simple et robuste en natif)
const hashPassword = (password) => crypto.createHash('sha256').update(password).digest('hex');

// Seeding - Utilisateurs d'exemple (admin & user de test)
const userCount = db.prepare("SELECT COUNT(*) as count FROM users").get();
if (userCount.count === 0) {
    db.prepare("INSERT INTO users (email, password, role) VALUES (?, ?, ?)")
      .run('admin@example.com', hashPassword('admin123'), 'manager');
    db.prepare("INSERT INTO users (email, password, role) VALUES (?, ?, ?)")
      .run('user@example.com', hashPassword('user123'), 'user');
    console.log("👉 Base de données initialisée avec l'admin (admin@example.com / admin123)");
}

// Seeding - Salles d'exemple
const roomCount = db.prepare("SELECT COUNT(*) as count FROM rooms").get();
if (roomCount.count === 0) {
    const insertRoom = db.prepare("INSERT INTO rooms (name, capacity, equipment, photo_url) VALUES (?, ?, ?, ?)");
    insertRoom.run('Salle Turing', 10, 'Vidéoprojecteur, Tableau blanc, Climatisation', 'https://images.unsplash.com/photo-1517502884422-41eaaced0168?w=600');
    insertRoom.run('Salle Lovelace', 6, 'Écran 4K, Visio-conférence, Machine à café', 'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=600');
    insertRoom.run('Salle Hopper', 18, 'Grand écran, Microphones, Modularité totale', 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600');
    console.log("👉 3 Salles d'exemple injectées.");
}

module.exports = db;