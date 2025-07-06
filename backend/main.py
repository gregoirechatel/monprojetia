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

@app.post("/generer", response_class=HTMLResponse)
async def generer(request: Request, objectif: str = Form(...), age: int = Form(...),
    poids: float = Form(...), taille: int = Form(...), sexe: str = Form(...),
    activite: str = Form(...), email: str = Form(...)):

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

@app.get("/regenerer/{jour}", response_class=HTMLResponse)
async def regenerer_jour(request: Request, jour: str):
    if jour not in JOURS:
        return RedirectResponse(url="/planning", status_code=303)

    prompt = f"Génère uniquement le planning nutritionnel pour {jour}, structuré en 3 repas équilibrés avec grammages précis."
    data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}

    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
        contenu = response.json()["choices"][0]["message"]["content"]

        with open("backend/data/planning.json", "r", encoding="utf-8") as f:
            data_json = json.load(f)
        data_json["plannings"][jour] = contenu

        with open("backend/data/planning.json", "w", encoding="utf-8") as f:
            json.dump(data_json, f, ensure_ascii=False, indent=2)

        await generer_liste_courses(data_json["plannings"])
    except:
        pass

    return RedirectResponse(url="/planning", status_code=303)

@app.get("/coach", response_class=HTMLResponse)
async def coach_page(request: Request):
    return templates.TemplateResponse("coach.html", {"request": request, "reponse": ""})

@app.post("/coach", response_class=HTMLResponse)
async def coach_action(request: Request, message: str = Form(...)):
    message_lower = message.lower()
    jour_cible = next((j for j in JOURS if j.lower() in message_lower), None)
    reponse = ""

    try:
        if any(mot in message_lower for mot in ["entraînement", "entrainement", "training", "sport", "pompes", "abdos", "squat", "cardio", "repos"]):
            prompt = (
                "Tu es un coach sportif. Voici une demande utilisateur :\n"
                f"{message}\n\n"
                "Génère un planning d'entraînement hebdomadaire adapté à sa requête. Donne un jour par ligne, clair, structuré, sans blabla."
            )
            data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            contenu = response.json()["choices"][0]["message"]["content"]

            with open("backend/data/training.json", "w", encoding="utf-8") as f:
                json.dump({"training": contenu}, f, ensure_ascii=False, indent=2)

            reponse = f"✅ Nouveau programme d'entraînement généré :\n\n{contenu}"

        else:
            prompt = (
                "Tu es un expert en nutrition. Voici une demande utilisateur :\n"
                f"{message}\n\n"
                "Interprète cette demande et génère les plannings nutritionnels modifiés. Pour chaque jour concerné, donne uniquement 3 repas (matin, midi, soir) avec aliments + grammages. "
                "Pas d’introduction, pas de blabla. Format brut uniquement."
            )
            data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            contenu = response.json()["choices"][0]["message"]["content"]

            with open("backend/data/planning.json", "r", encoding="utf-8") as f:
                data_json = json.load(f)

            if jour_cible:
                data_json["plannings"][jour_cible] = contenu
            else:
                for jour in JOURS:
                    if jour.lower() in contenu.lower():
                        index = contenu.lower().index(jour.lower())
                        bloc = contenu[index:].split("\n\n")[0].strip()
                        data_json["plannings"][jour] = bloc
                    else:
                        for jour in JOURS:
                            data_json["plannings"][jour] = contenu
                        break

            with open("backend/data/planning.json", "w", encoding="utf-8") as f:
                json.dump(data_json, f, ensure_ascii=False, indent=2)

            await generer_liste_courses(data_json["plannings"])
            reponse = f"✅ Planning nutrition mis à jour.\n\n{contenu}"

    except Exception as e:
        reponse = f"❌ Erreur IA : {str(e)}"

    return templates.TemplateResponse("coach.html", {"request": request, "reponse": reponse})

@app.get("/remarque", response_class=HTMLResponse)
async def get_remarque(request: Request):
    return templates.TemplateResponse("remarque.html", {"request": request})

@app.post("/remarque", response_class=HTMLResponse)
async def post_remarque(request: Request, feedback: str = Form(...)):
    try:
        with open("backend/data/formulaire.json", "r", encoding="utf-8") as f:
            formulaire = json.load(f)
    except:
        return templates.TemplateResponse("remarque.html", {"request": request, "erreur": "❌ Formulaire manquant"})

    plannings = {}
    for jour in JOURS:
        prompt = (
            f"Tu es un expert en nutrition. Génére un planning pour le {jour} en tenant compte de cette remarque : {feedback}. "
            f"3 repas équilibrés (matin, midi, soir) avec les grammages, adaptés à un profil de "
            f"{formulaire['age']} ans, {formulaire['poids']} kg, {formulaire['taille']} cm, sexe {formulaire['sexe']}, "
            f"objectif {formulaire['objectif']}, activité {formulaire['activite']}."
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
    await generer_training(formulaire["objectif"], formulaire["activite"])

    return RedirectResponse(url="/planning", status_code=303)
