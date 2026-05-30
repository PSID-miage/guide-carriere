# clean_cv_annotes.py
"""
Nettoie cv_annotes.csv exporté depuis Google Sheets :
- Skip la ligne 'Column1;Column2;...' parasite
- Fix l'encoding (Latin-1/CP1252 → UTF-8)
- Renomme les colonnes pour matcher le format attendu par ml.py
- Convertit le séparateur ; en ,
"""

import pandas as pd
import shutil

INPUT = "data/cv_annotes.csv"
BACKUP = "data/cv_annotes_raw.csv"
OUTPUT = "data/cv_annotes.csv"

# 1. Backup du fichier brut au cas où
shutil.copy(INPUT, BACKUP)
print(f"💾 Backup créé : {BACKUP}")

# 2. Tentative de lecture avec plusieurs encodings
df = None
for enc in ["cp1252", "latin-1", "utf-8-sig", "utf-8"]:
    try:
        df = pd.read_csv(
            BACKUP,
            sep=";",
            encoding=enc,
            skiprows=1,        # Skip "Column1;Column2;..."
            engine="python",
            on_bad_lines="skip"
        )
        print(f"✅ Lu avec encoding={enc}")
        break
    except Exception as e:
        print(f"❌ {enc} : {e}")
        continue

if df is None:
    raise RuntimeError("Impossible de lire le fichier avec un encoding connu")

# 3. Nettoyer : virer colonnes vides + renommer
df = df.loc[:, ~df.columns.str.contains('^Unnamed|^Column', na=False)]
df = df.dropna(how="all")  # virer lignes vides

print(f"\n📋 Colonnes brutes : {list(df.columns)}")
print(f"📊 Lignes : {len(df)}")

# 4. Renommage
rename_map = {
    "texte_cv": "cv_text",
    "code_rome": "code_rome_manuel",
    # groupe_thematique reste tel quel
}
df = df.rename(columns=rename_map)

# 5. Garder uniquement les colonnes utiles
required = ["cv_id", "cv_text", "code_rome_manuel", "groupe_thematique"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise RuntimeError(f"❌ Colonnes manquantes : {missing}\nColonnes dispo : {list(df.columns)}")

df = df[required]

# 6. Drop des CV sans annotation
df = df.dropna(subset=["code_rome_manuel", "groupe_thematique"])

# 7. Sauvegarde finale en UTF-8 standard avec sep=,
df.to_csv(OUTPUT, index=False, encoding="utf-8", sep=",")
print(f"\n💾 {len(df)} CV nettoyés et sauvegardés dans {OUTPUT}")
print(f"\n📋 Aperçu final :")
print(df[['cv_id', 'code_rome_manuel', 'groupe_thematique']].to_string())