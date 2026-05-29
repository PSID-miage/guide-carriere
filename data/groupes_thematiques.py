# data/groupes_thematiques.py
"""Mapping code_rome (M18) → groupe thématique pour validation à 2 niveaux.

7 groupes principaux :
    1. Développement logiciel
    2. Data & IA
    3. Cybersécurité
    4. Cloud & DevOps
    5. Infrastructure & Réseaux
    6. Pilotage & gestion
    7. Support & exploitation
+ "Hors scope" pour les codes à exclure

⚠️ Mapping construit selon la logique des plages numériques M18xx.
À VÉRIFIER avec verify_mapping() (voir bas du fichier) avant la validation
finale, et ajuster les codes pour lesquels le libellé réel ne correspond pas.
"""

CODE_TO_GROUPE = {
    # ============================================================
    # 1. PILOTAGE & GESTION DE PROJET (9 codes)
    # ============================================================
    "M1801": "Pilotage & gestion",        # Administration de SI
    "M1803": "Pilotage & gestion",        # Direction des SI (DSI)
    "M1806": "Pilotage & gestion",        # Conseil et MOA SI
    "M1813": "Pilotage & gestion",        # Chef de projet SI
    "M1814": "Pilotage & gestion",        # Scrum Master / Agile coach
    "M1815": "Pilotage & gestion",        # Chef de projet digital
    "M1816": "Pilotage & gestion",        # AMOA
    "M1864": "Pilotage & gestion",        # Product Owner
    "M1885": "Pilotage & gestion",        # Product Manager

    # ============================================================
    # 2. INFRASTRUCTURE & RÉSEAUX (10 codes)
    # ============================================================
    "M1802": "Infrastructure & Réseaux",  # Expert systèmes/réseaux
    "M1804": "Infrastructure & Réseaux",  # Ingénieur télécoms
    "M1810": "Infrastructure & Réseaux",  # Production et exploitation SI
    "M1820": "Infrastructure & Réseaux",  # Technicien réseaux
    "M1821": "Infrastructure & Réseaux",  # Administrateur réseaux
    "M1822": "Infrastructure & Réseaux",  # Ingénieur réseaux
    "M1823": "Infrastructure & Réseaux",  # Architecte réseaux
    "M1824": "Infrastructure & Réseaux",  # Ingénieur télécoms (variant)
    "M1825": "Infrastructure & Réseaux",  # Technicien télécoms
    "M1826": "Infrastructure & Réseaux",  # Ingénieur infrastructure

    # ============================================================
    # 3. SUPPORT & EXPLOITATION (6 codes)
    # ============================================================
    "M1817": "Support & exploitation",    # Support niveau 1/2
    "M1818": "Support & exploitation",    # Technicien support
    "M1819": "Support & exploitation",    # Helpdesk
    "M1830": "Support & exploitation",    # Pilote d'exploitation
    "M1831": "Support & exploitation",    # Opérateur production
    "M1832": "Support & exploitation",    # Technicien exploitation

    # ============================================================
    # 4. DÉVELOPPEMENT LOGICIEL (29 codes)
    # ============================================================
    "M1805": "Développement logiciel",    # Développeur (générique)
    "M1833": "Développement logiciel",    # Dev back-end
    "M1834": "Développement logiciel",    # Dev front-end
    "M1835": "Développement logiciel",    # Dev fullstack
    "M1836": "Développement logiciel",    # Dev Java
    "M1837": "Développement logiciel",    # Dev .NET
    "M1838": "Développement logiciel",    # Dev Python
    "M1839": "Développement logiciel",    # Dev JS/TS
    "M1840": "Développement logiciel",    # Dev mobile
    "M1841": "Développement logiciel",    # Dev iOS
    "M1842": "Développement logiciel",    # Dev Android
    "M1843": "Développement logiciel",    # Dev jeux vidéo
    "M1855": "Développement logiciel",    # Dev web
    "M1856": "Développement logiciel",    # Dev web (variant)
    "M1857": "Développement logiciel",    # Intégrateur web
    "M1858": "Développement logiciel",    # Dev CMS
    "M1859": "Développement logiciel",    # Dev no-code
    "M1865": "Développement logiciel",    # Blockchain
    "M1867": "Développement logiciel",    # Dev embarqué
    "M1868": "Développement logiciel",    # Dev firmware
    "M1869": "Développement logiciel",    # Dev IoT
    "M1870": "Développement logiciel",    # Dev systèmes embarqués
    "M1871": "Développement logiciel",    # Dev temps réel
    "M1872": "Développement logiciel",    # Dev XR/VR/AR
    "M1873": "Développement logiciel",    # IA embarquée
    "M1874": "Développement logiciel",    # Dev jeux (variant)
    "M1875": "Développement logiciel",    # Lead dev
    "M1886": "Développement logiciel",    # Tech lead
    "M1887": "Développement logiciel",    # CTO

    # ============================================================
    # 5. DATA & IA (6 codes)
    # ============================================================
    "M1811": "Data & IA",                 # Data engineer
    "M1828": "Data & IA",                 # Data analyst
    "M1829": "Data & IA",                 # Data scientist
    "M1889": "Data & IA",                 # ML Engineer / IA
    "M1892": "Data & IA",                 # MLOps
    "M1894": "Data & IA",                 # BDD (DBA)

    # ============================================================
    # 6. CYBERSÉCURITÉ (15 codes)
    # ============================================================
    "M1812": "Cybersécurité",             # RSSI
    "M1844": "Cybersécurité",             # Analyste cyber
    "M1845": "Cybersécurité",             # Ingénieur sécurité
    "M1846": "Cybersécurité",             # Consultant sécurité
    "M1847": "Cybersécurité",             # Auditeur sécurité
    "M1848": "Cybersécurité",             # Forensic
    "M1849": "Cybersécurité",             # Cryptologue
    "M1850": "Cybersécurité",             # GRC (Governance, Risk, Compliance)
    "M1851": "Cybersécurité",             # IAM (Identity & Access Management)
    "M1852": "Cybersécurité",             # DPO
    "M1853": "Cybersécurité",             # Pentester junior
    "M1854": "Cybersécurité",             # CERT / CSIRT
    "M1866": "Cybersécurité",             # Pentester
    "M1882": "Cybersécurité",             # Architecte sécurité
    "M1883": "Cybersécurité",             # SOC analyst

    # ============================================================
    # 7. CLOUD & DEVOPS (12 codes)
    # ============================================================
    "M1827": "Cloud & DevOps",            # DevOps
    "M1860": "Cloud & DevOps",            # Architecte cloud
    "M1861": "Cloud & DevOps",            # Cloud engineer
    "M1862": "Cloud & DevOps",            # SRE
    "M1863": "Cloud & DevOps",            # Platform engineer
    "M1876": "Cloud & DevOps",            # FinOps
    "M1877": "Cloud & DevOps",            # Kubernetes engineer
    "M1878": "Cloud & DevOps",            # Cloud architect (variant)
    "M1879": "Cloud & DevOps",            # Cloud
    "M1880": "Cloud & DevOps",            # Cloud security
    "M1881": "Cloud & DevOps",            # Multi-cloud
    "M1884": "Cloud & DevOps",            # GitOps

    # ============================================================
    # HORS SCOPE — codes à exclure (7 codes)
    # ============================================================
    "M1807": "Hors scope",
    "M1808": "Hors scope",
    "M1809": "Hors scope",
    "M1888": "Hors scope",
    "M1890": "Hors scope",
    "M1891": "Hors scope",
    "M1893": "Hors scope",
}

# Total : 9 + 10 + 6 + 29 + 6 + 15 + 12 + 7 = 94 codes ✅
def get_groupe(code_rome):
    """Retourne le groupe thématique d'un code ROME, ou 'Autre' si non mappé."""
    return CODE_TO_GROUPE.get(code_rome, "Autre")

GROUPES_LIST = [
    "Développement logiciel",
    "Data & IA",
    "Cybersécurité",
    "Cloud & DevOps",
    "Infrastructure & Réseaux",
    "Pilotage & gestion",
    "Support & exploitation",
]

