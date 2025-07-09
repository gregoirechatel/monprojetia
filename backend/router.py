import os
import json
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DATA_DIR = "backend/data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Accueil avec choix
@router.get("/", response_class=HTMLResponse)
async def welcome_page(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

# Page d'inscription
@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
async def register_post(request: Request, email: str = Form(...), password: str = Form(...)):
    os.makedirs(DATA_DIR, exist_ok=True)
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)

    if email in users:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email déjà utilisé."})

    users[email] = password
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

    user_dir = os.path.join(DATA_DIR, "utilisateurs", email)
    os.makedirs(user_dir, exist_ok=True)

    response = RedirectResponse(url="/login", status_code=303)
    return response

# Page de connexion
@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    if not os.path.exists(USERS_FILE):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Aucun compte trouvé."})

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)

    if email not in users or users[email] != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Identifiants invalides."})

    # ✅ On mémorise l'utilisateur connecté
    with open(os.path.join(DATA_DIR, "session.json"), "w", encoding="utf-8") as f:
        json.dump({"email": email}, f)

    # Utilisateur connecté → redirection vers vraie page d'accueil
    return RedirectResponse(url="/accueil", status_code=303)
