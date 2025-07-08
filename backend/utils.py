import os
import json

DATA_ROOT = "backend/data/utilisateurs"

def get_user_email():
    try:
        with open("backend/data/formulaire.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("email", None)
    except:
        return None

def user_file_path(filename: str):
    email = get_user_email()
    if not email:
        return f"backend/data/{filename}"  # fallback si pas d'email
    return os.path.join(DATA_ROOT, email, filename)
