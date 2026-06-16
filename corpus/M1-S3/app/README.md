# MiniShop - petite e-boutique FastAPI

Application web complète en Python 3.11 + FastAPI + SQLite + HTML/CSS/JavaScript vanilla.

## Lancement

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Ouvre ensuite : http://127.0.0.1:8000

## Comptes

Compte admin créé automatiquement au démarrage :

- Email : `admin@example.com`
- Mot de passe : `admin1234`

## Fonctionnalités

- Catalogue produits avec nom, description, prix, stock, image URL et catégorie
- Recherche par nom et filtre par catégorie
- Inscription, connexion et adresse de livraison
- Panier : ajout, suppression, modification de quantité
- Checkout avec récapitulatif et faux numéro de carte à 16 chiffres
- Création de commande et décrément du stock
- Historique des commandes client
- Admin : CRUD produits, consultation des commandes, changement de statut

## Base de données

La base SQLite `app.db` est créée automatiquement au premier lancement.
Cinq produits d'exemple sont injectés si le catalogue est vide.
