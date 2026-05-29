import os, requests
from dotenv import load_dotenv

load_dotenv()

r = requests.post(
    "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire",
    data={
        "grant_type": "client_credentials",
        "client_id": os.getenv("FT_CLIENT_ID"),
        "client_secret": os.getenv("FT_CLIENT_SECRET"),
        "scope": "api_offresdemploiv2 o2dsoffre"
    }
)
print(f"Auth status: {r.status_code}")
if r.status_code != 200:
    print(f"❌ {r.text}"); exit(1)
token = r.json()["access_token"]
print(f"✅ Token: {token[:30]}...")

r2 = requests.get(
    "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
    headers={"Authorization": f"Bearer {token}"},
    params={"codeROME": "M1805", "range": "0-4"}
)
print(f"Search status: {r2.status_code}")
if r2.status_code in (200, 206):
    offres = r2.json().get("resultats", [])
    print(f"✅ {len(offres)} offres reçues:")
    for o in offres[:3]:
        print(f"   • {o.get('intitule', 'N/A')[:80]}")
else:
    print(f"❌ {r2.text}")