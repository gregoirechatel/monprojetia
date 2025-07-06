import os
import json
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
async def generer(request: Request, objectif: str = Form(...), age: int = Form(...),
    poids: float = Form(...), taille: int = Form(...), sexe: str = Form(...),
    activite: str = Form(...), email: str = Form(...)):

    plannings = {}
    for jour in JOURS:
        prompt = (
            f"Tu es un expert en nutrition. Génére un planning nutritionnel pour {jour} : "
            f"3 repas équilibrés (matin, midi, soir) avec grammages, adaptés à un profil de "
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
    await generer_training(age, poids, objectif, activite)
    return RedirectResponse(url="/planning", status_code=303)

async def generer_liste_courses(plannings: dict):
    texte_complet = "\n".join(plannings.values())
    prompt_liste = (
        "Voici un planning nutritionnel pour la semaine :\n" + texte_complet +
        "\n\nGénère une liste de courses unique pour la semaine complète, avec quantités et grammages précis."
    )
    data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt_liste}]}
    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
        liste = response.json()["choices"][0]["message"]["content"]
    except:
        liste = "Erreur lors de la génération de la liste."

    with open("backend/data/liste.json", "w", encoding="utf-8") as f:
        json.dump({"liste": liste}, f, ensure_ascii=False, indent=2)

async def generer_training(age, poids, objectif, activite):
    prompt = (
        f"Tu es coach sportif. Génère un planning d'entraînement hebdomadaire structuré sur 7 jours "
        f"avec au moins un jour de repos, cohérent avec ce profil : {age} ans, {poids} kg, objectif {objectif}, activité {activite}. "
        f"Propose des séances concrètes et variées, de 45 minutes max."
    )
    data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
        training = response.json()["choices"][0]["message"]["content"]
    except:
        training = "Erreur lors de la génération de l'entraînement."

    with open("backend/data/training.json", "w", encoding="utf-8") as f:
        json.dump({"training": training}, f, ensure_ascii=False, indent=2)

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
        training = "Aucun entraînement trouvé."
    return templates.TemplateResponse("training.html", {"request": request, "training": training})

@app.get("/coach", response_class=HTMLResponse)
async def coach_page(request: Request):
    return templates.TemplateResponse("coach.html", {"request": request, "reponse": ""})

@app.post("/coach", response_class=HTMLResponse)
async def coach_action(request: Request, message: str = Form(...)):
    message_lower = message.lower()

    # --- nutrition ciblée sur un jour ---
    jour_cible = next((j for j in JOURS if j.lower() in message_lower), None)
    if jour_cible and any(mot in message_lower for mot in ["régénère", "recrée", "modifie", "change"]):
        prompt = f"Génère un nouveau planning nutritionnel pour {jour_cible}, structuré en 3 repas avec grammages précis."
        data_api = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
        try:
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_api)
            contenu = response.json()["choices"][0]["message"]["content"]

            with open("backend/data/planning.json", "r", encoding="utf-8") as f:
                data_planning = json.load(f)
            data_planning["plannings"][jour_cible] = contenu
            with open("backend/data/planning.json", "w", encoding="utf-8") as f:
                json.dump(data_planning, f, ensure_ascii=False, indent=2)

            await generer_liste_courses(data_planning["plannings"])
            reponse = f"✅ Planning du {jour_cible} mis à jour + liste de courses régénérée."
        except Exception as e:
            reponse = f"Erreur IA : {str(e)}"

    # --- toute la semaine / nutrition générale ---
    elif any(m in message_lower for m in ["repas", "calories", "protéines", "glucides", "ajoute un en-cas", "ajoute des collations", "modifie tous les jours"]):
        try:
            with open("backend/data/planning.json", "r", encoding="utf-8") as f:
                current = json.load(f)["plannings"]
            texte = "\n".join(current.values())
            prompt = message + "\nVoici le planning actuel :\n" + texte
            data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            new_planning = response.json()["choices"][0]["message"]["content"]

            # découpage intelligent par jour
            new_planning_dict = {}
            for jour in JOURS:
                start = new_planning.lower().find(jour.lower())
                if start != -1:
                    end = min([new_planning.lower().find(j.lower(), start + 1) for j in JOURS if j != jour and new_planning.lower().find(j.lower(), start + 1) != -1] + [len(new_planning)])
                    new_planning_dict[jour] = new_planning[start:end].strip()

            with open("backend/data/planning.json", "w", encoding="utf-8") as f:
                json.dump({"plannings": new_planning_dict}, f, ensure_ascii=False, indent=2)

            await generer_liste_courses(new_planning_dict)
            reponse = "✅ Planning nutritionnel mis à jour + liste mise à jour."
        except Exception as e:
            reponse = f"Erreur globale : {str(e)}"

    # --- entraînement ---
    elif any(m in message_lower for m in ["pompes", "abdos", "séance", "repos", "entraînement", "training", "exercice"]):
        try:
            with open("backend/data/training.json", "r", encoding="utf-8") as f:
                training = json.load(f)["training"]
            prompt = message + "\nVoici le programme actuel :\n" + training
            data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            nouveau = response.json()["choices"][0]["message"]["content"]

            with open("backend/data/training.json", "w", encoding="utf-8") as f:
                json.dump({"training": nouveau}, f, ensure_ascii=False, indent=2)

            reponse = "✅ Planning d'entraînement mis à jour."
        except Exception as e:
            reponse = f"Erreur IA training : {str(e)}"

    else:
        reponse = "❓ Je suis ton coach IA. Dis-moi par exemple : 'régénère le jeudi', ou 'ajoute des pompes chaque jour'."

    return templates.TemplateResponse("coach.html", {"request": request, "reponse": reponse})
