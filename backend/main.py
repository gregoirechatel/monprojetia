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


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generer", response_class=HTMLResponse)
async def generer(
    request: Request,
    objectif: str = Form(...),
    age: int = Form(...),
    poids: float = Form(...),
    taille: int = Form(...),
    sexe: str = Form(...),
    activite: str = Form(...),
    email: str = Form(...),
    contraintes: str = Form(...)
):
    prompt = (
        f"Tu es un expert en nutrition et sport. Génère :\n"
        f"1. Un planning nutritionnel simple, clair et complet pour 7 jours, avec 3 repas par jour et les grammages précis. "
        f"2. Une liste de courses associée avec les quantités exactes à acheter.\n"
        f"3. Un planning d'entraînement hebdomadaire adapté à l’objectif ({objectif}), à une personne de {age} ans, "
        f"{poids} kg, {taille} cm, sexe {sexe}, activité : {activite}, contraintes : {contraintes}.\n"
        f"Rends le tout structuré, lisible, concret et réalisable pour un utilisateur lambda."
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

        # Extraction manuelle (simplifiée ici pour test)
        parts = contenu.split("Liste de courses")
        planning = parts[0].strip()
        liste_part = parts[1] if len(parts) > 1 else "Liste de courses indisponible"

        if "Planning d'entraînement" in liste_part:
            liste, training = liste_part.split("Planning d'entraînement", 1)
            liste = "Liste de courses" + liste.strip()
            training = "Planning d'entraînement" + training.strip()
        else:
            liste = "Liste de courses" + liste_part.strip()
            training = "Planning d'entraînement indisponible"

        # Sauvegardes
        with open("backend/data/planning.json", "w", encoding="utf-8") as f:
            json.dump({"planning": planning}, f, ensure_ascii=False, indent=2)

        with open("backend/data/liste.json", "w", encoding="utf-8") as f:
            json.dump({"liste": liste}, f, ensure_ascii=False, indent=2)

        with open("backend/data/training.json", "w", encoding="utf-8") as f:
            json.dump({"training": training}, f, ensure_ascii=False, indent=2)

        return templates.TemplateResponse("planning.html", {"request": request, "planning": planning})

    except Exception as e:
        return templates.TemplateResponse("planning.html", {
            "request": request,
            "planning": f"Erreur lors de l’appel à l’IA : {str(e)}"
        })


@app.get("/planning", response_class=HTMLResponse)
async def afficher_planning(request: Request):
    try:
        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            planning = json.load(f)["planning"]
    except:
        planning = "Aucun planning trouvé. Veuillez d'abord en générer un."

    return templates.TemplateResponse("planning.html", {"request": request, "planning": planning})


@app.get("/liste", response_class=HTMLResponse)
async def afficher_liste(request: Request):
    try:
        with open("backend/data/liste.json", "r", encoding="utf-8") as f:
            liste = json.load(f)["liste"]
    except:
        liste = "Aucune liste trouvée. Veuillez d'abord générer un planning."

    return templates.TemplateResponse("liste.html", {"request": request, "liste": liste})


@app.get("/training", response_class=HTMLResponse)
async def afficher_training(request: Request):
    try:
        with open("backend/data/training.json", "r", encoding="utf-8") as f:
            training = json.load(f)["training"]
    except:
        training = "Aucun programme d'entraînement trouvé. Veuillez d'abord générer un planning."

    return templates.TemplateResponse("training.html", {"request": request, "training": training})
