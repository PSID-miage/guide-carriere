import pandas as pd
import numpy as np
import base64
import io
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics.pairwise import cosine_similarity
from urllib.parse import parse_qs, unquote
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Import pour l'extraction de texte PDF (Analyse de CV)
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# PROTECTION : dash.register_page ne s'exécute que si le script est appelé par l'app principale
if __name__ != "__main__":
    dash.register_page(__name__, path="/ml", name="Analyse Profil")

# ==========================================================
# PARTIE 1 : MOTEUR DE MACHINE LEARNING (LOGIQUE KNN & NLP)
# ==========================================================

class ROMEAIEngine:
    def __init__(self, data_path="data/"):
        self.data_path = data_path
        
        # ------------------------------------------------------
        # ÉTAPE 1 : DATA PREPARATION (Fusion des données)
        # ------------------------------------------------------
        self.df_trained = self._build_knowledge_base()
        
        if self.df_trained.empty:
            self.df_trained = pd.DataFrame({
                'libelle_rome': ['Dataset non chargé'], 
                'code_rome': ['N/A'], 
                'all_text_knowledge': [''],
                'transition_num': [0]
            })

        # ------------------------------------------------------
        # ÉTAPE 2 : VECTORISATION & POIDS DES MOTS (TF-IDF)
        # ------------------------------------------------------
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            max_df=0.5, # Élimine les mots trop communs (bruit statistique)
            min_df=2,
            stop_words=['ce', 'le', 'la', 'de', 'du', 'en', 'et', 'un', 'une', 'des', 'les', 'pour']
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df_trained['all_text_knowledge'])

        # ------------------------------------------------------
        # ÉTAPE 3 : TRAINING (KNN - K-Nearest Neighbors)
        # ------------------------------------------------------
        self.knn_model = KNeighborsClassifier(n_neighbors=5, metric='cosine')
        self.knn_model.fit(self.tfidf_matrix, self.df_trained['code_rome'])

    def _build_knowledge_base(self):
        """ Nettoyage et fusion des référentiels ROME """
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

    # ------------------------------------------------------
    # ÉTAPE 4 : PREDICTION (Inférence avec filtrage Famille)
    # ------------------------------------------------------
    def predict(self, user_input, top_n=3, families=None):
        """ Recommandation avec contrôle du signal (min 50 car.) """
        if not user_input or len(user_input) < 50: 
            return "SIGNAL_INSUFFISANT"
        
        user_vec = self.vectorizer.transform([user_input.lower()])
        
        if families:
            mask = self.df_trained['code_rome'].str.startswith(tuple(families))
            filtered_indices = np.where(mask)[0]
            if len(filtered_indices) == 0: return []

            sub_matrix = self.tfidf_matrix[filtered_indices]
            sims = cosine_similarity(user_vec, sub_matrix).flatten()
            best_sub_indices = sims.argsort()[-top_n:][::-1]
            results_indices = filtered_indices[best_sub_indices]
            scores = sims[best_sub_indices]
        else:
            distances, indices = self.knn_model.kneighbors(user_vec, n_neighbors=top_n)
            results_indices = indices[0]
            scores = [1 - d for d in distances[0]]

        results = []
        for i, idx in enumerate(results_indices):
            confiance = round(scores[i] * 100, 1)
            if confiance > 10:
                row = self.df_trained.iloc[idx]
                results.append({'metier': row['libelle_rome'], 'code': row['code_rome'], 'score': confiance})
        return results

    # ------------------------------------------------------
    # ÉTAPE 5 : VALIDATION (Matrice de Similarité Visuelle)
    # ------------------------------------------------------
    def generate_visual_matrix(self, target_rome_code, n_neighbors=8):
        """ Génère une Heatmap pour le rapport de projet """
        try:
            idx = self.df_trained[self.df_trained['code_rome'] == target_rome_code].index[0]
            sims = cosine_similarity(self.tfidf_matrix[idx], self.tfidf_matrix).flatten()
            nearest_indices = sims.argsort()[-n_neighbors:][::-1]
            
            sub_matrix = cosine_similarity(self.tfidf_matrix[nearest_indices])
            labels = [l[:20] + '..' for l in self.df_trained.iloc[nearest_indices]['libelle_rome'].values]

            plt.figure(figsize=(10, 8))
            sns.heatmap(sub_matrix, annot=True, fmt=".2f", cmap='YlGnBu', xticklabels=labels, yticklabels=labels)
            plt.title(f"Matrice de Similarité - Focus sur {labels[0]}")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig("matrice_similarite_rapport.png")
            plt.close()
            return "✅ Succès : Image 'matrice_similarite_rapport.png' créée."
        except Exception as e:
            return f"❌ Erreur : {str(e)}"

    # ------------------------------------------------------
    # ÉTAPE 6 : LOGIQUE POST-ML (Impact IA, Passerelles, Gap)
    # ------------------------------------------------------
    def get_ia_impact(self, row):
        try:
            raw_val = str(row.get('transition_num', 0)).replace('O', '0').strip()
            trans_score = float(raw_val)
        except (ValueError, TypeError):
            trans_score = 0.0

        content = str(row['all_text_knowledge'])
        ia_keywords = ['analyser', 'données', 'statistiques', 'algorithme', 'calcul', 'automatisé']
        has_keywords = sum(1 for kw in ia_keywords if kw in content)

        if trans_score >= 4 or (trans_score >= 3 and has_keywords >= 2):
            return "Élevé", "Forte mutation des tâches détectée par le modèle."
        elif trans_score >= 2 or has_keywords >= 1:
            return "Modéré", "L'IA assiste les tâches d'analyse documentaire."
        return "Faible", "Métier à forte composante humaine."

    def get_passerelles(self, code_rome):
        """ Utilise la Matrice de Similarité pour trouver des voisins """
        idx = self.df_trained[self.df_trained['code_rome'] == code_rome].index[0]
        sims = cosine_similarity(self.tfidf_matrix[idx], self.tfidf_matrix).flatten()
        related_indices = sims.argsort()[-5:-1][::-1] 
        return self.df_trained.iloc[related_indices]['libelle_rome'].tolist()

    def get_skill_gap(self, user_text, code_rome):
        row = self.df_trained[self.df_trained['code_rome'] == code_rome].iloc[0]
        required_skills = row['libelle_competence']
        if not required_skills or not user_text: return ["Analyse impossible"]
        user_text_lower = user_text.lower()
        gap = []
        for skill in required_skills:
            words = [w for w in skill.lower().split() if len(w) > 3]
            if not any(word in user_text_lower for word in words): gap.append(skill)
        return gap[:3]

# Initialisation
engine = ROMEAIEngine()

# ==========================================================
# PARTIE 2 : INTERFACE & DASH LOGIC
# ==========================================================

def get_ml_main_layout():
    return html.Div([
        html.Div([
            html.H1(["Analyse Profil & ", html.Span("Machine Learning", className="gradient-text")]),
            html.P("Découvrez les métiers du ROME via classification KNN.")
        ], className="analysis-hero text-center mb-5"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label("Domaine de recherche :", className="text-white mb-2"),
                    dcc.Dropdown(
                        id="family-filter",
                        options=[
                            {'label': 'Artisanat & Commerce (D)', 'value': 'D'},
                            {'label': 'Construction & BTP (F)', 'value': 'F'},
                            {'label': 'Management & Informatique (M)', 'value': 'M'},
                            {'label': 'Tous les secteurs', 'value': 'ALL'}
                        ], value='ALL', className="mb-4 text-dark"
                    ),
                    html.Div([
                        html.Button("Texte libre", id="mode-cv-btn", n_clicks=1, className="mode-btn active"),
                        html.Button("Upload PDF", id="mode-pdf-btn", n_clicks=0, className="mode-btn"),
                    ], className="mode-switch mb-4"),
                    html.Div([
                        html.Div([dcc.Textarea(id="cv-text", className="modern-textarea", placeholder="Saisissez votre expérience (min. 50 caractères)...")], id="cv-panel"),
                        html.Div([dcc.Upload(id="upload-data", children=html.Div(['Cliquez pour uploader un PDF']), className="pdf-upload-zone")], id="pdf-panel", style={"display": "none"}),
                        dbc.Button("Exécuter l'Analyse ML", id="analyze-btn", className="hero-primary-btn mt-4"),
                    ], className="glass-card p-4")
                ])
            ], lg=8)
        ], justify="center"),
        html.Div(id="analysis-preview", className="mt-5")
    ])

def get_fiche_metier_layout(job_code, user_data):
    if job_code not in engine.df_trained['code_rome'].values: return html.Div("Erreur.")
    row = engine.df_trained[engine.df_trained['code_rome'] == job_code].iloc[0]
    ia_val, ia_txt = engine.get_ia_impact(row)
    passerelles = engine.get_passerelles(job_code)
    gap = engine.get_skill_gap(user_data, job_code)

    return html.Div([
        dcc.Link("← Retour à l'analyse", href="/ml", className="back-link mb-4"),
        html.H1(row['libelle_rome'], className="gradient-text mb-5"),
        dbc.Row([
            dbc.Col(html.Div([
                html.Div("Savoir-faire opérationnels", className="result-card-title"),
                html.Ul([html.Li(c, className="list-item-ml") for c in row['libelle_competence'][:8]])
            ], className="glass-card p-4"), lg=6),
            dbc.Col(html.Div([
                html.Div("Savoirs théoriques", className="result-card-title"),
                html.Ul([html.Li(s, className="list-item-ml") for s in row['libelle_savoir'][:8]])
            ], className="glass-card p-4"), lg=6),
        ]),
        html.Div([
            dbc.Row([
                dbc.Col(html.Div([html.Div("Impact IA"), html.H3(ia_val), html.P(ia_txt)], className="footer-sub-card"), lg=4),
                dbc.Col(html.Div([html.Div("Passerelles"), html.Ul([html.Li(p) for p in passerelles])], className="footer-sub-card"), lg=4),
                dbc.Col(html.Div([html.Div("Skill Gap"), html.Ul([html.Li(g, style={"color":"#ffcc00"}) for g in gap])], className="footer-sub-card"), lg=4),
            ])
        ], className="footer-analysis-zone mt-4")
    ])

layout = html.Div([
    dcc.Location(id='url-ml', refresh=False),
    dcc.Store(id='cv-data-store', storage_type='session'),
    html.Div(id='page-content-ml', className="landing-container")
])

@callback(Output('page-content-ml', 'children'), [Input('url-ml', 'search')], [State('cv-data-store', 'data')])
def router(search, store_data):
    if search:
        params = parse_qs(search.lstrip('?'))
        if 'code' in params: return get_fiche_metier_layout(unquote(params['code'][0]), store_data)
    return get_ml_main_layout()

@callback([Output("cv-panel", "style"), Output("pdf-panel", "style"), Output("mode-cv-btn", "className"), Output("mode-pdf-btn", "className")],
          [Input("mode-cv-btn", "n_clicks"), Input("mode-pdf-btn", "n_clicks")])
def toggle_mode(n1, n2):
    if ctx.triggered_id == "mode-pdf-btn": return {"display":"none"}, {"display":"block"}, "mode-btn", "mode-btn active"
    return {"display":"block"}, {"display":"none"}, "mode-btn active", "mode-btn"

@callback([Output("analysis-preview", "children"), Output("cv-data-store", "data")], 
          Input("analyze-btn", "n_clicks"), State("cv-text", "value"), State("upload-data", "contents"), State("mode-cv-btn", "className"), State("family-filter", "value"))
def execute_analysis(n, text, pdf, c1, family_val):
    if not n: raise dash.exceptions.PreventUpdate
    source = text if "active" in c1 else ""
    if not source and pdf:
        try:
            content_string = pdf.split(',')[1]
            decoded = base64.b64decode(content_string)
            reader = PyPDF2.PdfReader(io.BytesIO(decoded))
            source = " ".join([p.extract_text() for p in reader.pages])
        except: return dbc.Alert("Erreur de lecture PDF.", color="danger"), ""

    selected_families = list(family_val) if family_val and family_val != 'ALL' else None
    recs = engine.predict(source, families=selected_families)
    
    if recs == "SIGNAL_INSUFFISANT": return dbc.Alert("Texte trop court (min 50 car.) pour le modèle ML.", color="warning"), ""
    if not recs: return dbc.Alert("Aucune correspondance trouvée dans ce secteur.", color="info"), source

    return html.Div([
        html.H4("Résultats de la classification KNN :", className="mb-4 text-white"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([html.Span(r['metier'], className="result-highlight"), html.Small(f" (Score : {r['score']}%)", style={"color": "#00d4ff"})]),
                    dcc.Link("Fiche métier ➜", href=f"/ml?code={r['code']}", className="fiche-link")
                ], className="glass-card p-3 mb-2") for r in recs
            ], lg=8)
        ])
    ]), source

# ==========================================================
# GESTION DU MODE SCRIPT (Génération image rapport)
# ==========================================================
if __name__ == "__main__":
    print("🚀 Démarrage du script de validation...")
    # On génère l'image avec le code métier "Boulanger"
    print(engine.generate_visual_matrix("D1102"))