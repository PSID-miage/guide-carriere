import pandas as pd
import base64
import io
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from urllib.parse import parse_qs, unquote
import os

# Import pour l'extraction de texte PDF (Analyse de CV)
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

dash.register_page(__name__, path="/ml", name="Analyse Profil")

# ==========================================================
# PARTIE 1 : MOTEUR DE MACHINE LEARNING (LOGIQUE NLP)
# ==========================================================

class ROMEAIEngine:
    def __init__(self, data_path="data/"):
        self.data_path = data_path
        self.df_trained = self._build_knowledge_base()
        
        if self.df_trained.empty:
            self.df_trained = pd.DataFrame({
                'libelle_rome': ['Dataset non chargé'], 
                'code_rome': ['N/A'], 
                'all_text_knowledge': [''],
                'transition_num': [0]
            })

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            stop_words=['ce', 'le', 'la', 'de', 'du', 'en', 'et', 'un', 'une', 'des', 'les', 'pour']
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df_trained['all_text_knowledge'])

    def _build_knowledge_base(self):
        try:
            def safe_read(name):
                path = os.path.join(self.data_path, name)
                if not os.path.exists(path): return pd.DataFrame()
                return pd.read_csv(path, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')

            df_rome = safe_read("unix_referentiel_code_rome_v460_utf8.csv")
            df_liens = safe_read("unix_liens_rome_referentiels_v460_utf8.csv")
            df_comp = safe_read("unix_referentiel_competence_v460_utf8.csv")
            df_savoir = safe_read("unix_referentiel_savoir_v460_utf8.csv")

            if df_rome.empty: return pd.DataFrame()
            for df in [df_rome, df_liens, df_comp, df_savoir]:
                if not df.empty: df.columns = df.columns.str.strip()

            comp_merged = df_liens[df_liens['code_compo_bloc'] == 5].merge(df_comp, on='code_ogr', how='inner')
            agg_comp = comp_merged.groupby('code_rome')['libelle_competence'].apply(list).reset_index()

            savoir_merged = df_liens.merge(df_savoir, left_on='code_ogr', right_on='code_ogr_savoir', how='inner')
            agg_savoir = savoir_merged.groupby('code_rome')['libelle_savoir'].apply(list).reset_index()

            final_df = df_rome.merge(agg_comp, on='code_rome', how='left')
            final_df = final_df.merge(agg_savoir, on='code_rome', how='left')
            
            final_df['all_text_knowledge'] = (
                final_df['libelle_rome'].fillna('') + " " + 
                final_df['libelle_competence'].apply(lambda x: " ".join(x) if isinstance(x, list) else "") + " " + 
                final_df['libelle_savoir'].apply(lambda x: " ".join(x) if isinstance(x, list) else "")
            ).str.lower().str.strip()
            return final_df
        except: return pd.DataFrame()

    def predict(self, user_input, top_n=3):
        if not user_input or len(user_input) < 10: return []
        user_vec = self.vectorizer.transform([user_input.lower()])
        similarities = cosine_similarity(user_vec, self.tfidf_matrix).flatten()
        best_indices = similarities.argsort()[-top_n:][::-1]
        results = []
        for i in best_indices:
            if similarities[i] > 0.02:
                row = self.df_trained.iloc[i]
                results.append({'metier': row['libelle_rome'], 'code': row['code_rome'], 'score': round(similarities[i] * 100, 1)})
        return results

    # --- LOGIQUE ML POUR LE BAS DE FICHE ---
    def get_ia_impact(self, row):
        content = str(row['all_text_knowledge'])
        ia_keywords = ['analyser', 'données', 'statistiques', 'prévision', 'algorithme', 'calcul', 'numérique']
        score = sum(1 for kw in ia_keywords if kw in content)
        if score >= 3: return "Élevé", "Forte mutation des tâches via l'automatisation des données."
        return "Modéré", "L'IA assiste les tâches de gestion et d'analyse d'informations."

    def get_passerelles(self, code_rome):
        idx = self.df_trained[self.df_trained['code_rome'] == code_rome].index[0]
        sims = cosine_similarity(self.tfidf_matrix[idx], self.tfidf_matrix).flatten()
        related = sims.argsort()[-4:-1][::-1]
        return self.df_trained.iloc[related]['libelle_rome'].tolist()

    def get_skill_gap(self, user_text, code_rome):
        row = self.df_trained[self.df_trained['code_rome'] == code_rome].iloc[0]
        skills = row['libelle_competence']
        if not skills or not user_text: return ["Analyse impossible"]
        gap = [s for s in skills if s.lower() not in str(user_text).lower()]
        return gap[:3]

engine = ROMEAIEngine()

# ==========================================================
# PARTIE 2 : INTERFACE
# ==========================================================

def get_ml_main_layout():
    return html.Div([
        html.Div([
            html.H1(["Analyse Profil & ", html.Span("Machine Learning", className="gradient-text")]),
            html.P("Découvrez les métiers du ROME qui correspondent à votre expérience.")
        ], className="analysis-hero text-center mb-5"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Button("Texte libre", id="mode-cv-btn", n_clicks=1, className="mode-btn active"),
                        html.Button("Upload PDF", id="mode-pdf-btn", n_clicks=0, className="mode-btn"),
                    ], className="mode-switch mb-4"),
                    html.Div([
                        html.Div([dcc.Textarea(id="cv-text", className="modern-textarea", placeholder="Collez vos compétences...")], id="cv-panel"),
                        html.Div([dcc.Upload(id="upload-data", children=html.Div(['Cliquez pour uploader']), className="pdf-upload-zone")], id="pdf-panel", style={"display": "none"}),
                        dbc.Button("Exécuter l'Analyse", id="analyze-btn", className="hero-primary-btn mt-4"),
                    ], className="glass-card p-4")
                ])
            ], lg=8)
        ], justify="center"),
        html.Div(id="analysis-preview", className="mt-5")
    ])

def get_fiche_metier_layout(job_code, user_data):
    row = engine.df_trained[engine.df_trained['code_rome'] == job_code].iloc[0]
    ia_val, ia_txt = engine.get_ia_impact(row)
    passerelles = engine.get_passerelles(job_code)
    gap = engine.get_skill_gap(user_data, job_code)

    return html.Div([
        dcc.Link("← Retour", href="/ml", className="back-link mb-4"),
        html.H1(row['libelle_rome'], className="gradient-text mb-5"),
        
        dbc.Row([
            dbc.Col(html.Div([
                html.Div("Savoir-faire opérationnels", className="result-card-title"),
                html.Ul([html.Li(c, className="list-item-ml") for c in row['libelle_competence'][:10]])
            ], className="glass-card p-4"), lg=6),
            dbc.Col(html.Div([
                html.Div("Savoirs théoriques", className="result-card-title"),
                html.Ul([html.Li(s, className="list-item-ml") for s in row['libelle_savoir'][:10]])
            ], className="glass-card p-4"), lg=6),
        ]),

        html.Div([
            dbc.Row([
                dbc.Col(html.Div([
                    html.Div("1. Score d'Exposition IA", className="footer-card-title"),
                    html.H3(ia_val, style={"color": "#00d4ff"}), html.P(ia_txt, className="footer-desc")
                ], className="footer-sub-card"), lg=4),
                dbc.Col(html.Div([
                    html.Div("2. Métiers Voisins", className="footer-card-title"),
                    html.H3("Passerelles", className="footer-main-val"),
                    html.Ul([html.Li(p, className="footer-desc") for p in passerelles])
                ], className="footer-sub-card"), lg=4),
                dbc.Col(html.Div([
                    html.Div("3. Plan de Montée", className="footer-card-title"),
                    html.H3("Skill Gap", className="footer-main-val"),
                    html.Ul([html.Li(g, className="footer-desc", style={"color":"#e5e8ec"}) for g in gap])
                ], className="footer-sub-card"), lg=4),
            ])
        ], className="footer-analysis-zone mt-4")
    ])

# ==========================================================
# PARTIE 3 : ROUTING & CALLBACKS
# ==========================================================

layout = html.Div([
    dcc.Location(id='url-ml', refresh=False),
    html.Div(id='page-content-ml', className="landing-container")
])

@callback(
    Output('page-content-ml', 'children'),
    [Input('url-ml', 'search')],
    [State('cv-data-store', 'data')] # Utilisation de ton ID existant
)
def router(search, store_data):
    if search:
        params = parse_qs(search.lstrip('?'))
        if 'code' in params: return get_fiche_metier_layout(unquote(params['code'][0]), store_data)
    return get_ml_main_layout()

@callback(
    [Output("cv-panel", "style"), Output("pdf-panel", "style"),
     Output("mode-cv-btn", "className"), Output("mode-pdf-btn", "className")],
    [Input("mode-cv-btn", "n_clicks"), Input("mode-pdf-btn", "n_clicks")]
)
def toggle_mode(n1, n2):
    if ctx.triggered_id == "mode-pdf-btn":
        return {"display":"none"}, {"display":"block"}, "mode-btn", "mode-btn active"
    return {"display":"block"}, {"display":"none"}, "mode-btn active", "mode-btn"

@callback(
    [Output("analysis-preview", "children"), Output("cv-data-store", "data")], # Sauvegarde dans ton ID existant
    Input("analyze-btn", "n_clicks"),
    State("cv-text", "value"),
    State("upload-data", "contents"),
    State("mode-cv-btn", "className"),
)
def execute_analysis(n, text, pdf, c1):
    if not n: raise dash.exceptions.PreventUpdate
    source = text if "active" in c1 else ""
    if not source and pdf:
        content_string = pdf.split(',')[1]
        decoded = base64.b64decode(content_string)
        reader = PyPDF2.PdfReader(io.BytesIO(decoded))
        source = " ".join([p.extract_text() for p in reader.pages])

    recs = engine.predict(source)
    if not recs: return dbc.Alert("Analyse impossible."), source

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span(r['metier'], className="result-highlight"),
                    dcc.Link(" Fiche ➜", href=f"/ml?code={r['code']}", className="fiche-link")
                ], className="glass-card p-3 mb-2") for r in recs
            ], lg=7)
        ])
    ]), source