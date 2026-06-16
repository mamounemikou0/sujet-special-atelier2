# Roomly — réservation de salles de réunion

Application web classique rendue côté serveur, réalisée avec **Node.js + Express**, **SQLite via better-sqlite3**, et **HTML/CSS/JavaScript vanilla**.

## Fonctionnalités

- Inscription et connexion par email/mot de passe ; mots de passe hachés avec `bcryptjs`.
- Liste des salles avec capacité, équipements et photo.
- Calendrier journalier par salle, avec créneaux fixes d'une heure de 08:00 à 18:00.
- Création, modification et annulation de ses propres réservations.
- Affichage de l'utilisateur ayant réservé chaque créneau.
- Rôle gestionnaire : CRUD des salles, annulation de toute réservation et tableau de bord d'occupation à 30 jours.
- Notifications simulées stockées en base pour les réservations démarrant dans les prochaines 24 heures.
- Protection CSRF simple sur tous les formulaires modifiant les données.

## Pré-requis

- Node.js 22 ou version ultérieure.
- npm.

## Installation et lancement

```bash
npm install
node server.js
```

Ouvrez ensuite `http://localhost:3000`.

Le fichier SQLite `app.db` est créé automatiquement à la racine du projet au premier lancement.

## Données initiales automatiques

Trois salles sont créées au premier lancement : **Salle Horizon**, **Salle Atlas** et **Salle Nova**.

Compte gestionnaire de démonstration :

- Email : `admin@example.com`
- Mot de passe : `Admin123!`

Changez ce mot de passe et la variable `SESSION_SECRET` avant tout usage réel.

## Configuration optionnelle

```bash
PORT=3000 SESSION_SECRET="une-cle-longue-et-secrete" node server.js
```

## Structure

```text
meeting-room-booking/
├── server.js
├── db.js
├── middleware.js
├── view-engine.js
├── package.json
├── routes/
│   ├── auth.js
│   ├── bookings.js
│   ├── manager.js
│   ├── notifications.js
│   └── rooms.js
├── views/
│   ├── layout.html
│   ├── login.html
│   ├── register.html
│   ├── rooms.html
│   ├── calendar.html
│   ├── my-bookings.html
│   ├── edit-booking.html
│   ├── notifications.html
│   ├── dashboard.html
│   ├── manage-rooms.html
│   └── room-form.html
└── public/
    ├── styles.css
    └── app.js
```

## Modèle de données

- `users` : comptes et rôle (`user` ou `manager`).
- `rooms` : salles réservables.
- `reservations` : créneaux avec unicité `(room_id, start_time)` empêchant les doubles réservations.
- `notifications` : rappels simulés, uniques par réservation et type.

## Utilisation gestionnaire

Connectez-vous avec le compte gestionnaire, puis ouvrez **Gestionnaire** dans la barre de navigation. Le tableau de bord calcule l'occupation sur les 30 jours calendaires à venir, sur une base de 10 créneaux disponibles par jour et par salle.

## Notes de production

Cette application est conçue comme une base pédagogique complète. Pour un déploiement réel, utilisez un stockage de sessions persistant, imposez HTTPS avec cookies `secure`, fournissez un secret de session robuste, appliquez une politique de mots de passe adaptée et hébergez les images sur une source maîtrisée.
