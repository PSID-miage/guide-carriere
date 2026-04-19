
import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__, path="/", name="Accueil")


def stat_card(value, label, accent):
    return dbc.Col(
        html.Div(
            [
                html.Div(value, className="stat-value"),
                html.Div(label, className="stat-label"),
            ],
            className=f"glass-card stat-card accent-{accent}",
        ),
        xs=12,
        sm=6,
        lg=3,
        className="mb-4",
    )


def feature_card(icon, title, text, badge):
    return dbc.Col(
        html.Div(
            [
                html.Div(icon, className="feature-icon"),
                html.Div(badge, className="feature-badge"),
                html.H4(title, className="feature-title"),
                html.P(text, className="feature-text"),
            ],
            className="glass-card feature-card reveal-up",
        ),
        xs=12,
        md=6,
        lg=4,
        className="mb-4",
    )


def step_card(step, title, text):
    return dbc.Col(
        html.Div(
            [
                html.Div(step, className="step-index"),
                html.H5(title, className="step-title"),
                html.P(text, className="step-text"),
            ],
            className="glass-card step-card",
        ),
        xs=12,
        md=6,
        lg=3,
        className="mb-4",
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
                                html.Div("Orientation carrière", className="brand-subtitle"),
                            ],
                            className="brand-block",
                        ),
                        html.Div(
                            [
                                dbc.Button("Découvrir l’outil", href="/ml", className="nav-ghost-btn"),
                                dbc.Button("Explorer le Dashboard", href="/dashboard", className="nav-primary-btn"),
                            ],
                            className="nav-actions",
                        ),
                    ],
                    className="top-nav-modern",
                ),

                html.Section(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div("Gagne du temps et cible mieux", className="eyebrow-pill"),
                                        html.H1(
                                            [
                                                "Pilote ton avenir avec une ",
                                                html.Span("cartographie carrière", className="gradient-text"),
                    
                                            ],
                                            className="hero-title",
                                        ),
                                        html.Div(
                                            "Exposition à l’automatisation, métiers voisins et plan de montée en compétences.",
                                            className="typing-line",
                                        ),
                                        html.P(
                                            "Un outil d’orientation moderne pour aider un utilisateur à comprendre son profil, "
                                            "se positionner sur des métiers proches, identifier ses gaps de compétences et "
                                            "viser des trajectoires plus résilientes face à l’IA.",
                                            className="hero-text",
                                        ),
                                       
                                        html.Div(
                                            [
                                                html.Div("Sans LinkedIn pour le MVP", className="mini-chip"),
                                                html.Div("Saisie guidée + CV texte", className="mini-chip"),
                                                html.Div("Dashboard Power BI ", className="mini-chip"),
                                            ],
                                            className="chips-row",
                                        ),
                                    ],
                                    xs=12,
                                    lg=7,
                                    className="hero-left",
                                ),
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Div("Score IA", className="visual-label"),
                                                        html.Div("Moyen", className="visual-value"),
                                                        html.Div("expliqué par tâches et compétences", className="visual-sub"),
                                                    ],
                                                    className="floating-panel panel-a",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Div("Métiers voisins", className="visual-label"),
                                                        html.Div("Data Analyst • BI • Product Owner", className="visual-sub big"),
                                                    ],
                                                    className="floating-panel panel-b",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Div("Skill Gap", className="visual-label"),
                                                        html.Div("Python • SQL • DataViz", className="visual-sub big"),
                                                    ],
                                                    className="floating-panel panel-c",
                                                ),
                                                html.Div(className="hero-ring"),
                                                html.Div(className="hero-grid"),
                                        
                                            ],
                                            className="hero-visual-card",
                                        )
                                    ],
                                    xs=12,
                                    lg=5,
                                    className="hero-right",
                                ),
                            ],
                            align="center",
                            className="hero-row",
                        )
                    ],
                    className="hero-section-modern",
                ),

                html.Section(
                    [
                        dbc.Row(
                            [
                    
                                stat_card("ROME ", "référentiels publics mobilisés", "blue"),
                                stat_card("CV + Skills", "deux modes d’entrée guidés", "green"),
                                stat_card("MVP réaliste", "sans dépendre de LinkedIn", "orange"),
                            ]
                        )
                    ],
                    className="stats-section",
                ),

                html.Section(
                    [
                        html.Div(
                            [
                                html.Div("Ce que fait la plateforme", className="section-kicker"),
                                html.H2("Une interface claire, crédible et orientée décision", className="section-title"),
                                html.P(
                                    "Le but n’est pas juste d’afficher un formulaire mais de proposer une expérience découverte "
                                    " avec des blocs de valeur, des parcours simples et une restitution utile.",
                                    className="section-text",
                                ),
                            ],
                            className="section-heading",
                            id="features",
                        ),
                        dbc.Row(
                            [
                                feature_card(
                                    "🧭",
                                    "Positionnement métier",
                                    "L’utilisateur renseigne ses compétences ou colle son CV puis on le situe sur une cartographie de métiers proche de son profil.",
                                    "Entrée guidée",
                                ),
                                feature_card(
                                    "🤖",
                                    "Exposition à l’automatisation ",
                                    "Un score faible, moyen ou fort justifié par les tâches répétitives, automatisables ou au contraire plus complexes et humaines.",
                                    "Explicable",
                                ),
                                feature_card(
                                    "🌱",
                                    "Plan de montée en compétences",
                                    "On identifie les compétences manquantes entre le profil actuel et un métier cible pour produire un plan d’évolution concret.",
                                    "Actionnable",
                                ),
                                feature_card(
                                    "🔁",
                                    "Métiers voisins et alternatives",
                                    "L’outil suggère des alternatives plus résilientes ou accessibles à partir des proximités de compétences et de familles métiers.",
                                    "Résilience",
                                ),
                                feature_card(
                                    "📊",
                                    "Dashboard carrière",
                                    "Une page dédiée au pilotage et à la visualisation macro : tendances, clusters métiers, référentiels et indicateurs décisionnels.",
                                    "Power BI ",
                                ),
                                feature_card(
                                    "🧩",
                                    "MVP réaliste",
                                    "Le MVP repose sur des référentiels publics, une saisie guidée, du CV texte ",
                                    "Pragmatique",
                                ),
                            ]
                        ),
                    ],
                    className="content-section",
                ),

                html.Section(
                    [
                        html.Div(
                            [
                                html.Div("Parcours utilisateur", className="section-kicker"),
                                html.H2("Un flow simple en 4 étapes.", className="section-title"),
                            ],
                            className="section-heading",
                        ),
                        dbc.Row(
                            [
                                step_card("01", "Entrée du profil", "Liste guidée ou copie colle du CV en texte brut."),
                                step_card("02", "Analyse du profil", "Extraction de compétences, structuration du profil, pré positionnement métier."),
                                step_card("03", "Restitution", "Score IA, métiers voisins, métiers cibles et lecture explicable."),
                                step_card("04", "Projection", "Skill gap, montée en compétences et futur matching avec offres."),
                            ]
                        ),
                    ],
                    className="content-section soft-section",
                ),
        
                html.Section(
                    [
                        html.Div(
                            [
                                html.Div("Prêt à lancer l’expérience ?", className="cta-kicker"),
                            
                                html.Div(
                                    [
                                        dbc.Button("Ouvrir la page analyse", href="/ml", className="hero-primary-btn"),
                                        dbc.Button("Accéder au dashboard", href="/dashboard", className="hero-secondary-btn"),
                                    ],
                                    className="hero-actions",
                                ),
                            ],
                            className="cta-panel",
                        )
                    ],
                    className="final-cta-section",
                ),
            ],
            fluid=True,
            className="landing-container",
        ),
    ],
    className="page-home-modern",
)