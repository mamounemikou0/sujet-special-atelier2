# Système ERP Simplifié - Dashboard PME

Application web de gestion des ressources humaines et des demandes de congés bâtie sur FastAPI, SQL Alchemy et SQLite.

## Installation & Lancement

1. S'assurer de disposer de Python 3.11+.
2. Installer les paquets requis :
   ```bash
   pip install -r requirements.txt

   uvicorn main:app --reload


   ### Instructions pour tester immédiatement :
1. Crée ton dossier de projet.
2. Écris ces fichiers exactement comme indiqué.
3. Lance la commande `uvicorn main:app --reload` dans ton terminal. 
4. Ouvre `http://127.0.0.1:8000`. La base de données `app.db` se créera automatiquement au premier démarrage avec les utilisateurs demandés (1 admin, 2 managers, 5 employés).