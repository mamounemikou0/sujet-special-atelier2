# Dashboard administratif PME

Application web FastAPI + SQLite + HTML/CSS/JS vanilla.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Ouvrir : http://127.0.0.1:8000

## Comptes de test

- Admin : `admin@pme.local` / `admin123`
- Manager Tech : `marc@pme.local` / `manager123`
- Manager RH : `sofia@pme.local` / `manager123`
- Employé : `nina@pme.local` / `employee123`

## Fonctionnalités

- Connexion email + mot de passe
- Rôles : Employé, Manager, Admin
- Employé : profil, salaire, historique et demande de congés, upload photo
- Manager : équipe, salaires, approbation/refus des congés
- Admin : CRUD utilisateurs, rôles, salaires, photos, export CSV
- Statistiques admin : départements, total/moyenne salaires, congés
- Base SQLite `app.db`, créée automatiquement au premier lancement
- Uploads stockés dans `static/uploads`
