from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from database import init_db
from routes import auth_routes, employee_routes, manager_routes, admin_routes

app = FastAPI(title="HR Dashboard", version="1.0.0")

# Static files
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_routes.router)
app.include_router(employee_routes.router)
app.include_router(manager_routes.router)
app.include_router(admin_routes.router)


@app.on_event("startup")
def on_startup():
    init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
