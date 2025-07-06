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

@app.get("/planning", response_class=HTMLResponse)
async def afficher_planning(request: Request):
    try:
        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            plannings = json.load(f)["plannings"]
    except:
        plannings = {}
    return templates.TemplateResponse("planning.html", {"request": request, "plannings": plannings})

@app.get("/liste", response_class=HTMLResponse)
async def afficher_liste(request: Request):
    try:
        with open("backend/data/liste.json", "r", encoding="utf-8") as f:
            liste = json.load(f)["liste"]
    except:
        liste = "Aucune liste trouvée."
    return templates.TemplateResponse("liste.html", {"request": request, "liste": liste})

@app.get("/training", response_class=HTMLResponse)
async def afficher_training(request: Request):
    try:
        with open("backend/data/training.json", "r", encoding="utf-8") as f:
            training = json.load(f)["training"]
    except:
        training = "Aucun planning trouvé."
    return templates.TemplateResponse("training.html", {"request": request, "training": training})

@app.get("/remarque", response_class=HTMLResponse)
async def remarque_page(request: Request):
    return templates.TemplateResponse("remarque.html", {"request": request, "reponse": ""})

@app.post("/remarque", response_class=HTMLResponse)
async def traiter_remarque(request: Request, feedback: str = Form(...)):
    try:
        with open("backend/data/formulaire.json", "r", encoding="utf-8") as f:
            formulaire = json.load(f)
        age = formulaire["age"]
        poids = formulaire["poids"]
        taille = formulaire["taille"]
        sexe = formulaire["sexe"]
        activite = formulaire["activite"]
        objectif = formulaire["objectif"]

        plannings = {}
        for jour in JOURS:
            prompt = (
                f"Tu es un expert en nutrition. Génére un planning pour le {jour} : "
                f"3 repas équilibrés (matin, midi, soir) avec les grammages, adaptés à un profil de "
                f"{age} ans, {poids} kg, {taille} cm, sexe {sexe}, objectif {objectif}, activité {activite}.\n"
                f"L'utilisateur a partagé ce ressenti : {feedback}. Prends-le en compte."
            )
            data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            contenu = response.json()["choices"][0]["message"]["content"]
            plannings[jour] = contenu

        with open("backend/data/planning.json", "w", encoding="utf-8") as f:
            json.dump({"plannings": plannings}, f, ensure_ascii=False, indent=2)

        await generer_liste_courses(plannings)
        reponse = "✅ Semaine régénérée avec ta remarque prise en compte."

    except Exception as e:
        reponse = f"❌ Erreur lors de la régénération : {str(e)}"

    return templates.TemplateResponse("remarque.html", {"request": request, "reponse": reponse})

@app.post("/generer", response_class=HTMLResponse)
async def generer(request: Request, objectif: str = Form(...), age: int = Form(...),
    poids: float = Form(...), taille: int = Form(...), sexe: str = Form(...),
    activite: str = Form(...), email: str = Form(...)):

    # Stockage des données dans formulaire.json
    with open("backend/data/formulaire.json", "w", encoding="utf-8") as f:
        json.dump({"objectif": objectif, "age": age, "poids": poids, "taille": taille, "sexe": sexe, "activite": activite, "email": email}, f, ensure_ascii=False, indent=2)

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

    await generer_liste_courses(plannings)
    await generer_training(objectif, activite)

    return RedirectResponse(url="/planning", status_code=303)

async def generer_liste_courses(plannings: dict):
    texte_complet = "\n".join(plannings.values())
    prompt_liste = (
        "Génère une seule liste de courses pour toute la semaine (sans séparer par jour) avec quantités et grammages précis.\n" + texte_complet
    )
    data_courses = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt_liste}]}
    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_courses)
        liste = response.json()["choices"][0]["message"]["content"]
    except:
        liste = "Erreur lors de la génération de la liste."

    with open("backend/data/liste.json", "w", encoding="utf-8") as f:
        json.dump({"liste": liste}, f, ensure_ascii=False, indent=2)

async def generer_training(objectif: str, activite: str):
    prompt = (
        f"Tu es un coach sportif. Génère un planning d'entraînement complet sur 7 jours adapté à une personne ayant comme objectif '{objectif}' "
        f"et un niveau d’activité '{activite}'. Utilise un format clair avec un jour par ligne. Inclue un jour de repos."
    )
    data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
        contenu = response.json()["choices"][0]["message"]["content"]
    except:
        contenu = "Erreur génération entraînement."

    with open("backend/data/training.json", "w", encoding="utf-8") as f:
        json.dump({"training": contenu}, f, ensure_ascii=False, indent=2)
