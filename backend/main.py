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

# Formulaire
@app.get("/formulaire", response_class=HTMLResponse)
async def formulaire(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

# Traitement du formulaire et génération IA
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
        f"Tu es un expert en nutrition et sport. Génére un planning nutritionnel HEBDOMADAIRE (7 jours), "
        f"avec 3 repas par jour (matin, midi, soir), simples, équilibrés, bien formatés, et avec les grammages. "
        f"Profil utilisateur : {age} ans, {poids} kg, {taille} cm, sexe : {sexe}, objectif : {objectif}, activité : {activite}. "
        f"Ensuite, génère une liste de courses pour la semaine avec quantités précises. "
        f"Enfin, génère un planning sportif HEBDOMADAIRE (7 jours, 1 jour de repos), cohérent avec la nutrition et l’objectif."
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

        # Extraction des blocs
        planning = "Aucun planning généré"
        liste = "Aucune liste générée"
        training = "Aucun programme généré"

        if "Liste de courses" in contenu:
            parts = contenu.split("Liste de courses")
            planning = parts[0].strip()
            if "Planning sportif" in parts[1]:
                liste_part, training_part = parts[1].split("Planning sportif", 1)
                liste = "Liste de courses" + liste_part.strip()
                training = "Planning sportif" + training_part.strip()
            else:
                liste = "Liste de courses" + parts[1].strip()
        elif "Planning sportif" in contenu:
            parts = contenu.split("Planning sportif")
            planning = parts[0].strip()
            training = "Planning sportif" + parts[1].strip()
        else:
            planning = contenu

        # Sauvegardes séparées
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
            "planning": f"Erreur IA : {str(e)}"
        })

# Affichage du planning nutritionnel
@app.get("/planning", response_class=HTMLResponse)
async def afficher_planning(request: Request):
    try:
        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        planning = data["planning"]
    except:
        planning = "Aucun planning trouvé."

    return templates.TemplateResponse("planning.html", {"request": request, "planning": planning})

# Affichage de la liste de courses
@app.get("/liste", response_class=HTMLResponse)
async def afficher_liste(request: Request):
    try:
        with open("backend/data/liste.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        liste = data["liste"]
    except:
        liste = "Aucune liste trouvée."

    return templates.TemplateResponse("liste.html", {"request": request, "liste": liste})

# Affichage du planning d'entraînement
@app.get("/training", response_class=HTMLResponse)
async def afficher_training(request: Request):
    try:
        with open("backend/data/training.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        training = data["training"]
    except:
        training = "Aucun planning d'entraînement trouvé."

    return templates.TemplateResponse("training.html", {"request": request, "training": training})
