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
            contenu = response.json()["choices"][0]["message"]["content"]
            plannings[jour] = contenu
        except:
            plannings[jour] = f"Erreur IA pour {jour}"

    with open("backend/data/planning.json", "w", encoding="utf-8") as f:
        json.dump({"plannings": plannings}, f, ensure_ascii=False, indent=2)

    # Liste unique pour toute la semaine
    texte_complet = "\n".join(plannings.values())
    prompt_liste = (
        "À partir de ce planning nutritionnel hebdomadaire, génère une seule et unique liste de courses "
        "pour toute la semaine avec quantités précises. Ne fais pas de liste par jour.\n" + texte_complet
    )
    data_courses = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt_liste}]}
    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_courses)
        liste = response.json()["choices"][0]["message"]["content"]
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

@app.get("/liste", response_class=HTMLResponse)
async def afficher_liste(request: Request):
    try:
        with open("backend/data/liste.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        liste = data["liste"]
    except:
        liste = "Aucune liste trouvée."
    return templates.TemplateResponse("liste.html", {"request": request, "liste": liste})

@app.get("/coach", response_class=HTMLResponse)
async def coach_page(request: Request):
    return templates.TemplateResponse("coach.html", {"request": request, "reponse": ""})

@app.post("/coach", response_class=HTMLResponse)
async def coach_action(request: Request, message: str = Form(...)):
    # Analyse du message
    jour_cible = next((j for j in JOURS if j.lower() in message.lower()), None)

    if "régénère" in message.lower() and jour_cible:
        prompt = f"Génère un nouveau planning nutritionnel pour {jour_cible}, 3 repas avec grammages, simples et efficaces."
        data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
        try:
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            nouveau = response.json()["choices"][0]["message"]["content"]
            with open("backend/data/planning.json", "r", encoding="utf-8") as f:
                planning_data = json.load(f)
            planning_data["plannings"][jour_cible] = nouveau
            with open("backend/data/planning.json", "w", encoding="utf-8") as f:
                json.dump(planning_data, f, ensure_ascii=False, indent=2)

            # Mise à jour automatique de la liste
            full_text = "\n".join(planning_data["plannings"].get(j, "") for j in JOURS)
            liste_prompt = "Fais une seule liste de courses hebdomadaire basée sur ceci :\n" + full_text
            data_courses = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": liste_prompt}]}
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_courses)
            liste = response.json()["choices"][0]["message"]["content"]
            with open("backend/data/liste.json", "w", encoding="utf-8") as f:
                json.dump({"liste": liste}, f, ensure_ascii=False, indent=2)

            reponse = f"✅ Le planning du {jour_cible} a été régénéré et la liste de courses mise à jour."
        except Exception as e:
            reponse = f"Erreur : {str(e)}"
    else:
        # Réponse générique de coach
        data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": message}]}
        try:
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            reponse = response.json()["choices"][0]["message"]["content"]
        except:
            reponse = "Erreur IA."

    return templates.TemplateResponse("coach.html", {"request": request, "reponse": reponse})
