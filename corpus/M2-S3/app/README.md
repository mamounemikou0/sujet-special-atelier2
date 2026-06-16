# ✦ Boutique — E-commerce App

Application e-commerce complète construite avec **FastAPI + SQLite + Vanilla JS**.

## Installation

```bash
cd shop
pip install -r requirements.txt
uvicorn main:app --reload
```

Ouvrez http://localhost:8000

## Comptes par défaut

| Rôle  | Email            | Mot de passe |
|-------|------------------|--------------|
| Admin | admin@shop.com   | admin123     |

## Fonctionnalités

- 🛍 Catalogue de produits avec recherche et filtre par catégorie
- 👤 Inscription / Connexion (JWT via cookie httponly)
- 🛒 Panier (ajout, suppression, quantité)
- 💳 Passage de commande avec simulation de paiement
- 📋 Historique des commandes client
- ⚙️ Espace admin : gestion produits & commandes

## Structure

```
shop/
├── main.py           # Entrée app + seed
├── models.py         # Modèles SQLAlchemy
├── database.py       # Connexion SQLite
├── auth.py           # JWT + bcrypt
├── routes/
│   ├── auth_routes.py
│   ├── product_routes.py
│   ├── cart_routes.py
│   └── order_routes.py
├── templates/
│   └── index.html    # SPA unique
├── static/
│   ├── css/style.css
│   └── js/app.js
└── requirements.txt
```

## Notes

- La base de données `app.db` est créée automatiquement au démarrage
- 5 produits d'exemple + 1 admin injectés si absents
- Le paiement est **simulatif** — aucun traitement réel
