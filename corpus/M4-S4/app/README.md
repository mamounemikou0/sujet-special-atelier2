# Tableau de bord administratif pour PME

Une application web pour gérer les employés, les congés et les salaires d'une PME.

## Prérequis

- Python 3.11
- pip

## Installation

1. Cloner le dépôt ou copier les fichiers.
2. Créer un environnement virtuel :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   venv\Scripts\activate  # Sur Windows


   Installer les dépendances :
bash
Copier

pip install -r requirements.txt




Lancer l'application :
bash
Copier

uvicorn main\:app --reload


Accéder à l'application : http://localhost:8000
Utiliser les identifiants suivants pour tester :

Admin : admin@pme.com / admin123
Manager 1 : manager1@pme.com / manager123
Manager 2 : manager2@pme.com / manager123
Employé 1 : employee1@pme.com / employee123
Employé 2 : employee2@pme.com / employee123
Employé 3 : employee3@pme.com / employee123
Employé 4 : employee4@pme.com / employee123
Employé 5 : employee5@pme.com / employee123




