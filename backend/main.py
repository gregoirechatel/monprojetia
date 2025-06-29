from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import requests

# Initialisation FastAPI
app = FastAPI()

# Fichiers statiques et templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Récupération de la clé API depuis la variable d'environnement
API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Accueil
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Formulaire
@app.get("/formulaire", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

# Traitement du formulaire
@app.post("/planning", response_class=HTMLResponse)
async def generate_planning(
    request: Request,
    objectif: str = Form(...),
    age: int = Form(...),
    poids: float = Form(...),
    taille: int = Form(...),
    sexe: str = Form(...),
    activite: str = Form(...)
):
    prompt = f"""
Tu es un expert en nutrition. Crée un planning nutritionnel hebdomadaire pour :
- Objectif : {objectif}
- Âge : {age} ans
- Poids : {poids} kg
- Taille : {taille} cm
- Sexe : {sexe}
- Niveau d’activité : {activite}

Le planning doit contenir des repas simples, équilibrés et adaptés à cet utilisateur.
Structure-le par jour (lundi à dimanche), avec matin / midi / soir, et donne des grammages approximatifs.
"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "anthropic/claude-3-haiku",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        result = f"Erreur lors de l’appel à l’API OpenRouter : {e}"

    return templates.TemplateResponse("planning.html", {
        "request": request,
        "planning": result
    })
