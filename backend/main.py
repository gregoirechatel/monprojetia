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
    planning = {}
    liste_complete = ""
    training = ""

    for jour in JOURS:
        prompt = (
            f"Tu es un expert en nutrition. Génére uniquement le plan nutritionnel de {jour} (matin, midi, soir), "
            f"pour une personne de {age} ans, {poids} kg, {taille} cm, sexe {sexe}, objectif {objectif}, activité {activite}. "
            f"Donne les grammages exacts. Puis ajoute une courte liste de courses pour cette journée à la fin."
        )
        data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
        try:
            res = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            content = res.json()["choices"][0]["message"]["content"]
            planning[jour] = content

            if "Liste de courses" in content:
                liste_complete += content.split("Liste de courses", 1)[-1].strip() + "\n"

        except Exception as e:
            planning[jour] = f"Erreur IA pour {jour} : {e}"

    # Générer training global (1 fois)
    training_prompt = (
        f"Tu es coach sportif. Génére un planning sportif hebdomadaire de 7 jours (avec 1 jour repos) adapté à : {objectif}, {activite}. "
        f"Donne des explications claires jour par jour."
    )
    try:
        res = requests.post(CLAUDE_URL, headers=HEADERS, json={
            "model": "anthropic/claude-3-haiku",
            "messages": [{"role": "user", "content": training_prompt}]
        })
        training = res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        training = f"Erreur IA : {e}"

    # Sauvegardes
    with open("backend/data/planning.json", "w", encoding="utf-8") as f:
        json.dump(planning, f, ensure_ascii=False, indent=2)
    with open("backend/data/liste.json", "w", encoding="utf-8") as f:
        json.dump({"liste": liste_complete}, f, ensure_ascii=False, indent=2)
    with open("backend/data/training.json", "w", encoding="utf-8") as f:
        json.dump({"training": training}, f, ensure_ascii=False, indent=2)

    return templates.TemplateResponse("planning.html", {"request": request, "planning": planning})

@app.post("/regenerer/{jour}", response_class=HTMLResponse)
async def regenerer_jour(request: Request, jour: str):
    try:
        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            planning = json.load(f)
    except:
        planning = {}

    prompt = f"Génère uniquement le plan nutritionnel pour {jour} (matin, midi, soir), avec les grammages précis, simple et adapté."
    data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
    try:
        res = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
        content = res.json()["choices"][0]["message"]["content"]
        planning[jour] = content
    except Exception as e:
        planning[jour] = f"Erreur IA : {e}"

    with open("backend/data/planning.json", "w", encoding="utf-8") as f:
        json.dump(planning, f, ensure_ascii=False, indent=2)

    return RedirectResponse("/planning", status_code=303)

@app.get("/planning", response_class=HTMLResponse)
async def afficher_planning(request: Request):
    try:
        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            planning = json.load(f)
    except:
        planning = {j: "Non précisé" for j in JOURS}
    return templates.TemplateResponse("planning.html", {"request": request, "planning": planning})

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
