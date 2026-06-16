# UserHub — Application de gestion d'utilisateurs

Application web complète de gestion d'utilisateurs construite avec **FastAPI**, **SQLite** et **HTML/CSS/JS vanilla**.

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python 3.11 + FastAPI |
| Base de données | SQLite (`app.db`) |
| ORM | SQLAlchemy 2.0 |
| Auth | Sessions (itsdangerous) + bcrypt |
| Frontend | HTML + CSS + JavaScript vanilla |
| Templates | Jinja2 |

## Structure des fichiers

```
app/
├── main.py              # Point d'entrée FastAPI
├── models.py            # Modèles SQLAlchemy + configuration BDD
├── requirements.txt     # Dépendances Python
├── README.md
├── routes/
│   ├── __init__.py
│   ├── auth.py          # Inscription, connexion, déconnexion
│   └── users.py         # Dashboard, profil, suppression
├── templates/
│   ├── base.html        # Layout de base
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html   # Liste des utilisateurs
│   ├── profile.html     # Modification du profil
│   └── view_profile.html
└── static/
    ├── css/style.css
    └── js/app.js
```

## Installation & lancement

### 1. Créer un environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate      # Linux / macOS
# ou
venv\Scripts\activate         # Windows
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Lancer l'application

```bash
uvicorn main:app --reload
```

L'application sera disponible sur : **http://127.0.0.1:8000**

## Compte administrateur par défaut

Au premier lancement, un compte admin est créé automatiquement :

| Champ | Valeur |
|-------|--------|
| Nom d'utilisateur | `admin` |
| Mot de passe | `admin1234` |

> ⚠️ **Changez ce mot de passe en production !**

## Fonctionnalités

| Fonctionnalité | Utilisateur | Admin |
|----------------|-------------|-------|
| Inscription | ✅ | — |
| Connexion / Déconnexion | ✅ | ✅ |
| Voir la liste des utilisateurs | ✅ | ✅ |
| Modifier son propre profil | ✅ | ✅ |
| Changer son mot de passe | ✅ | ✅ |
| Supprimer son propre compte | ✅ | — |
| Voir le profil de n'importe quel utilisateur | ❌ | ✅ |
| Supprimer n'importe quel compte | ❌ | ✅ |

## Sécurité

- Les mots de passe sont hachés avec **bcrypt**
- Les sessions sont signées avec `itsdangerous`
- La clé secrète de session est dans `main.py` — **à remplacer en production** par une vraie valeur aléatoire

## Production

Pour un déploiement en production, pensez à :

1. Remplacer la clé secrète de session dans `main.py`
2. Utiliser une base de données PostgreSQL ou MySQL
3. Activer HTTPS
4. Lancer avec Gunicorn : `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`
