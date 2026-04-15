from dash import dcc, html
import dash_bootstrap_components as dbc

def render_axe4():
    return html.Div([
        # --- HEADER SECTION ---
        html.Div([
            html.Div(style={'width': '60px', 'height': '4px', 'backgroundColor': '#42b2c1', 'marginBottom': '20px', 'borderRadius': '2px'}),
            html.H2("AXE 4 : EXPLORATION DÉTAILLÉE & ORIENTATION", 
                    style={'fontWeight': '800', 'color': "#2c3e50", 'letterSpacing': '0.5px'}),
            html.P("Analyse approfondie des compétences issues du référentiel métier.",
                   style={'fontSize': '1.1rem', 'color': "#7f8c8d", 'maxWidth': '800px'})
        ], className="mb-5 mt-5"),

        # --- FICHE MÉTIER & RIASEC ---
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Span("RÉFÉRENTIEL MÉTIER : ", style={'color': '#7f8c8d', 'fontSize': '0.9rem', 'fontWeight': 'bold'}),
                        html.H3(id="fiche-titre-metier", style={'color': '#2c3e50', 'margin': '0', 'fontWeight': '800', 'fontSize': '1.8rem'})
                    ], style={'backgroundColor': 'white', 'borderBottom': '1px solid #f1f2f6', 'padding': '25px'}),
                    
                    dbc.CardBody([
                        html.Div(id="metier-tags", className="mb-4 d-flex gap-2"),
                        html.Div([
                            html.Label("COMPÉTENCES TECHNIQUES (SAVOIR-FAIRE)", 
                                       style={'fontSize': '0.85rem', 'fontWeight': '800', 'color': '#42b2c1', 'textTransform': 'uppercase', 'letterSpacing': '1px', 'display': 'block', 'marginBottom': '20px'}),
                            html.Div(id="fiche-competences", className="d-flex flex-column gap-3", style={'fontSize': '1.1rem'}),
                        ], style={'padding': '10px'})
                    ])
                ], className="border-0 shadow-sm h-100", style={'borderRadius': '15px'})
            ], lg=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Strong("PROFIL PSYCHOLOGIQUE (RIASEC)", style={'fontSize': '1.1rem'}), style={'backgroundColor': 'white', 'borderBottom': 'none', 'padding': '25px'}),
                    dbc.CardBody([
                        # --- BLOC EXPLICATIF RIASEC RE-AJOUTÉ ---
                        html.Div([
                            html.P([
                                html.Strong("Le modèle RIASEC", style={'color': '#42b2c1'}), 
                                " est une méthode scientifique utilisée en psychologie pour mesurer l'adéquation entre votre personnalité et votre environnement de travail."
                            ], style={'fontSize': '1rem', 'color': '#2c3e50', 'marginBottom': '15px'}),
                            
                            html.P("Ce graphique représente les 6 types de profils dominants :", style={'fontSize': '0.9rem', 'fontWeight': '600', 'marginBottom': '10px'}),
                            
                            html.Ul([
                                html.Li([html.Strong("R"), "éaliste : concret, technique"], style={'fontSize': '0.9rem'}),
                                html.Li([html.Strong("I"), "nvestigateur : analyse, recherche"], style={'fontSize': '0.9rem'}),
                                html.Li([html.Strong("A"), "rtistique : création, originalité"], style={'fontSize': '0.9rem'}),
                                html.Li([html.Strong("S"), "ocial : entraide, contact"], style={'fontSize': '0.9rem'}),
                                html.Li([html.Strong("E"), "ntreprenant : décision, leadership"], style={'fontSize': '0.9rem'}),
                                html.Li([html.Strong("C"), "onventionnel : organisation, données"], style={'fontSize': '0.9rem'}),
                            ], style={'color': '#7f8c8d', 'columnCount': 2, 'listStyleType': 'none', 'padding': '0'}),
                            
                            html.Div([
                                html.Small("💡 Un score élevé sur une dimension indique que ce trait est essentiel pour s'épanouir dans ce métier.", 
                                          style={'fontStyle': 'italic', 'color': '#95a5a6'})
                            ], className="mt-3")
                        ], className="mb-4 p-4", style={'backgroundColor': '#f8f9fa', 'borderRadius': '12px', 'borderLeft': '5px solid #42b2c1'}),
                        
                        dcc.Loading(dcc.Graph(id='g12-radar-riasec', config={'displayModeBar': False})),
                    ])
                ], className="border-0 shadow-sm h-100", style={'borderRadius': '15px'})
            ], lg=6),
        ], className="mb-5 g-4"),

        # --- MOBILITÉ ---
        html.Div([
            html.H4("PASSERELLES DE MOBILITÉ CONSEILLÉES", 
                    style={'fontWeight': '800', 'color': '#2c3e50', 'marginBottom': '30px', 'letterSpacing': '0.5px'}),
            html.Div(id="container-metiers-similaires", className="row g-4")
        ], className="mt-5 mb-5")
        
    ], id="section-axe4", style={'display': 'none'})