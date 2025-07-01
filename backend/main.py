import os
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
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

# Page d'accueil
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Nouvelle route : affichage du formulaire depuis le bouton accueil
@app.get("/formulaire", response_class=HTMLResponse)
async def show_formulaire(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

# Traitement du formulaire
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
    prompt = (
        f"Tu es un expert en nutrition. Génére un planning nutritionnel simple, complet, avec grammages précis, "
        f"matin-midi-soir pour 7 jours pour une personne de {age} ans, {poids} kg, {taille} cm, sexe {sexe}, "
        f"objectif : {objectif}, activité : {activite}. Donne aussi la liste de courses correspondante avec grammages."
    )

    data = {
        "model": "anthropic/claude-3-haiku",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
        result = response.json()

        contenu = result["choices"][0]["message"]["content"]

        if "Liste de courses" in contenu:
            parts = contenu.split("Liste de courses")
            planning = parts[0].strip()
            liste_courses = "Liste de courses" + parts[1].strip()
        else:
            planning = contenu
            liste_courses = "Liste indisponible"

        with open("backend/data/planning.json", "w", encoding="utf-8") as f:
            json.dump({"planning": planning}, f, ensure_ascii=False, indent=2)

        with open("backend/data/liste.json", "w", encoding="utf-8") as f:
            json.dump({"liste": liste_courses}, f, ensure_ascii=False, indent=2)

        return templates.TemplateResponse("planning.html", {"request": request, "planning": planning})

    except Exception as e:
        return templates.TemplateResponse("planning.html", {
            "request": request,
            "planning": f"Erreur lors de l’appel à l’IA : {str(e)}"
        })

# Page planning
@app.get("/planning", response_class=HTMLResponse)
async def afficher_planning(request: Request):
    try:
        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        planning = data["planning"]
    except:
        planning = "Aucun planning trouvé. Veuillez d'abord en générer un."

    return templates.TemplateResponse("planning.html", {"request": request, "planning": planning})

# Page liste de courses
@app.get("/liste", response_class=HTMLResponse)
async def afficher_liste(request: Request):
    try:
        with open("backend/data/liste.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        liste = data["liste"]
    except:
        liste = "Aucune liste trouvée. Veuillez d'abord générer un planning."

    return templates.TemplateResponse("liste.html", {"request": request, "liste": liste})
