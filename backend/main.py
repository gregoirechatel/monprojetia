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
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

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

    for jour in JOURS:
        prompt = (
            f"Tu es un expert en nutrition. Génére un planning pour le {jour} : "
            f"3 repas équilibrés (matin, midi, soir) avec les grammages, adaptés à un profil de "
            f"{age} ans, {poids} kg, {taille} cm, sexe {sexe}, objectif {objectif}, activité {activite}."
        )
        data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
        try:
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            result = response.json()
            contenu = result["choices"][0]["message"]["content"]
            plannings[jour] = contenu
        except:
            plannings[jour] = f"Erreur IA pour {jour}"

    # Sauvegarde du planning
    with open("backend/data/planning.json", "w", encoding="utf-8") as f:
        json.dump({"plannings": plannings}, f, ensure_ascii=False, indent=2)

    # Génération liste de courses globale
    texte_complet = "\n".join(plannings.values())
    prompt_liste = (
        f"Génère une liste de courses complète pour toute la semaine à partir de ce planning. "
        f"Ne regroupe surtout pas les courses par jour, mais bien une seule fois avec les quantités :\n{texte_complet}"
    )
    data_courses = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt_liste}]}

    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_courses)
        result = response.json()
        liste = result["choices"][0]["message"]["content"]
    except:
        liste = "Erreur lors de la génération de la liste."

    with open("backend/data/liste.json", "w", encoding="utf-8") as f:
        json.dump({"liste": liste}, f, ensure_ascii=False, indent=2)

    return RedirectResponse(url="/planning", status_code=303)

@app.get("/planning", response_class=HTMLResponse)
async def afficher_planning(request: Request):
    try:
        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        plannings = data["plannings"]
    except:
        plannings = {}

    return templates.TemplateResponse("planning.html", {"request": request, "plannings": plannings})

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
        f"Tu es un expert en nutrition. Génére uniquement le planning nutritionnel pour {jour} : "
        f"3 repas équilibrés avec grammages, pour un profil actif."
    )
    data_api = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}

    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_api)
        result = response.json()
        contenu = result["choices"][0]["message"]["content"]
        data["plannings"][jour] = contenu
    except:
        data["plannings"][jour] = f"Erreur lors de la régénération de {jour}"

    # Sauvegarde
    with open("backend/data/planning.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Recalcul liste de courses unique pour la semaine
    full_text = "\n".join(data["plannings"].get(j, "") for j in JOURS)
    liste_prompt = (
        f"Voici le planning nutritionnel sur 7 jours. Génère une seule liste de courses hebdomadaire avec tous les ingrédients "
        f"et grammages regroupés sans doublons. Ne jamais faire une liste par jour :\n{full_text}"
    )
    data_courses = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": liste_prompt}]}

    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_courses)
        result = response.json()
        liste = result["choices"][0]["message"]["content"]
    except:
        liste = "Erreur liste courses"

    with open("backend/data/liste.json", "w", encoding="utf-8") as f:
        json.dump({"liste": liste}, f, ensure_ascii=False, indent=2)

    return RedirectResponse(url="/planning", status_code=303)

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

@app.get("/coach", response_class=HTMLResponse)
async def get_coach(request: Request):
    return templates.TemplateResponse("coach.html", {"request": request})

@app.post("/coach", response_class=HTMLResponse)
async def post_coach(request: Request, message: str = Form(...)):
    prompt = (
        f"Tu es un coach personnel IA ultra compétent en nutrition, sport et bien-être. "
        f"Voici une question ou instruction de ton client : {message}. "
        f"Réponds clairement, adapte si besoin le planning (ex: changer jeudi, raccourcir une séance)."
    )
    data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}

    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
        result = response.json()
        reponse = result["choices"][0]["message"]["content"]
    except:
        reponse = "Erreur IA lors de la réponse."

    return templates.TemplateResponse("coach.html", {"request": request, "reponse": reponse})
