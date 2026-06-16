# RoomBook – Application de réservation de salles de réunion

Application web complète de gestion et réservation de salles de réunion.

## Stack technique

- **Backend** : Node.js + Express.js
- **Base de données** : SQLite (fichier `app.db`, via `better-sqlite3`)
- **Frontend** : HTML + CSS + JavaScript vanilla (pas de framework)
- **Sessions** : `express-session` + `connect-sqlite3`
- **Authentification** : `bcryptjs` (hash des mots de passe)

## Installation et démarrage

```bash
npm install
node server.js
```

Ouvrez ensuite http://localhost:3000

## Comptes de démonstration

| Rôle         | Email                 | Mot de passe |
|--------------|-----------------------|--------------|
| Gestionnaire | admin@example.com     | admin1234    |
| Utilisateur  | (créez via /register) | —            |

## Fonctionnalités

### Utilisateur
- Inscription / connexion avec email + mot de passe
- Consultation des salles disponibles (nom, capacité, équipements, photo)
- Calendrier hebdomadaire par salle (créneaux d'1 heure, 8h–19h)
- Création d'une réservation en cliquant sur un créneau libre
- Modification et annulation de ses propres réservations
- Visualisation des réservations existantes (qui a réservé, quand)
- Notifications simulées en base de données (rappel 24h avant)

### Gestionnaire (admin)
- Toutes les fonctionnalités utilisateur
- Ajout / modification / suppression de salles
- Annulation de n'importe quelle réservation
- Tableau de bord : taux d'occupation par salle, toutes les réservations, top utilisateurs
- Filtrage des réservations par date et par salle

## Structure du projet

```
app/
├── server.js              # Point d'entrée
├── db.js                  # Initialisation SQLite + seed
├── middleware.js           # requireAuth, requireManager
├── routes/
│   ├── auth.js            # /login, /register, /logout
│   ├── rooms.js           # /rooms + gestion gestionnaire
│   ├── reservations.js    # /reservations
│   ├── api.js             # /api/* (JSON)
│   └── dashboard.js       # /dashboard
├── views/                 # Pages HTML
│   ├── login.html
│   ├── register.html
│   ├── rooms.html
│   ├── room-detail.html
│   ├── room-form.html
│   ├── reservations.html
│   ├── reservation-form.html
│   └── dashboard.html
├── public/
│   ├── css/style.css
│   └── js/layout.js       # Navigation partagée
├── package.json
└── README.md
```

## Base de données

Tables SQLite créées automatiquement au démarrage :
- `users` – utilisateurs (id, email, password, name, role)
- `rooms` – salles (id, name, capacity, equipment, photo_url, active)
- `reservations` – réservations (id, room_id, user_id, date, hour, title, status)
- `notifications` – notifications (id, user_id, reservation_id, message, read)

## Notifications

Un job tourne toutes les 5 minutes et insère automatiquement une notification en base pour toute réservation ayant lieu dans moins de 24h. Les notifications sont visibles via l'icône 🔔 dans la barre de navigation.

## Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| PORT     | 3000   | Port du serveur |
