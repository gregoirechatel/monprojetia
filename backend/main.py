# (le code complet est identique au précédent à l’exception de coach_action ci-dessous)

@app.post("/coach", response_class=HTMLResponse)
async def coach_action(request: Request, message: str = Form(...)):
    message_lower = message.lower()
    jour_cible = next((j for j in JOURS if j.lower() in message_lower), None)
    reponse = ""

    try:
        # 🔍 Filtrage du domaine de la requête (entraînement ou nutrition)
        mots_clefs_sport = ["sport", "entraînement", "training", "musculation", "pompes", "séance", "cardio", "repos", "salle"]
        domaine = "training" if any(mot in message_lower for mot in mots_clefs_sport) else "nutrition"

        if domaine == "training":
            prompt = (
                "Tu es un coach sportif. Voici une demande utilisateur :\n"
                f"{message}\n\n"
                "Génère un planning d'entraînement hebdomadaire clair et adapté. Format brut, un jour par ligne, sans blabla."
            )

            data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": prompt}]}
            response = requests.post(CLAUDE_URL, headers=HEADERS, json=data)
            contenu = response.json()["choices"][0]["message"]["content"]

            with open("backend/data/training.json", "w", encoding="utf-8") as f:
                json.dump({"training": contenu}, f, ensure_ascii=False, indent=2)

            reponse = f"✅ Entraînement mis à jour :\n\n{contenu}"

        else:
            prompt = (
                "Tu es un expert en nutrition. Voici une demande utilisateur :\n"
                f"{message}\n\n"
                "Interprète cette demande et génère les plannings alimentaires modifiés. "
                "Pour chaque jour concerné, donne uniquement un planning structuré en 3 repas (matin, midi, soir) avec des aliments et grammages. "
                "Ne fais pas d’introduction, pas de blabla, pas de conseil. Donne uniquement le texte brut des repas pour chaque jour."
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
