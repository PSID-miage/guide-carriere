from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

def render_axe3(df_gd):
    # Préparation des options pour le sélecteur
    options_domaines = [
        {'label': f"Secteur {row['code_grand_domaine']} : {row['libelle_grand_domaine']}", 
         'value': row['code_grand_domaine']} 
        for _, row in df_gd.iterrows()
    ]

    return html.Div([
        # --- EN-TÊTE ---
        html.Div([
            html.H2("AXE 3 : RELATIONS ET MOBILITÉ ENTRE MÉTIERS", 
                    style={'fontWeight': '800', 'color': "#0A0A0A", 'letterSpacing': '0.5px'}),
            html.P("Exploration visuelle des mobilités inter-métiers et analyse : Les métiers sont-ils isolés ou interconnectés ? Existe-t-il des passerelles ?",
                   style={'fontSize': '1.1rem', 'color': "#2F79B6", 'maxWidth': '800px'})
        ], className="mb-5 mt-4"),

        # --- PANNEAU DE SÉLECTION ---
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("1. Choisir un Grand Domaine", style={'fontWeight': '600', 'color': '#2c3e50', 'marginBottom': '10px'}),
                        dcc.Dropdown(id='domaine-filter', options=options_domaines, value=options_domaines[0]['value'], clearable=False, style={'borderRadius': '10px'}),
                    ], md=6),
                    dbc.Col([
                        html.Label("2. Zoomer sur un métier spécifique", style={'fontWeight': '600', 'color': '#2c3e50', 'marginBottom': '10px'}),
                        dcc.Dropdown(id='metier-zoom-filter', placeholder="Rechercher un intitulé (ex: Data Scientist)...", clearable=True, style={'borderRadius': '10px'}),
                    ], md=6),
                ])
            ], className="p-4")
        ], className="border-0 shadow-sm mb-5", style={'borderRadius': '15px'}),

        # --- RÉSEAU ET INDEX ---
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Réseau de métiers (network graph) dynamique - pour  visualiser les relations entre métiers", style={'backgroundColor': 'transparent', 'fontWeight': '700', 'borderBottom': 'none', 'paddingTop': '20px'}),
                    dbc.CardBody([
                        dcc.Loading(dcc.Graph(id='g7-net-graph', style={'height': '600px'}), type="dot", color="#8bb4ef")
                    ])
                ], className="border-0 shadow-sm h-100", style={'borderRadius': '15px'})
            ], lg=8, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Index des Métiers", style={'backgroundColor': 'transparent', 'fontWeight': '700', 'borderBottom': 'none', 'paddingTop': '20px'}),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='table-legende',
                            columns=[{"name": "CODE ROME", "id": "code_rome"}, {"name": "INTITULÉ", "id": "libelle_rome"}],
                            style_table={'height': '540px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '15px', 'fontFamily': 'sans-serif', 'fontSize': '13px', 'borderBottom': '1px solid #f1f2f6'},
                            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'fontSize': '11px', 'color': '#8395a7'},
                            fixed_rows={'headers': True},
                        )
                    ], className="p-0")
                ], className="border-0 shadow-sm h-100", style={'borderRadius': '15px'})
            ], lg=4, className="mb-4"),
        ], className="mb-5"),

        # --- SECTION G8 : PIVOTS ---
        html.Div([
            html.Div(style={'width': '60px', 'height': '4px', 'backgroundColor': "#71a9e1", 'marginBottom': '20px', 'borderRadius': '2px'}),
            html.H4("Top 10 : Les Métiers Pivots", style={'fontWeight': '700', 'color': '#2c3e50'}),
            html.P("Métiers possédant le plus haut taux d'interconnectivité (entrante et sortante).",
                   style={'color': '#718093', 'marginBottom': '30px'})
        ], className="mt-5"),

        dbc.Card([
            dbc.CardBody([
                dcc.Loading(dcc.Graph(id='g8-pivots-graph', config={'displayModeBar': False}))
            ], className="p-4")
        ], className="border-0 shadow-sm mb-5", style={'borderRadius': '15px'}),

        # --- SECTION G10 : GLOBAL ---
        html.Div([
            html.Div(style={'width': '60px', 'height': '4px', 'backgroundColor': '#6f42c1', 'marginBottom': '20px', 'borderRadius': '2px'}),
            html.H4("Bar Chart de Potentiel de Mobilité : ouverture à la Mobilité par Secteur", style={'fontWeight': '700', 'color': '#2c3e50'}),
            html.P("Analyse du nombre moyen de passerelles sortantes par métier pour chaque grand domaine.",
                   style={'color': '#718093', 'marginBottom': '30px'})
        ], className="mt-5"),

        dbc.Card([
            dbc.CardBody([
                dcc.Loading(dcc.Graph(id='g10-potentiel-global', config={'displayModeBar': False}))
            ], className="p-4")
        ], className="border-0 shadow-sm mb-5", style={'borderRadius': '15px'})

    ], style={'padding': '40px 60px', 'backgroundColor': '#f8f9fb', 'minHeight': '100vh', 'fontFamily': 'Segoe UI, sans-serif'})