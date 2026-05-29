# prepare_data.py
"""Scripts de préparation des données :
1. Scrape l'API France Travail pour les offres M18 → data/offres_ft_m18.csv
2. Export du Google Sheet d'étiquetage CV → data/cv_annotes.csv
"""

import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from data.codes_m18 import CODES_INFO_M18

load_dotenv()

CLIENT_ID = os.getenv("FT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FT_CLIENT_SECRET")
TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

# ==========================================================
# PARTIE A : SCRAPING API FRANCE TRAVAIL
# ==========================================================

def get_token():
    """Authentification OAuth2 client_credentials."""
    response = requests.post(TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "api_offresdemploiv2 o2dsoffre"
    })
    # === DEBUG ===
    print(f"DEBUG status: {response.status_code}")
    print(f"DEBUG body: {response.text}")
    print(f"DEBUG client_id sent: {CLIENT_ID[:30] if CLIENT_ID else 'NONE'}...")
    # === FIN DEBUG ===
    response.raise_for_status()
    return response.json()["access_token"]

def fetch_offres_for_code(code_rome, token, max_offres=150):
    """Récupère jusqu'à max_offres pour un code ROME donné."""
    headers = {"Authorization": f"Bearer {token}"}
    offres = []

    # On pagine par tranches de 50
    for start in range(0, max_offres, 50):
        params = {
            "codeROME": code_rome,
            "range": f"{start}-{start + 49}"
        }
        try:
            r = requests.get(SEARCH_URL, headers=headers, params=params, timeout=15)
            if r.status_code == 204:  # pas de résultats
                break
            if r.status_code not in (200, 206):
                print(f"  ⚠️  {code_rome} status {r.status_code} (start={start})")
                break

            data = r.json().get("resultats", [])
            if not data:
                break

            for offre in data:
                offres.append({
                    "code_rome": code_rome,
                    "libelle_offre": offre.get("intitule", ""),
                    "description": offre.get("description", ""),
                    "competences": " ".join([
                        c.get("libelle", "") for c in offre.get("competences", [])
                    ]),
                })

            time.sleep(0.3)  # politesse — éviter rate limiting
        except Exception as e:
            print(f"  ❌ {code_rome} erreur : {e}")
            break

    return offres

def scrape_offres_m18(output_path="data/offres_ft_m18.csv"):
    """Boucle sur les 87 codes M18 utiles et sauvegarde tout en CSV."""
    print(f"🔑 Authentification...")
    token = get_token()
    print(f"✅ Token obtenu")

    all_offres = []
    for i, code in enumerate(CODES_INFO_M18, 1):
        print(f"[{i}/{len(CODES_INFO_M18)}] {code} ...", end=" ", flush=True)
        offres = fetch_offres_for_code(code, token)
        all_offres.extend(offres)
        print(f"→ {len(offres)} offres (total : {len(all_offres)})")

    df = pd.DataFrame(all_offres)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\\n💾 {len(df)} offres sauvegardées dans {output_path}")
    print(f"📊 Répartition par code ROME :")
    print(df['code_rome'].value_counts().head(10))

# ==========================================================
# PARTIE B : EXPORT DU GOOGLE SHEET D'ÉTIQUETAGE
# ==========================================================

def export_cv_dataset(input_path="data/cv_annotes_brut.csv",
                      output_path="data/cv_annotes.csv"):
    """
    Lit le CSV téléchargé depuis Google Sheet (avec doubles annotations)
    et produit un dataset clean pour la validation (une ligne par CV).

    Format attendu du Google Sheet (téléchargé en CSV) :
    cv_id | annotatrice | cv_text | code_rome_manuel | groupe_thematique | confiance | notes
    """
    df = pd.read_csv(input_path)

    # On garde la 1ère annotation pour chaque CV (la 2e sert au kappa)
    df_clean = df.drop_duplicates(subset="cv_id", keep="first")
    df_clean = df_clean[['cv_id', 'cv_text', 'code_rome_manuel', 'groupe_thematique']]

    df_clean.to_csv(output_path, index=False, encoding="utf-8")
    print(f"💾 {len(df_clean)} CV uniques exportés dans {output_path}")
    return df_clean

# ==========================================================
# COHEN'S KAPPA (à lancer après l'étiquetage à 4)
# ==========================================================

def compute_cohen_kappa(input_path="data/cv_annotes_brut.csv"):
    """Compare les annotations entre annotatrices sur les CV en commun."""
    from sklearn.metrics import cohen_kappa_score
    df = pd.read_csv(input_path)

    # Pour chaque CV avec 2+ annotations, on récupère les paires
    paires = []
    for cv_id, group in df.groupby("cv_id"):
        if len(group) >= 2:
            paires.append({
                "annot1": group.iloc[0]['code_rome_manuel'],
                "annot2": group.iloc[1]['code_rome_manuel'],
                "annot1_groupe": group.iloc[0]['groupe_thematique'],
                "annot2_groupe": group.iloc[1]['groupe_thematique'],
            })

    if not paires:
        print("⚠️  Pas de paires d'annotations trouvées")
        return

    df_paires = pd.DataFrame(paires)

    # Kappa au niveau ROME (fine)
    kappa_fine = cohen_kappa_score(df_paires['annot1'], df_paires['annot2'])
    # Kappa au niveau groupe (coarse)
    kappa_coarse = cohen_kappa_score(df_paires['annot1_groupe'], df_paires['annot2_groupe'])

    print(f"🤝 Cohen's kappa (code ROME précis) : {kappa_fine:.3f}")
    print(f"🤝 Cohen's kappa (groupe thématique) : {kappa_coarse:.3f}")
    print(f"   → Seuil acceptable : > 0.6")
    print(f"   → Nombre de paires : {len(paires)}")

    return kappa_fine, kappa_coarse

# ==========================================================
# ENTRY POINTS
# ==========================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "scrape":
            scrape_offres_m18()
        elif cmd == "export_cv":
            export_cv_dataset()
        elif cmd == "kappa":
            compute_cohen_kappa()
        else:
            print(f"Commande inconnue : {cmd}")
            print("Usage : python prepare_data.py [scrape|export_cv|kappa]")
    else:
        # Par défaut : scrape les offres
        scrape_offres_m18()