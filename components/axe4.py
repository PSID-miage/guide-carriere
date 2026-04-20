from dash import dcc, html
import dash_bootstrap_components as dbc

def render_axe4():
    return html.Div([
        # --- HEADER SECTION ---
        html.Div([
            html.Div(style={'width': '60px', 'height': '4px', 'backgroundColor': '#42b2c1', 'marginBottom': '20px', 'borderRadius': '2px'}),
            html.H2("AXE 4 : EXPLORATION DÉTAILLÉE ET ORIENTATION", 
                    style={'fontWeight': '800', 'color': "#2c3e50", 'letterSpacing': '0.5px', 'textTransform': 'uppercase'}),
            html.P("Fiche métier augmentée : référentiel de compétences, savoirs et opportunités de mobilité.",
                   style={'fontSize': '1.1rem', 'color': "#7f8c8d", 'maxWidth': '800px'})
        ], className="mb-5 mt-5"),

        # --- FICHE MÉTIER DYNAMIQUE ---
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Span("FICHE RÉFÉRENTIEL : ", style={'color': '#7f8c8d', 'fontSize': '0.9rem'}),
                        html.Strong(id="fiche-titre-metier", style={'color': '#2c3e50'})
                    ], style={'backgroundColor': 'white', 'borderBottom': '1px solid #f1f2f6', 'padding': '15px'}),
                    dbc.CardBody([
                        # Tags de transition
                        html.Div(id="metier-tags", className="mb-4 d-flex gap-2"),
                        
                        html.Div([
                            html.H6("COMPÉTENCES TECHNIQUES (SAVOIR-FAIRE)", 
                                    style={'fontSize': '0.85rem', 'fontWeight': 'bold', 'color': '#2c3e50', 'letterSpacing': '1px'}),
                            html.Div(id="fiche-competences", className="d-flex flex-wrap gap-2 mb-4", style={'paddingTop': '10px'}),
                            
                            html.H6("CONNAISSANCES ET SAVOIRS THEORIQUES", 
                                    style={'fontSize': '0.85rem', 'fontWeight': 'bold', 'color': '#2c3e50', 'letterSpacing': '1px'}),
                            html.Div(id="fiche-savoirs", className="d-flex flex-wrap gap-2 mb-4", style={'paddingTop': '10px'}),
                            
                            html.H6("CONTEXTES D'ACTIVITÉ", 
                                    style={'fontSize': '0.85rem', 'fontWeight': 'bold', 'color': '#2c3e50', 'letterSpacing': '1px'}),
                            html.Ul(id="fiche-activites", style={'fontSize': '0.9rem', 'color': '#2c3e50', 'paddingLeft': '20px', 'paddingTop': '10px'})
                        ])
                    ])
                ], className="border-0 shadow-sm h-100", style={'borderRadius': '8px'})
            ], lg=7),

            # --- G12 : RADAR RIASEC ---
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Strong("PROFIL RIASEC ESTIMÉ"), 
                                   style={'backgroundColor': 'white', 'borderBottom': 'none', 'textAlign': 'center', 'paddingTop': '15px'}),
                    dbc.CardBody([
                        dcc.Loading(dcc.Graph(id='g12-radar-riasec', config={'displayModeBar': False}))
                    ])
                ], className="border-0 shadow-sm h-100", style={'borderRadius': '8px'})
            ], lg=5),
        ], className="mb-4"),

        # --- MÉTIERS SIMILAIRES ---
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Strong("OPPORTUNITÉS DE MOBILITÉ ET ALTERNATIVES"), 
                                   style={'backgroundColor': '#f8f9fa', 'color': '#2c3e50'}),
                    dbc.CardBody([
                        html.P("Métiers présentant une forte proximité en termes de socle de compétences :", 
                               style={'fontSize': '0.9rem', 'color': '#7f8c8d'}),
                        html.Div(id="container-metiers-similaires", className="row g-3")
                    ])
                ], className="border-0 shadow-sm", style={'borderRadius': '8px'})
            ], width=12)
        ], className="mb-5")
    ], id="section-axe4", style={'display': 'none', 'paddingBottom': '50px'})