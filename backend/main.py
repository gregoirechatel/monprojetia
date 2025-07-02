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

# Page d'accueil
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Formulaire
@app.get("/formulaire", response_class=HTMLResponse)
async def formulaire(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

# Génération complète du planning (7 requêtes)
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

    # Sauvegarde du planning
    with open("backend/data/planning.json", "w", encoding="utf-8") as f:
        json.dump({"plannings": plannings}, f, ensure_ascii=False, indent=2)

    # Génération de la liste de courses globale
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

    return RedirectResponse(url="/planning", status_code=303)

# Re-générer une journée spécifique
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

# Page planning
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

# Page liste de courses
@app.get("/liste", response_class=HTMLResponse)
async def afficher_liste(request: Request):
    try:
        with open("backend/data/liste.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        liste = data["liste"]
    except:
        liste = "Aucune liste trouvée."

    return templates.TemplateResponse("liste.html", {"request": request, "liste": liste})
