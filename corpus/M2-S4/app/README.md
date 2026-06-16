# HR Dashboard — Tableau de bord RH

Application web de gestion RH pour PME, construite avec **FastAPI + SQLite + Vanilla JS**.

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.11 + FastAPI |
| Base de données | SQLite (`app.db`) |
| ORM | SQLAlchemy 2.0 |
| Auth | JWT (cookies httponly) + bcrypt |
| Frontend | HTML + CSS + JavaScript vanilla |
| Templates | Jinja2 |

## Installation

```bash
# 1. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
uvicorn main:app --reload
```

L'application sera accessible sur **http://localhost:8000**

La base de données est initialisée automatiquement au premier démarrage.

## Comptes de démonstration

| Rôle     | Email                   | Mot de passe  |
|----------|-------------------------|---------------|
| Admin    | admin@company.com       | admin123      |
| Manager  | manager1@company.com    | manager123    |
| Manager  | manager2@company.com    | manager123    |
| Employé  | emp1@company.com        | emp123        |
| Employé  | emp2@company.com        | emp123        |
| Employé  | emp3@company.com        | emp123        |
| Employé  | emp4@company.com        | emp123        |
| Employé  | emp5@company.com        | emp123        |

## Fonctionnalités

### Vue Employé
- Voir son profil (nom, poste, département, manager, date d'embauche)
- Voir son salaire avec estimation du net
- Upload de photo de profil
- Historique des demandes de congés
- Soumettre une nouvelle demande de congé

### Vue Manager
- Tableau de bord avec demandes en attente
- Approuver / Refuser les congés de son équipe
- Voir les salaires et informations de l'équipe

### Vue Admin
- Tableau de bord global (stats, utilisateurs récents)
- CRUD complet sur les utilisateurs (créer, modifier, supprimer)
- Changer de rôle à n'importe quel utilisateur
- Upload de photo de profil pour n'importe quel utilisateur
- Voir tous les salaires par département
- Exporter la liste des employés en CSV
- Page statistiques : effectifs/salaires par département, état des congés

## Structure des fichiers

```
hr_dashboard/
├── main.py              # Entrée FastAPI
├── models.py            # Modèles SQLAlchemy
├── database.py          # Session DB + seed
├── auth.py              # JWT helpers
├── routes/
│   ├── auth_routes.py   # Login / logout
│   ├── employee_routes.py
│   ├── manager_routes.py
│   └── admin_routes.py
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── employee/
│   ├── manager/
│   └── admin/
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── uploads/         # Photos de profil
├── requirements.txt
└── README.md
```

## Sécurité (production)

- Changer `SECRET_KEY` dans `auth.py`
- Passer HTTPS pour les cookies httponly
- Remplacer SQLite par PostgreSQL
