import pandas as pd

# ======================
# 1. Charger les fichiers
# ======================
jobs = pd.read_csv("data/unix_referentiel_code_rome_v460_utf8.csv")
skills = pd.read_csv("data/unix_referentiel_competence_v460_utf8.csv")
links = pd.read_csv("data/unix_liens_rome_referentiels_v460_utf8.csv")

print("✅ Fichiers chargés")

# ======================
# 2. Garder seulement colonnes utiles
# ======================
jobs = jobs[["code_rome", "libelle_rome"]]
skills = skills[["code_ogr", "libelle_competence"]]
links = links[["code_rome", "code_ogr"]]

# ======================
# 3. Renommer pour simplifier
# ======================
jobs = jobs.rename(columns={
    "code_rome": "job_code",
    "libelle_rome": "job_title"
})

skills = skills.rename(columns={
    "code_ogr": "skill_code",
    "libelle_competence": "skill"
})

links = links.rename(columns={
    "code_rome": "job_code",
    "code_ogr": "skill_code"
})

print("✅ Colonnes nettoyées")

# ======================
# 4. Merge
# ======================
df = links.merge(jobs, on="job_code")
df = df.merge(skills, on="skill_code")

print("✅ Merge OK")
print(df.head())

# ======================
# 5. Regrouper compétences par métier
# ======================
final = df.groupby("job_title")["skill"].apply(lambda x: ", ".join(x)).reset_index()

# ======================
# 6. Sauvegarde
# ======================
final.to_csv("data/final_jobs.csv", index=False)

print("🎉 Dataset final créé : data/final_jobs.csv")