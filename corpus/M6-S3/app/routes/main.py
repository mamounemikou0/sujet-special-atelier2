from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from models import create_db_and_seed
from routes import auth, shop, admin

app = FastAPI(title="Mini e-boutique")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(shop.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup():
    create_db_and_seed()
