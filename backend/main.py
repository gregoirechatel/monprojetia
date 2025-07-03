import os
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import requests

load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}
CLAUDE_URL = "https://openrouter.ai/api/v1/chat/completions"
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/formulaire", response_class=HTMLResponse)
async def formulaire(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

@app.post("/generer", response_class=HTMLResponse)
async def generer(
    request: Request,
    objectif: str = Form(...),
    age: int = Form(...),
    poids: float = Form(...),
    taille: int = Form(...),
    sexe: str = Form(...),
    activite: str = Form(...),
    email: str = Form(...)
):
    plannings = {}
    full_text = ""

    for jour in JOURS:
        prompt = (
            f"Tu es un expert en nutrition. Génère uniquement le planning nutritionnel pour {jour} : "
            f"3 repas (matin, midi, soir) avec des plats simples, équilibrés et les grammages. "
            f"Profil : {age} ans, {poids} kg, {taille} cm, sexe : {sexe}, objectif : {objectif}, activité : {activite}."
        )
        data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
        try:
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            result = response.json()
            contenu = result["choices"][0]["message"]["content"]
            plannings[jour] = contenu
            full_text += contenu + "\n"
        except:
            plannings[jour] = f"Erreur lors de la génération de {jour}."

    # Sauvegarde du planning nutritionnel
    with open("backend/data/planning.json", "w", encoding="utf-8") as f:
        json.dump({"plannings": plannings}, f, ensure_ascii=False, indent=2)

    # Génération de la liste de courses
    liste_prompt = (
        f"Génère la liste complète de courses pour les 7 jours de repas générés. "
        f"Profil : {age} ans, {poids} kg, {taille} cm, sexe : {sexe}, objectif : {objectif}, activité : {activite}. "
        f"Base-toi sur ce planning :\n{full_text}"
    )
    data_courses = {
        "model": "anthropic/claude-3-haiku",
        "messages": [{"role": "user", "content": liste_prompt}]
    }

    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_courses)
        result = response.json()
        liste = result["choices"][0]["message"]["content"]
    except:
        liste = "Erreur lors de la génération de la liste."

    with open("backend/data/liste.json", "w", encoding="utf-8") as f:
        json.dump({"liste": liste}, f, ensure_ascii=False, indent=2)

    # Génération du planning d'entraînement
    sport_prompt = (
        f"Tu es un coach sportif. Propose un planning d'entraînement pour 7 jours (1 jour de repos), "
        f"adapté au profil : {age} ans, {poids} kg, {taille} cm, sexe : {sexe}, objectif : {objectif}, activité : {activite}. "
        f"Ce planning doit être cohérent avec la nutrition hebdomadaire ci-dessous :\n{full_text}"
    )
    data_sport = {
        "model": "anthropic/claude-3-haiku",
        "messages": [{"role": "user", "content": sport_prompt}]
    }

    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_sport)
        result = response.json()
        training = result["choices"][0]["message"]["content"]
    except:
        training = "Erreur lors de la génération du planning sportif."

    with open("backend/data/training.json", "w", encoding="utf-8") as f:
        json.dump({"training": training}, f, ensure_ascii=False, indent=2)

    return RedirectResponse(url="/planning", status_code=303)

@app.get("/regenerer/{jour}", response_class=HTMLResponse)
async def regenerer_jour(request: Request, jour: str):
    if jour not in JOURS:
        return RedirectResponse(url="/planning", status_code=303)

    try:
        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {"plannings": {}}

    prompt = (
        f"Tu es un expert en nutrition. Génère uniquement le planning nutritionnel pour {jour} : "
        f"3 repas (matin, midi, soir) équilibrés avec les grammages, pour un profil standard actif."
    )
    data_api = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}

    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_api)
        result = response.json()
        contenu = result["choices"][0]["message"]["content"]
        data["plannings"][jour] = contenu
    except:
        data["plannings"][jour] = f"Erreur lors de la régénération de {jour}."

    with open("backend/data/planning.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return RedirectResponse(url="/planning", status_code=303)

@app.get("/planning", response_class=HTMLResponse)
async def afficher_planning(request: Request):
    try:
        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        plannings = data["plannings"]
    except:
        plannings = {}

    return templates.TemplateResponse("planning.html", {
        "request": request,
        "plannings": plannings
    })

@app.get("/liste", response_class=HTMLResponse)
async def afficher_liste(request: Request):
    try:
        with open("backend/data/liste.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        liste = data["liste"]
    except:
        liste = "Aucune liste trouvée."

    return templates.TemplateResponse("liste.html", {"request": request, "liste": liste})

@app.get("/training", response_class=HTMLResponse)
async def afficher_training(request: Request):
    try:
        with open("backend/data/training.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        training = data["training"]
    except:
        training = "Aucun planning d'entraînement trouvé."

    return templates.TemplateResponse("training.html", {"request": request, "training": training})
