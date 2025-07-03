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

    # Génération liste de courses une seule fois pour toute la semaine
    texte_complet = "\n".join(plannings[j] for j in JOURS if j in plannings)
    prompt_liste = f"Génère une liste de courses complète avec grammages à partir de ce programme hebdomadaire :\n{texte_complet}"
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

    # Recalcul unique liste courses à partir des 7 jours
    full_text = "\n".join(data["plannings"].get(j, "") for j in JOURS)
    liste_prompt = f"Génère une liste de courses unique et complète pour la semaine entière :\n{full_text}"
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
