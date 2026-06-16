# Mini e-boutique FastAPI

Petite application de boutique en ligne avec FastAPI, SQLite et frontend HTML/CSS/JS vanilla.

## Stack

- Backend : Python 3.11 + FastAPI
- Base de données : SQLite (`app.db`)
- Frontend : HTML + CSS + JavaScript vanilla
- Lancement : `uvicorn main:app --reload`

## Installation

```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
uvicorn main:app --reload
