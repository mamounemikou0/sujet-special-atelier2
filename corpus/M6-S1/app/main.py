from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from models import init_db
from routes import auth, profile, users

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="CHANGE_ME_SECRET_KEY")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    user_id = request.session.get("user_id")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user_id": user_id},
    )


app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(users.router)
