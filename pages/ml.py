
import re
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx

dash.register_page(__name__, path="/ml", name="Analyse Profil")

SKILL_OPTIONS = [
    {"label": "Python", "value": "python"},
    {"label": "SQL", "value": "sql"},
    {"label": "Excel / Reporting", "value": "excel"},
    {"label": "Power BI / DataViz", "value": "powerbi"},
    {"label": "Machine Learning", "value": "ml"},
    {"label": "Communication", "value": "communication"},
    {"label": "Gestion de projet", "value": "gestion_projet"},
    {"label": "Analyse de données", "value": "analyse_donnees"},
    {"label": "Support client", "value": "support_client"},
    {"label": "Saisie administrative", "value": "saisie_admin"},
    {"label": "Automatisation / Scripts", "value": "automatisation"},
    {"label": "Travail terrain", "value": "terrain"},
    {"label": "Pédagogie / Formation", "value": "pedagogie"},
    {"label": "Organisation", "value": "organisation"},
]

TARGET_JOBS = [
    {"label": "Data Analyst", "value": "Data Analyst"},
    {"label": "Business Analyst", "value": "Business Analyst"},
    {"label": "Chargé de projet digital", "value": "Chargé de projet digital"},
    {"label": "Product Operations", "value": "Product Operations"},
    {"label": "Consultant BI", "value": "Consultant BI"},
    {"label": "Chef de projet IA / Data", "value": "Chef de projet IA / Data"},
]

KEYWORD_MAP = {
    "python": [r"\bpython\b"],
    "sql": [r"\bsql\b", r"\bmysql\b", r"\bpostgres\b"],
    "excel": [r"\bexcel\b", r"\breporting\b", r"\btableaux?\b"],
    "powerbi": [r"\bpower\s?bi\b", r"\bdataviz\b", r"\bvisualisation\b"],
    "ml": [r"\bmachine learning\b", r"\bdeep learning\b", r"\bmod[eè]le\b"],
    "communication": [r"\bcommunication\b", r"\bprésentation\b", r"\banimation\b"],
    "gestion_projet": [r"\bgestion de projet\b", r"\bpilotage\b", r"\bcoordination\b"],
    "analyse_donnees": [r"\banalyse de donn[ée]es\b", r"\bdata analysis\b", r"\bkpi\b"],
    "support_client": [r"\bsupport client\b", r"\bservice client\b", r"\brelation client\b"],
    "saisie_admin": [r"\bsaisie\b", r"\badministratif\b", r"\bback office\b"],
    "automatisation": [r"\bautomatisation\b", r"\bscript\b", r"\bworkflow\b"],
    "terrain": [r"\bterrain\b", r"\bopérationnel\b", r"\bintervention\b"],
    "pedagogie": [r"\bformation\b", r"\bpédagogie\b", r"\btransmission\b"],
    "organisation": [r"\borganisation\b", r"\bplanification\b", r"\bprocess\b"],
}

SKILL_LABELS = {item["value"]: item["label"] for item in SKILL_OPTIONS}


def extract_skills_from_cv(text):
    if not text:
        return []

    text = text.lower()
    found = []
    for skill, patterns in KEYWORD_MAP.items():
        for pattern in patterns:
            if re.search(pattern, text):
                found.append(skill)
                break
    return found


def compute_demo_risk(skills):
    high_risk = {"saisie_admin", "excel", "support_client"}
    low_risk = {"communication", "gestion_projet", "pedagogie", "terrain"}
    future_ready = {"python", "sql", "powerbi", "ml", "analyse_donnees", "automatisation"}

    score = 50

    for skill in skills:
        if skill in high_risk:
            score += 12
        if skill in low_risk:
            score -= 10
        if skill in future_ready:
            score -= 8

    score = max(10, min(score, 90))

    if score >= 65:
        level = "Fort"
        reason = "Le profil contient plusieurs tâches potentiellement standardisables ou automatisables."
    elif score >= 40:
        level = "Moyen"
        reason = "Le profil combine des tâches partiellement automatisables et des compétences plus différenciantes."
    else:
        level = "Faible"
        reason = "Le profil repose davantage sur l’analyse, la coordination, la communication ou des compétences techniques à forte valeur."
    return level, score, reason


def build_result_card(title, content, icon):
    return html.Div(
        [
            html.Div(icon, className="result-icon"),
            html.Div(
                [
                    html.Div(title, className="result-card-title"),
                    content,
                ],
                className="result-card-body",
            ),
        ],
        className="glass-card result-card",
    )


layout = html.Div(
    [
        html.Div(className="bg-orb orb-1"),
        html.Div(className="bg-orb orb-2"),
        html.Div(className="bg-orb orb-3"),

        dbc.Container(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div("Career Navigator", className="brand-title"),
                                html.Div("Page analyse guidée", className="brand-subtitle"),
                            ],
                            className="brand-block",
                        ),
                        html.Div(
                            [
                                dbc.Button("Accueil", href="/", className="nav-ghost-btn"),
                                dbc.Button("Dashboard", href="/dashboard", className="nav-primary-btn"),
                            ],
                            className="nav-actions",
                        ),
                    ],
                    className="top-nav-modern",
                ),

                html.Div(
                    [
                        html.Div("Analyse profil", className="eyebrow-pill"),
                        html.H1(
                            ["Renseigne ton profil avec une ", html.Span("expérience guidée", className="gradient-text")],
                            className="hero-title small-hero-title",
                        ),
                       
                    ],
                    className="analysis-hero",
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Button("Liste guidée", id="mode-skills-btn", n_clicks=1, className="mode-btn active"),
                                                html.Button("Copie colle ton CV", id="mode-cv-btn", n_clicks=0, className="mode-btn"),
                                            ],
                                            className="mode-switch",
                                        ),

                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Label("Sélectionne tes compétences", className="field-label"),
                                                        dcc.Dropdown(
                                                            id="skills-dropdown",
                                                            options=SKILL_OPTIONS,
                                                            multi=True,
                                                            placeholder="Choisis une ou plusieurs compétences",
                                                            className="modern-dropdown",
                                                        ),
                                                        html.Div(
                                                            "Astuce : commence avec 4 à 8 compétences principales pour un rendu plus lisible.",
                                                            className="field-help",
                                                        ),
                                                    ],
                                                    id="skills-panel",
                                                    className="input-panel",
                                                ),

                                                html.Div(
                                                    [
                                                        html.Label("Colle ici le texte du CV", className="field-label"),
                                                        dcc.Textarea(
                                                            id="cv-text",
                                                            placeholder="Exemple : Data analyst junior, reporting Excel, SQL, dashboarding, coordination projet...",
                                                            className="modern-textarea",
                                                        ),
                                                        
                                                    ],
                                                    id="cv-panel",
                                                    className="input-panel",
                                                    style={"display": "none"},
                                                ),

                                                html.Div(
                                                    [
                                                        html.Label("Métier cible", className="field-label"),
                                                        dcc.Dropdown(
                                                            id="target-job",
                                                            options=TARGET_JOBS,
                                                            placeholder="Choisis un métier cible",
                                                            className="modern-dropdown",
                                                        ),
                                                    ],
                                                    className="input-panel",
                                                ),

                                                html.Div(
                                                    [
                                                        dbc.Button("Lancer une prévisualisation", id="analyze-btn", className="hero-primary-btn"),
                                                        dbc.Button("Réinitialiser", id="reset-btn", className="hero-secondary-btn"),
                                                    ],
                                                    className="analysis-actions",
                                                ),
                                            ],
                                            className="glass-card input-card",
                                        )
                                    ]
                                )
                            ],
                            lg=8,
                            className="mb-4",
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Div("Sorties prévues", className="section-kicker"),
                                        html.H3("Ce que l’outil retournera", className="side-title"),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Div("1", className="mini-step"),
                                                        html.Div(
                                                            [
                                                                html.Div("Score d’exposition IA", className="mini-step-title"),
                                                                html.Div("Faible / moyen / fort avec justification.", className="mini-step-text"),
                                                            ]
                                                        ),
                                                    ],
                                                    className="mini-step-card",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Div("2", className="mini-step"),
                                                        html.Div(
                                                            [
                                                                html.Div("Métiers voisins", className="mini-step-title"),
                                                                html.Div("Alternatives plus résilientes et passerelles.", className="mini-step-text"),
                                                            ]
                                                        ),
                                                    ],
                                                    className="mini-step-card",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Div("3", className="mini-step"),
                                                        html.Div(
                                                            [
                                                                html.Div("Plan de montée en compétences", className="mini-step-title"),
                                                                html.Div("Skill gap entre profil actuel et métier cible.", className="mini-step-text"),
                                                            ]
                                                        ),
                                                    ],
                                                    className="mini-step-card",
                                                ),
                                            ]
                                        ),
                                    
                                    ],
                                    className="glass-card side-card",
                                )
                            ],
                            lg=4,
                            className="mb-4",
                        ),
                    ]
                ),

                html.Div(
                    id="analysis-preview",
                    className="results-zone",
                    children=[
                        html.Div(
                            [
                                html.Div("Prévisualisation", className="section-kicker"),
                                html.H2("La restitution apparaîtra ici après clic.", className="section-title"),
                                
                            ],
                            className="glass-card placeholder-card",
                        )
                    ],
                ),
            ],
            fluid=True,
            className="landing-container",
        ),
    ],
    className="page-home-modern",
)


@callback(
    Output("skills-panel", "style"),
    Output("cv-panel", "style"),
    Output("mode-skills-btn", "className"),
    Output("mode-cv-btn", "className"),
    Input("mode-skills-btn", "n_clicks"),
    Input("mode-cv-btn", "n_clicks"),
)
def toggle_mode(n_skills, n_cv):
    trigger = ctx.triggered_id

    if trigger == "mode-cv-btn":
        return {"display": "block"}, {"display": "block"}, "mode-btn", "mode-btn active"

    return {"display": "block"}, {"display": "none"}, "mode-btn active", "mode-btn"


@callback(
    Output("skills-dropdown", "value"),
    Output("cv-text", "value"),
    Output("target-job", "value"),
    Input("reset-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_form(_):
    return [], "", None


@callback(
    Output("analysis-preview", "children"),
    Input("analyze-btn", "n_clicks"),
    State("skills-dropdown", "value"),
    State("cv-text", "value"),
    State("target-job", "value"),
    State("mode-cv-btn", "className"),
)
def preview_analysis(n_clicks, skills, cv_text, target_job, cv_mode_class):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    is_cv_mode = "active" in (cv_mode_class or "")
    selected_skills = skills or []

    if is_cv_mode:
        extracted = extract_skills_from_cv(cv_text or "")
        selected_skills = extracted

    readable_skills = [SKILL_LABELS[s] for s in selected_skills if s in SKILL_LABELS]
    level, score, reason = compute_demo_risk(selected_skills)

    if target_job:
        if target_job == "Data Analyst":
            missing = ["SQL", "Power BI / DataViz", "Analyse de données"]
        elif target_job == "Consultant BI":
            missing = ["Power BI / DataViz", "SQL", "Communication"]
        elif target_job == "Chef de projet IA / Data":
            missing = ["Gestion de projet", "Communication", "Machine Learning"]
        else:
            missing = ["Gestion de projet", "Analyse de données", "Communication"]
    else:
        missing = ["Choisis un métier cible pour calculer un skill gap plus réaliste"]

    nearby_jobs = ["Business Analyst", "Consultant BI", "Product Operations"]
    if "python" in selected_skills or "analyse_donnees" in selected_skills:
        nearby_jobs = ["Data Analyst", "BI Analyst", "Chargé d’études"]
    if "gestion_projet" in selected_skills or "communication" in selected_skills:
        nearby_jobs = ["Chef de projet digital", "Product Operations", "Consultant fonctionnel"]

    summary_text = (
        "Mode CV texte activé. Compétences détectées automatiquement : "
        if is_cv_mode else
        "Mode liste guidée activé. Compétences sélectionnées : "
    )

    return [
        html.Div(
            [
                html.Div("Résultat démo", className="section-kicker"),
                html.H2("Une restitution plus premium, claire et actionnable.", className="section-title"),
                html.P(
                    "Cette sortie est une simulation UX pour travailler le produit",
                    className="section-text",
                ),
            ],
            className="section-heading",
        ),
        dbc.Row(
            [
                dbc.Col(
                    build_result_card(
                        "Profil détecté",
                        html.Div(
                            [
                                html.P(summary_text, className="result-text"),
                                html.Div(
                                    [html.Span(skill, className="result-chip") for skill in readable_skills] or
                                    [html.Span("Aucune compétence détectée pour l’instant", className="result-chip muted-chip")],
                                    className="result-chip-row",
                                ),
                            ]
                        ),
                        "🧩",
                    ),
                    lg=4,
                    className="mb-4",
                ),
                dbc.Col(
                    build_result_card(
                        "Exposition IA / automatisation",
                        html.Div(
                            [
                                html.Div(f"{level} • {score}/100", className="result-score"),
                                html.P(reason, className="result-text"),
                            ]
                        ),
                        "🤖",
                    ),
                    lg=4,
                    className="mb-4",
                ),
                dbc.Col(
                    build_result_card(
                        "Métiers voisins",
                        html.Div(
                            [
                                html.Div(
                                    [html.Span(job, className="result-chip") for job in nearby_jobs],
                                    className="result-chip-row",
                                ),
                                html.P("Des alternatives plus résilientes ou proches peuvent être proposées ici.", className="result-text"),
                            ]
                        ),
                        "🔁",
                    ),
                    lg=4,
                    className="mb-4",
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    build_result_card(
                        "Métier cible",
                        html.Div(
                            [
                                html.Div(target_job or "Non renseigné", className="result-highlight"),
                                html.P("Choisis un métier cible pour guider le skill gap.", className="result-text"),
                            ]
                        ),
                        "🎯",
                    ),
                    lg=4,
                    className="mb-4",
                ),
                dbc.Col(
                    build_result_card(
                        "Plan de montée en compétences",
                        html.Div(
                            [
                                html.Div(
                                    [html.Span(item, className="result-chip") for item in missing],
                                    className="result-chip-row",
                                ),
                               
                            ]
                        ),
                        "📈",
                    ),
                    lg=8,
                    className="mb-4",
                ),
            ]
        ),
    ]