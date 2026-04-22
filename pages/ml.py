import pandas as pd
import numpy as np
import base64
import io
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx

# --- IMPORTS POUR L'URL ET LA NAVIGATION ---
from urllib.parse import parse_qs, unquote

# --- IMPORTS POUR LA VALIDATION SCIENTIFIQUE ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split, cross_val_score, learning_curve
from sklearn.metrics import accuracy_score, classification_report

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
# PARTIE 1 : MOTEUR DE MACHINE LEARNING (LOGIQUE KNN & VALIDATION)
# ==========================================================

class ROMEAIEngine:
    def __init__(self, data_path="data/"):
        self.data_path = data_path
        self.df_trained = self._build_knowledge_base()
        
        if self.df_trained.empty:
            self.df_trained = pd.DataFrame({
                'libelle_rome': ['Dataset vide'], 'code_rome': ['N/A'], 'all_text_knowledge': [''], 'transition_num': [0]
            })

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            max_df=0.5, 
            min_df=2,
            stop_words=['ce', 'le', 'la', 'de', 'du', 'en', 'et', 'un', 'une', 'des', 'les', 'pour']
        )

        self.train_df, self.test_df = train_test_split(self.df_trained, test_size=0.20, random_state=42)
        self.tfidf_matrix_train = self.vectorizer.fit_transform(self.train_df['all_text_knowledge'])
        self.knn_model = KNeighborsClassifier(n_neighbors=5, metric='cosine')
        self.knn_model.fit(self.tfidf_matrix_train, self.train_df['code_rome'])
        self.accuracy = self._calculate_accuracy()

    def _calculate_accuracy(self):
        try:
            test_vectors = self.vectorizer.transform(self.test_df['all_text_knowledge'])
            predictions_codes = self.knn_model.predict(test_vectors)
            y_true_families = [code[0] for code in self.test_df['code_rome']]
            y_pred_families = [code[0] for code in predictions_codes]
            acc = accuracy_score(y_true_families, y_pred_families)
            return round(acc * 100, 2)
        except: return 0.0

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

            if not df_rome.empty:
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
            return pd.DataFrame()
        except: return pd.DataFrame()

    def predict(self, user_input, top_n=3, families=None):
        if not user_input or len(user_input) < 30: return "SIGNAL_INSUFFISANT"
        user_vec = self.vectorizer.transform([user_input.lower()])
        
        # SÉCURITÉ : Si families est None ou vide, on cherche partout
        if families and families != 'ALL':
            mask = self.train_df['code_rome'].str.startswith(tuple(families))
            filtered_indices = np.where(mask)[0]
            if len(filtered_indices) == 0: return []
            sub_matrix = self.tfidf_matrix_train[filtered_indices]
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
            row = self.train_df.iloc[idx]
            results.append({'metier': row['libelle_rome'], 'code': row['code_rome'], 'score': round(scores[i] * 100, 1)})
        return results

    def get_ia_impact(self, row):
        try:
            raw_val = str(row.get('transition_num', 0)).replace('O', '0').strip()
            trans_score = float(raw_val)
        except: trans_score = 0.0
        return ("Élevé", "Forte mutation.") if trans_score >= 3 else ("Faible", "Composante humaine stable.")

    def get_passerelles(self, code_rome):
        try:
            idx = self.df_trained[self.df_trained['code_rome'] == code_rome].index[0]
            sims = cosine_similarity(self.vectorizer.transform([self.df_trained.iloc[idx]['all_text_knowledge']]), self.tfidf_matrix_train).flatten()
            related_indices = sims.argsort()[-5:-1][::-1] 
            return self.train_df.iloc[related_indices]['libelle_rome'].tolist()
        except: return []

    def get_skill_gap(self, user_text, code_rome):
        try:
            row = self.df_trained[self.df_trained['code_rome'] == code_rome].iloc[0]
            req = row['libelle_competence']
            if not req or not user_text: return ["Analyse impossible"]
            gap = [s for s in req if not any(w in user_text.lower() for w in s.lower().split() if len(w)>3)]
            return gap[:3]
        except: return ["Non disponible"]
        
    def export_pedagogical_metrics(self):
        """ Génère les preuves scientifiques pour le rapport de Master 2 """
        print("📊 Génération des métriques pédagogiques...")

        # 1. CROSS-VALIDATION (Validation Croisée)
        # On découpe en 5 et on vérifie la stabilité
        # On utilise la première lettre du code ROME (la famille) pour plus de sens
        y_families = [c[0] for c in self.df_trained['code_rome']]
        X_tfidf = self.vectorizer.fit_transform(self.df_trained['all_text_knowledge'])
        
        scores = cross_val_score(self.knn_model, X_tfidf, y_families, cv=5)
        
        plt.figure(figsize=(8, 5))
        plt.bar(range(1, 6), scores, color='skyblue')
        plt.axhline(y=scores.mean(), color='red', linestyle='--', label=f'Moyenne : {scores.mean():.2f}')
        plt.title("Stabilité du modèle (5-Fold Cross-Validation)")
        plt.xlabel("Itération (Fold)")
        plt.ylabel("Accuracy Score")
        plt.legend()
        plt.savefig("validation_croisee_master.png")
        plt.close()
        print("✅ Image 'validation_croisee_master.png' créée.")

        # 2. LEARNING CURVE (Courbe d'Apprentissage)
        train_sizes, train_scores, test_scores = learning_curve(
            self.knn_model, X_tfidf, y_families, cv=5, n_jobs=-1, 
            train_sizes=np.linspace(0.1, 1.0, 5)
        )
        
        train_mean = np.mean(train_scores, axis=1)
        test_mean = np.mean(test_scores, axis=1)

        plt.figure(figsize=(8, 5))
        plt.plot(train_sizes, train_mean, 'o-', color="r", label="Score Entraînement")
        plt.plot(train_sizes, test_mean, 'o-', color="g", label="Score Validation")
        plt.title("Courbe d'Apprentissage (Détection Overfitting)")
        plt.xlabel("Nombre d'exemples d'entraînement")
        plt.ylabel("Score")
        plt.legend(loc="best")
        plt.grid()
        plt.savefig("courbe_apprentissage_master.png")
        plt.close()
        print("✅ Image 'courbe_apprentissage_master.png' créée.")

engine = ROMEAIEngine()

# ==========================================================
# PARTIE 2 : INTERFACE DASH
# ==========================================================

def get_ml_main_layout():
    return html.Div([
        html.Div([
            html.H1(["Analyse Profil & ", html.Span("Machine Learning", className="gradient-text")]),
            html.P(f"Moteur KNN validé (Accuracy Famille : {engine.accuracy}%)")
        ], className="analysis-hero text-center mb-5"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label("Domaine de recherche :", className="text-white mb-2"),
                    dcc.Dropdown(id="family-filter", options=[{'label': 'Artisanat (D)', 'value': 'D'}, {'label': 'BTP (F)', 'value': 'F'}, {'label': 'Informatique (M)', 'value': 'M'}, {'label': 'Tous', 'value': 'ALL'}], value='ALL', clearable=True, className="mb-4 text-dark"),
                    html.Div([html.Button("Texte libre", id="mode-cv-btn", n_clicks=1, className="mode-btn active"), html.Button("Upload PDF", id="mode-pdf-btn", n_clicks=0, className="mode-btn")], className="mode-switch mb-4"),
                    html.Div([
                        html.Div([dcc.Textarea(id="cv-text", className="modern-textarea", placeholder="Ex: analyse des données et data visualisation, language python...")], id="cv-panel"),
                        html.Div([dcc.Upload(id="upload-data", children=html.Div(['Cliquez pour PDF']), className="pdf-upload-zone")], id="pdf-panel", style={"display": "none"}),
                        dbc.Button("Lancer l'Analyse Scientifique", id="analyze-btn", className="hero-primary-btn mt-4"),
                    ], className="glass-card p-4")
                ])
            ], lg=8)
        ], justify="center"),
        html.Div(id="analysis-preview", className="mt-5")
    ])

def get_fiche_metier_layout(job_code, user_data):
    if job_code not in engine.df_trained['code_rome'].values: return html.Div("Métier introuvable.")
    row = engine.df_trained[engine.df_trained['code_rome'] == job_code].iloc[0]
    ia_val, ia_txt = engine.get_ia_impact(row); passs = engine.get_passerelles(job_code); gap = engine.get_skill_gap(user_data, job_code)
    return html.Div([
        dcc.Link("← Retour", href="/ml", className="back-link mb-4"),
        html.H1(row['libelle_rome'], className="gradient-text mb-4"),
        dbc.Row([
            dbc.Col(html.Div([html.Div("Compétences Clés", className="result-card-title"), html.Ul([html.Li(c) for c in (row['libelle_competence'][:8] if isinstance(row['libelle_competence'], list) else ["Non listées"])])], className="glass-card p-4"), lg=6),
            dbc.Col(html.Div([html.Div("Savoirs théoriques", className="result-card-title"), html.Ul([html.Li(s) for s in (row['libelle_savoir'][:8] if isinstance(row['libelle_savoir'], list) else ["Non listés"])])], className="glass-card p-4"), lg=6),
        ]),
        html.Div([dbc.Row([
            dbc.Col(html.Div([html.Div("Impact IA"), html.H3(ia_val)], className="footer-sub-card"), lg=4),
            dbc.Col(html.Div([html.Div("Passerelles"), html.Ul([html.Li(p) for p in passs])], className="footer-sub-card"), lg=4),
            dbc.Col(html.Div([html.Div("Skill Gap"), html.Ul([html.Li(g, style={"color":"#ffcc00"}) for g in gap])], className="footer-sub-card"), lg=4),
        ])], className="footer-analysis-zone mt-4")
    ])

layout = html.Div([dcc.Location(id='url-ml', refresh=False), dcc.Store(id='cv-data-store', storage_type='session'), html.Div(id='page-content-ml', className="landing-container")])

@callback(Output('page-content-ml', 'children'), [Input('url-ml', 'search')], [State('cv-data-store', 'data')])
def router(search, store_data):
    if search:
        params = parse_qs(search.lstrip('?'))
        if 'code' in params: return get_fiche_metier_layout(unquote(params['code'][0]), store_data or "")
    return get_ml_main_layout()

@callback([Output("cv-panel", "style"), Output("pdf-panel", "style"), Output("mode-cv-btn", "className"), Output("mode-pdf-btn", "className")], [Input("mode-cv-btn", "n_clicks"), Input("mode-pdf-btn", "n_clicks")])
def toggle_mode(n1, n2):
    if ctx.triggered_id == "mode-pdf-btn": return {"display":"none"}, {"display":"block"}, "mode-btn", "mode-btn active"
    return {"display":"block"}, {"display":"none"}, "mode-btn active", "mode-btn"

@callback([Output("analysis-preview", "children"), Output("cv-data-store", "data")], Input("analyze-btn", "n_clicks"), State("cv-text", "value"), State("upload-data", "contents"), State("mode-cv-btn", "className"), State("family-filter", "value"))
def execute_analysis(n, text, pdf, c1, family_val):
    if not n: raise dash.exceptions.PreventUpdate
    source = text if "active" in c1 else ""
    if not source and pdf:
        try:
            content_string = pdf.split(',')[1]; decoded = base64.b64decode(content_string)
            reader = PyPDF2.PdfReader(io.BytesIO(decoded)); source = " ".join([p.extract_text() for p in reader.pages])
        except: return dbc.Alert("Erreur PDF.", color="danger"), ""
    
    # SÉCURITÉ : On gère le cas où family_val est None ou 'ALL'
    target_families = None
    if family_val and family_val != 'ALL':
        target_families = [family_val]

    recs_knn = engine.predict(source, families=target_families)
    
    if recs_knn == "SIGNAL_INSUFFISANT": return dbc.Alert("Texte trop court.", color="warning"), ""

    recs_knn_filtres = [r for r in recs_knn if r['score'] > 0]
    
    if not recs_knn_filtres:
        return dbc.Alert("🔍 Signal trop faible. Utilisez des mots-clés techniques (ex: tailler, planter, gérer).", color="info"), source

    return html.Div([
        html.H4("Résultats KNN (Supervisé) :", className="text-white mt-4"),
        html.Div([
            html.Div([
                html.Span(r['metier'], className="result-highlight"), 
                html.Small(f" Confiance : {r['score']}%"),
                dcc.Link(" Voir Fiche ➜", href=f"/ml?code={r['code']}", className="ms-3", style={"color":"#00d4ff", "text-decoration":"none"})
            ], className="glass-card p-3 mb-2") for r in recs_knn_filtres
        ]),
    ]), source

if __name__ == "__main__":
    print(f"\n🚀 Système prêt. Validation par famille : {engine.accuracy}%")
    
    # Génère les images pour ton rapport
    engine.export_pedagogical_metrics()
    
    # Génère la matrice Data Scientist (M1805)
    print(engine.generate_visual_matrix("M1805"))