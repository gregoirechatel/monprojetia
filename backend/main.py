import os
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import requests
from backend.utils import user_file_path 
from typing import List # 👈 ajout unique

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

@app.get("/accueil", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/formulaire", response_class=HTMLResponse)
async def formulaire(request: Request):
    return templates.TemplateResponse("formulaire.html", {"request": request})

@app.get("/planning", response_class=HTMLResponse)
async def afficher_planning(request: Request):
    try:
        with open(user_file_path("planning.json"), "r", encoding="utf-8") as f:
            plannings = json.load(f)["plannings"]
    except:
        plannings = {}
    return templates.TemplateResponse("planning.html", {"request": request, "plannings": plannings})

@app.get("/liste", response_class=HTMLResponse)
async def afficher_liste(request: Request):
    try:
        with open(user_file_path("liste.json"), "r", encoding="utf-8") as f:
            liste = json.load(f)["liste"]
    except:
        liste = "Aucune liste trouvée."
    return templates.TemplateResponse("liste.html", {"request": request, "liste": liste})

@app.get("/training", response_class=HTMLResponse)
async def afficher_training(request: Request):
    try:
        with open(user_file_path("training.json"), "r", encoding="utf-8") as f:
            training = json.load(f)["training"]
    except:
        training = "Aucun planning trouvé."
    return templates.TemplateResponse("training.html", {"request": request, "training": training})

@app.post("/generer", response_class=HTMLResponse)
async def generer(
    request: Request,
    age: int = Form(...),
    poids: float = Form(...),
    taille: int = Form(...),
    sexe: str = Form(...),
    activite: str = Form(...),
    sport_actuel: str = Form(...),
    sport_passe: str = Form(...),
    objectif: str = Form(...),
    deja_essaye: str = Form(...),
    reussi: str = Form(...),
    temps_dispo: str = Form(...),
    regime: str = Form(...),
    budget: str = Form(...),
    physique: str = Form(...),
    allergies: str = Form(...),
    precision: str = Form(...),
    jours_sport: List[str] = Form(default=[])
):

    formulaire = {
        "age": age,
        "poids": poids,
        "taille": taille,
        "sexe": sexe,
        "activite": activite,
        "sport_actuel": sport_actuel,
        "sport_passe": sport_passe,
        "objectif": objectif,
        "deja_essaye": deja_essaye,
        "reussi": reussi,
        "temps_dispo": temps_dispo,
        "regime": regime,
        "budget": budget,
        "physique": physique,
        "allergies": allergies,
        "precision": precision,
        "jours_sport": jours_sport  # 👈 AJOUT UNIQUE
    } 
    os.makedirs("backend/data", exist_ok=True)  # 👈 à ajouter ici

    with open(user_file_path("formulaire.json"), "w", encoding="utf-8") as f:
        json.dump(formulaire, f, ensure_ascii=False, indent=2)

    plannings = {}
    for jour in JOURS:
        prompt = (
            f"Tu es un expert en nutrition. Génére un planning pour le {jour} : "
            f"3 repas équilibrés (matin, midi, soir) avec les grammages, adaptés à un profil de "
            f"{age} ans, {poids} kg, {taille} cm, sexe {sexe}, objectif {objectif}, activité {activite}, "
            f"régime alimentaire : {regime}, allergies : {allergies}, budget hebdo : {budget}€. "
            f"L’utilisateur a précisé : {precision}. "
            f"Adapte les repas pour respecter le régime et éviter les allergènes. "
            f"N’utilise pas les mots glucides, lipides ou protéines. Format : sans blabla, uniquement les repas."
        )
        data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
        try:
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            contenu = response.json()["choices"][0]["message"]["content"]
            plannings[jour] = contenu
        except:
            plannings[jour] = f"Erreur IA pour {jour}"

    with open(user_file_path("planning.json"), "w", encoding="utf-8") as f:
        json.dump({"plannings": plannings}, f, ensure_ascii=False, indent=2)

    await generer_liste_courses(plannings)
    await generer_training(objectif, activite, sport_actuel, sport_passe, temps_dispo, jours_sport)

    return RedirectResponse(url="/planning", status_code=303)


async def generer_liste_courses(plannings: dict):
    texte_complet = "\n".join(plannings.values())
    prompt_liste = (
        "Génère une seule liste de courses pour toute la semaine (sans séparer par jour) avec quantités et grammages précis. "
        "Assure-toi que chaque ingrédient listé est présent avec un grammage total correspondant à l’addition de tous les repas des 7 jours. Aucun ingrédient ne doit être oublié.\n"
        + texte_complet
    )
    data_courses = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt_liste}]}
    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data_courses)
        liste = response.json()["choices"][0]["message"]["content"]
    except:
        liste = "Erreur lors de la génération de la liste."

    with open(user_file_path("liste.json"), "w", encoding="utf-8") as f:
        json.dump({"liste": liste}, f, ensure_ascii=False, indent=2)




async def generer_training(objectif: str, activite: str, sport_actuel: str, sport_passe: str, temps_dispo: str, jours_sport: List[str]):
    jours_str = ', '.join(jours_sport)
    prompt = (
        f"Tu es un coach sportif. Génére un planning d'entraînement uniquement pour les jours suivants : {jours_str}, adapté à une personne ayant comme objectif '{objectif}', "
        f"niveau d’activité '{activite}', sport pratiqué actuellement : {sport_actuel}, sport pratiqué dans le passé : {sport_passe}, "
        f"temps disponible par jour pour s'entraîner : {temps_dispo}. "
        f"Detaille bien chaque exercice, pour une séance structurée dans un ordre précis. . Ne fais pas d’intro ni d’explication.répartis equitablement entre les jours"
        f"Fais au moins 5 lignes par jour pour que ce soit bien détaillé, pour chaque jour de la semaine. "
        f"Pour chaque exercice reconnu, ajoute un lien HTML cliquable vers sa fiche sur exrx.net juste après, au format : <a href='https://exrx.net/...'>Nom de l’exercice</a>."
        f"detaille bien les series et les repetitions si c'est necessaire"
    )
    data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
        contenu = response.json()["choices"][0]["message"]["content"]
    except:
        contenu = "Erreur génération entraînement."

    with open(user_file_path("training.json"), "w", encoding="utf-8") as f:
        json.dump({"training": contenu}, f, ensure_ascii=False, indent=2)


@app.get("/regenerer/{jour}", response_class=HTMLResponse)
async def regenerer_jour(request: Request, jour: str):
    if jour not in JOURS:
        return RedirectResponse(url="/planning", status_code=303)

    try:
        with open(user_file_path("formulaire.json"), "r", encoding="utf-8") as f:
            formulaire = json.load(f)
    except:
        return RedirectResponse(url="/planning", status_code=303)

    prompt = (
        f"Tu es un expert en nutrition. Génére uniquement le planning pour le {jour} : "
        f"3 repas équilibrés (matin, midi, soir) avec les grammages, adaptés à un profil de "
        f"{formulaire['age']} ans, {formulaire['poids']} kg, {formulaire['taille']} cm, sexe {formulaire['sexe']}, "
        f"objectif {formulaire['objectif']}, activité {formulaire['activite']}, "
        f"régime alimentaire : {formulaire['regime']}, allergies : {formulaire['allergies']}, "
        f"budget hebdo : {formulaire['budget']}€. "
        f"L’utilisateur a précisé : {formulaire['precision']}. "
        f"Adapte les repas pour respecter le régime et éviter les allergènes. "
        f"N’utilise pas les mots glucides, lipides ou protéines. Format : sans blabla, uniquement les repas."
    )

    data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}

    try:
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
        contenu = response.json()["choices"][0]["message"]["content"]

        with open(user_file_path("planning.json"), "r", encoding="utf-8") as f:
            data_json = json.load(f)

        data_json["plannings"][jour] = contenu

        with open(user_file_path("planning.json"), "w", encoding="utf-8") as f:
            json.dump(data_json, f, ensure_ascii=False, indent=2)

        await generer_liste_courses(data_json["plannings"])

    except:
        pass

    return RedirectResponse(url="/planning", status_code=303)


@app.get("/coach", response_class=HTMLResponse)
async def coach_page(request: Request):
    return templates.TemplateResponse("coach.html", {"request": request, "reponse": ""})


@app.post("/coach", response_class=HTMLResponse)
@app.post("/coach", response_class=HTMLResponse)
async def coach_action(request: Request, message: str = Form(...)):
    message_lower = message.lower()
    reponse = ""

    try:
        with open(user_file_path("formulaire.json"), "r", encoding="utf-8") as f:
            formulaire = json.load(f)
    except:
        return templates.TemplateResponse("coach.html", {"request": request, "reponse": "❌ Impossible de charger le formulaire utilisateur."})

    # 🧠 L’IA détermine si la requête concerne la nutrition ou l’entraînement
    prompt_classification = (
        f"Un utilisateur t’envoie cette requête :\n\n\"{message}\"\n\n"
        "Ta seule tâche est de dire si cela concerne l'entraînement physique ou la nutrition. "
        "Réponds uniquement par 'sport' ou 'nutrition' (sans phrase, sans ponctuation)."
    )
    try:
        data_classification = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt_classification}]}
        response_class = requests.post(CLAUDE_URL, headers=HEADERS, json=data_classification)
        domaine = response_class.json()["choices"][0]["message"]["content"].strip().lower()
    except:
        domaine = "nutrition"

    # 🧠 L’IA détermine les jours concernés
    prompt_jours = (
        f"Un utilisateur t’écrit : \"{message}\"\n"
        f"Quels jours de la semaine sont concernés par sa demande ? "
        f"Réponds uniquement par une liste de jours clairs en français, séparés par des virgules. "
        f"Si tous les jours sont concernés, réponds : 'tous'. Aucune autre phrase."
    )
    try:
        data_jours = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt_jours}]}
        response_jours = requests.post(CLAUDE_URL, headers=HEADERS, json=data_jours)
        jours_texte = response_jours.json()["choices"][0]["message"]["content"].strip().lower()
        if "tous" in jours_texte:
            jours_mentions = JOURS
        else:
            jours_mentions = [j for j in JOURS if j.lower() in jours_texte]
    except:
        jours_mentions = JOURS

    if domaine == "sport":
        jours_formulaire = formulaire.get("jours_sport", [])
        if isinstance(jours_formulaire, str):
            jours_formulaire = [jours_formulaire]  # Si un seul jour
        elif not isinstance(jours_formulaire, list):
            jours_formulaire = []

        # Fusion avec les jours détectés par l’IA dans le message
        jours_mentions = list(set(jours_mentions + jours_formulaire))
        jours_str = ', '.join(jours_mentions)

        prompt = (
            f"Tu es un coach sportif. Génére un planning d'entraînement uniquement pour les jours suivants : {jours_str}, "
            f"adapté à une personne ayant comme objectif '{formulaire['objectif']}', "
            f"niveau d’activité '{formulaire['activite']}', sport pratiqué actuellement : {formulaire['sport_actuel']}, "
            f"sport pratiqué dans le passé : {formulaire['sport_passe']}, "
            f"temps disponible par jour pour s'entraîner : {formulaire['temps_dispo']} min. "
            f"Voici la demande précise de l'utilisateur : {message} "
            f"Detaille bien chaque exercice, pour une séance structurée dans un ordre précis. Ne fais pas d’intro ni d’explication. "
            f"Répartis équitablement entre les jours. Fais au moins 5 lignes par jour. "
            f"Pour chaque exercice reconnu, ajoute un lien HTML cliquable vers sa fiche sur exrx.net au format : "
            f"<a href='https://exrx.net/...'>Nom de l’exercice</a>. "
            f"Detaille bien les séries et les répétitions si nécessaire."
        )

        data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
        response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
        contenu = response.json()["choices"][0]["message"]["content"]

        with open(user_file_path("training.json"), "w", encoding="utf-8") as f:
            json.dump({"training": contenu}, f, ensure_ascii=False, indent=2)

        reponse = f"✅ Nouveau programme d'entraînement généré :\n\n{contenu}"

    else:
        with open(user_file_path("planning.json"), "r", encoding="utf-8") as f:
            data_json = json.load(f)

        for jour in jours_mentions:
            prompt = (
                f"Tu es un expert en nutrition. Voici une demande utilisateur :\n"
                f"{message}\n\n"
                f"Voici son profil : {formulaire['age']} ans, {formulaire['poids']} kg, {formulaire['taille']} cm, sexe {formulaire['sexe']}, "
                f"objectif = {formulaire['objectif']}, activité = {formulaire['activite']}, "
                f"régime = {formulaire['regime']}, allergies = {formulaire['allergies']}, "
                f"budget = {formulaire['budget']}€, précisions : {formulaire['precision']}.\n"
                f"Génère uniquement les 3 repas (matin, midi, soir) avec aliments et grammages pour le jour : {jour}. "
                "Aucune introduction, aucun blabla, format brut uniquement."
            )
            data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            contenu = response.json()["choices"][0]["message"]["content"]
            data_json["plannings"][jour] = contenu

        with open(user_file_path("planning.json"), "w", encoding="utf-8") as f:
            json.dump(data_json, f, ensure_ascii=False, indent=2)

        await generer_liste_courses(data_json["plannings"])
        reponse = f"✅ Planning nutrition mis à jour."

    return templates.TemplateResponse("coach.html", {"request": request, "reponse": reponse})


@app.get("/remarque", response_class=HTMLResponse)
async def get_remarque(request: Request):
    return templates.TemplateResponse("remarque.html", {"request": request})

@app.post("/remarque", response_class=HTMLResponse)
async def post_remarque(request: Request, feedback: str = Form(...)):
    try:
        with open(user_file_path("formulaire.json"), "r", encoding="utf-8") as f:
            formulaire = json.load(f)
    except:
        return templates.TemplateResponse("remarque.html", {"request": request, "erreur": "❌ Formulaire manquant"})

    plannings = {}
    for jour in JOURS:
        prompt = (
            f"Tu es un expert en nutrition. Génére un planning pour le {jour} : "
            f"3 repas équilibrés (matin, midi, soir) avec les grammages, adaptés à un profil de "
            f"{formulaire['age']} ans, {formulaire['poids']} kg, {formulaire['taille']} cm, sexe {formulaire['sexe']}, "
            f"objectif {formulaire['objectif']}, activité {formulaire['activite']}, "
            f"régime alimentaire : {formulaire['regime']}, allergies : {formulaire['allergies']}, budget hebdo : {formulaire['budget']}€. "
            f"L’utilisateur a précisé : {formulaire['precision']}. "
            f"Remarque de l’utilisateur cette semaine : {feedback}. "
            f"Adapte les repas pour respecter le régime et éviter les allergènes. "
            f"N’utilise pas les mots glucides, lipides ou protéines. Format : sans blabla, uniquement les repas."
        )
        data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
        try:
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            contenu = response.json()["choices"][0]["message"]["content"]
            plannings[jour] = contenu
        except:
            plannings[jour] = f"Erreur IA pour {jour}"

    with open(user_file_path("planning.json"), "w", encoding="utf-8") as f:
        json.dump({"plannings": plannings}, f, ensure_ascii=False, indent=2)

    await generer_liste_courses(plannings)
    await generer_training(
    formulaire["objectif"],
    formulaire["activite"],
    formulaire["sport_actuel"],
    formulaire["sport_passe"],
    formulaire["temps_dispo"],
    formulaire["jours_sport"]
)


    return RedirectResponse(url="/planning", status_code=303)


from backend import router
app.include_router(router.router)
