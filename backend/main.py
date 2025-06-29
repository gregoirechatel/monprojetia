import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import openai
import pathlib
import json

# Charger les variables d’environnement depuis Render ou local
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Définir le dossier du projet
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

# Init FastAPI
app = FastAPI()

# CORS pour accès depuis le JS (planning.html)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fichiers statiques
app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")

# Route API : génération de planning
@app.post("/generate")
async def generate(objectif: str = Form(...), contraintes: str = Form(...)):
    prompt = f"""Tu es un expert en nutrition. Crée un planning alimentaire pour atteindre : {objectif}.
Contraintes : {contraintes}.
Le planning doit être structuré jour par jour, repas par repas, avec grammages et plats simples, comme dans un Google Agenda.
À la fin, ajoute une liste de courses synthétique.
Réponds en HTML pur prêt à afficher dans une page web.
    """

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content

        # Sauvegarder le dernier planning (optionnel)
        data_path = BASE_DIR / "backend" / "data" / "planning.json"
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump({"html": content}, f, ensure_ascii=False, indent=2)

        return JSONResponse({"html": content})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
