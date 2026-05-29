
import pandas as pd
import numpy as np
import base64
import io
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx

from urllib.parse import parse_qs, unquote

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split, cross_val_score, learning_curve
from sklearn.metrics import accuracy_score, classification_report

import os
import re
import string
import matplotlib.pyplot as plt
import seaborn as sns

# Import pour l'extraction de texte PDF
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# Import pour skill gap sémantique avancé
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

# PROTECTION : dash.register_page ne s'exécute que si le script est appelé par l'app principale
if __name__ != "__main__":
    dash.register_page(__name__, path="/ml", name="Analyse Profil")

# ==========================================================
# PARTIE 1 : MOTEUR DE MACHINE LEARNING (LOGIQUE KNN & VALIDATION)
# ==========================================================

STOP_WORDS_FR = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "à", "au", "aux",
    "en", "dans", "sur", "sous", "pour", "par", "avec", "sans", "ce", "ces", "cet",
    "cette", "son", "sa", "ses", "leur", "leurs", "il", "elle", "ils", "elles",
    "nous", "vous", "je", "tu", "d", "l", "a", "est", "sont", "être", "avoir",
    "faire", "plus", "moins", "très", "comme", "afin", "ainsi", "chez", "tout",
    "tous", "toute", "toutes", "qui", "que", "quoi", "dont", "où", "ne", "pas",
    "cela", "ceci", "ceux", "celles", "lui", "ni", "y"
}

class ROMEAIEngine:
    def __init__(self, data_path="data/"):
        self.data_path = data_path
        self.df_trained = self._build_knowledge_base()

        if self.df_trained.empty:
            self.df_trained = pd.DataFrame({
                'libelle_rome': ['Dataset vide'],
                'code_rome': ['N/A'],
                'all_text_knowledge': [''],
                'transition_num': [0],
                'libelle_competence': [[]],
                'libelle_savoir': [[]]
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

        # Skill gap sémantique
        self.semantic_model = None
        self.semantic_enabled = False
        self._load_semantic_model()

    def _load_semantic_model(self):
        if SentenceTransformer is None:
            self.semantic_enabled = False
            return
        try:
            self.semantic_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            self.semantic_enabled = True
        except Exception:
            self.semantic_model = None
            self.semantic_enabled = False

    def _normalize_text(self, text):
        if not isinstance(text, str):
            return []
        text = text.lower()
        text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
        text = re.sub(r"\d+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return [tok for tok in text.split(" ") if len(tok) > 1 and tok not in STOP_WORDS_FR]

    def _split_sentences(self, text):
        if not isinstance(text, str):
            return []
        parts = re.split(r"[.!?\n;]+", text)
        return [p.strip() for p in parts if p.strip()]

    def _calculate_accuracy(self):
        try:
            test_vectors = self.vectorizer.transform(self.test_df['all_text_knowledge'])
            predictions_codes = self.knn_model.predict(test_vectors)
            y_true_families = [code[0] for code in self.test_df['code_rome']]
            y_pred_families = [code[0] for code in predictions_codes]
            acc = accuracy_score(y_true_families, y_pred_families)
            return round(acc * 100, 2)
        except Exception:
            return 0.0

    def _build_knowledge_base(self):
        try:
            def safe_read(name):
                path = os.path.join(self.data_path, name)
                if not os.path.exists(path):
                    return pd.DataFrame()
                return pd.read_csv(path, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')

            df_rome = safe_read("unix_referentiel_code_rome_v460_utf8.csv")
            df_liens = safe_read("unix_liens_rome_referentiels_v460_utf8.csv")
            df_comp = safe_read("unix_referentiel_competence_v460_utf8.csv")
            df_savoir = safe_read("unix_referentiel_savoir_v460_utf8.csv")

            if not df_rome.empty:
                for df in [df_rome, df_liens, df_comp, df_savoir]:
                    if not df.empty:
                        df.columns = df.columns.str.strip()

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
        except Exception:
            return pd.DataFrame()

    def predict(self, user_input, top_n=3):
        if not user_input or len(user_input) < 30:
            return "SIGNAL_INSUFFISANT"

        user_vec = self.vectorizer.transform([user_input.lower()])
        distances, indices = self.knn_model.kneighbors(user_vec, n_neighbors=top_n)

        results_indices = indices[0]
        scores = [1 - d for d in distances[0]]

        results = []
        for i, idx in enumerate(results_indices):
            row = self.train_df.iloc[idx]
            results.append({
                'metier': row['libelle_rome'],
                'code': row['code_rome'],
                'score': round(scores[i] * 100, 1)
            })
        return results

    def get_ia_impact(self, row):
        try:
            raw_val = str(row.get('transition_num', 0)).replace('O', '0').strip()
            trans_score = float(raw_val)
        except Exception:
            trans_score = 0.0
        return ("Élevé", "Forte mutation.") if trans_score >= 3 else ("Faible", "Composante humaine stable.")

    def get_passerelles(self, code_rome):
        try:
            idx = self.df_trained[self.df_trained['code_rome'] == code_rome].index[0]
            sims = cosine_similarity(
                self.vectorizer.transform([self.df_trained.iloc[idx]['all_text_knowledge']]),
                self.tfidf_matrix_train
            ).flatten()
            related_indices = sims.argsort()[-5:-1][::-1]
            return self.train_df.iloc[related_indices]['libelle_rome'].tolist()
        except Exception:
            return []

    # ------------------------------------------------------
    # SKILL GAP AVANCÉ (remplacement de la version simple)
    # ------------------------------------------------------
    def get_skill_gap(self, user_text, code_rome):
        try:
            row = self.df_trained[self.df_trained['code_rome'] == code_rome].iloc[0]
            skills = row.get('libelle_competence', [])

            if not isinstance(skills, list) or not skills:
                return ["Analyse impossible"]

            if not user_text or len(user_text.strip()) < 10:
                return skills[:5]

            # Mode sémantique avancé
            if self.semantic_enabled and self.semantic_model is not None:
                try:
                    cv_units = self._split_sentences(user_text)
                    if not cv_units:
                        cv_units = [user_text]

                    skill_texts = [str(s) for s in skills if str(s).strip()]
                    if not skill_texts:
                        return ["Analyse impossible"]

                    skill_emb = self.semantic_model.encode(skill_texts, convert_to_numpy=True)
                    cv_emb = self.semantic_model.encode(cv_units, convert_to_numpy=True)

                    sim_matrix = cosine_similarity(skill_emb, cv_emb)

                    missing_skills = []
                    for i, skill in enumerate(skill_texts):
                        max_sim = float(sim_matrix[i].max())
                        if max_sim < 0.55:
                            missing_skills.append(skill)

                    return missing_skills[:5] if missing_skills else ["Compétences globalement alignées"]
                except Exception:
                    pass

            # Fallback lexical
            user_tokens = set(self._normalize_text(user_text))
            gap = []
            for s in skills:
                skill_tokens = set(self._normalize_text(str(s)))
                if skill_tokens and not skill_tokens.issubset(user_tokens):
                    gap.append(s)

            return gap[:5] if gap else ["Compétences globalement alignées"]

        except Exception:
            return ["Non disponible"]

    # ------------------------------------------------------
    # NOUVEAU : mots-clés en commun
    # ------------------------------------------------------
    def get_overlap_keywords(self, user_text, code_rome, top_n=8):
        try:
            row = self.df_trained[self.df_trained['code_rome'] == code_rome].iloc[0]
            job_text = row['all_text_knowledge']

            user_tokens = set(self._normalize_text(user_text))
            job_tokens = set(self._normalize_text(job_text))

            overlap = sorted(list(user_tokens.intersection(job_tokens)))
            return overlap[:top_n]
        except Exception:
            return []

    def export_pedagogical_metrics(self):
        """ Génère les preuves scientifiques pour le rapport de Master 2 """
        print("📊 Génération des métriques pédagogiques...")

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
                    html.Div([
                        html.Button("Texte libre", id="mode-cv-btn", n_clicks=1, className="mode-btn active"),
                        html.Button("Upload PDF", id="mode-pdf-btn", n_clicks=0, className="mode-btn")
                    ], className="mode-switch mb-4"),

                    html.Div([
                        html.Div([
                            dcc.Textarea(
                                id="cv-text",
                                className="modern-textarea",
                                placeholder="Ex: analyse des données et data visualisation, langage Python..."
                            )
                        ], id="cv-panel"),

                        html.Div([
                            dcc.Upload(
                                id="upload-data",
                                children=html.Div(['Cliquez pour PDF']),
                                className="pdf-upload-zone"
                            )
                        ], id="pdf-panel", style={"display": "none"}),

                        dbc.Button("Lancer l'Analyse Scientifique", id="analyze-btn", className="hero-primary-btn mt-4"),
                    ], className="glass-card p-4")
                ])
            ], lg=8)
        ], justify="center"),

        html.Div(id="analysis-preview", className="mt-5")
    ])

def get_fiche_metier_layout(job_code, user_data):
    if job_code not in engine.df_trained['code_rome'].values:
        return html.Div("Métier introuvable.")

    row = engine.df_trained[engine.df_trained['code_rome'] == job_code].iloc[0]
    ia_val, ia_txt = engine.get_ia_impact(row)
    passs = engine.get_passerelles(job_code)
    gap = engine.get_skill_gap(user_data, job_code)
    overlap = engine.get_overlap_keywords(user_data, job_code)

    return html.Div([
        dcc.Link("← Retour", href="/ml", className="back-link mb-4"),
        html.H1(row['libelle_rome'], className="gradient-text mb-4"),

        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Div("Compétences Clés", className="result-card-title"),
                    html.Ul([
                        html.Li(c) for c in (
                            row['libelle_competence'][:8] if isinstance(row['libelle_competence'], list) else ["Non listées"]
                        )
                    ])
                ], className="glass-card p-4"),
                lg=6
            ),
            dbc.Col(
                html.Div([
                    html.Div("Savoirs théoriques", className="result-card-title"),
                    html.Ul([
                        html.Li(s) for s in (
                            row['libelle_savoir'][:8] if isinstance(row['libelle_savoir'], list) else ["Non listés"]
                        )
                    ])
                ], className="glass-card p-4"),
                lg=6
            ),
        ]),

        html.Div([
            dbc.Row([
                dbc.Col(html.Div([
                    html.Div("Impact IA"),
                    html.H3(ia_val)
                ], className="footer-sub-card"), lg=4),

                dbc.Col(html.Div([
                    html.Div("Passerelles"),
                    html.Ul([html.Li(p) for p in passs])
                ], className="footer-sub-card"), lg=4),

                dbc.Col(html.Div([
                    html.Div("Skill Gap"),
                    html.Ul([html.Li(g, style={"color": "#ffcc00"}) for g in gap])
                ], className="footer-sub-card"), lg=4),
            ])
        ], className="footer-analysis-zone mt-4"),

        # NOUVEAU BLOC COMME SUR TA CAPTURE
        html.Div([
            html.Div("Mots-clés en commun avec le profil", className="footer-card-title mb-3"),
            html.Div([
                dbc.Badge(k, color="info", className="me-2 mb-2", pill=True)
                for k in overlap
            ]) if overlap else html.P("Pas de mots-clés fortement communs détectés.", className="text-muted")
        ], className="glass-card p-4 mt-4")
    ])

layout = html.Div([
    dcc.Location(id='url-ml', refresh=False),
    dcc.Store(id='cv-data-store', storage_type='session'),
    html.Div(id='page-content-ml', className="landing-container")
])

@callback(
    Output('page-content-ml', 'children'),
    [Input('url-ml', 'search')],
    [State('cv-data-store', 'data')]
)
def router(search, store_data):
    if search:
        params = parse_qs(search.lstrip('?'))
        if 'code' in params:
            return get_fiche_metier_layout(unquote(params['code'][0]), store_data or "")
    return get_ml_main_layout()

@callback(
    [Output("cv-panel", "style"), Output("pdf-panel", "style"), Output("mode-cv-btn", "className"), Output("mode-pdf-btn", "className")],
    [Input("mode-cv-btn", "n_clicks"), Input("mode-pdf-btn", "n_clicks")]
)
def toggle_mode(n1, n2):
    if ctx.triggered_id == "mode-pdf-btn":
        return {"display": "none"}, {"display": "block"}, "mode-btn", "mode-btn active"
    return {"display": "block"}, {"display": "none"}, "mode-btn active", "mode-btn"

@callback(
    [Output("analysis-preview", "children"), Output("cv-data-store", "data")],
    Input("analyze-btn", "n_clicks"),
    State("cv-text", "value"),
    State("upload-data", "contents"),
    State("mode-cv-btn", "className")
)
def execute_analysis(n, text, pdf, c1):
    if not n:
        raise dash.exceptions.PreventUpdate

    source = text if "active" in c1 else ""

    if not source and pdf:
        try:
            content_string = pdf.split(',')[1]
            decoded = base64.b64decode(content_string)
            reader = PyPDF2.PdfReader(io.BytesIO(decoded))
            source = " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
        except Exception:
            return dbc.Alert("Erreur PDF.", color="danger"), ""

    recs_knn = engine.predict(source)

    if recs_knn == "SIGNAL_INSUFFISANT":
        return dbc.Alert("Texte trop court.", color="warning"), ""

    recs_knn_filtres = [r for r in recs_knn if r['score'] > 0]

    if not recs_knn_filtres:
        return dbc.Alert("🔍 Signal trop faible. Utilisez des mots-clés techniques.", color="info"), source

    return html.Div([
        html.H4("Résultats KNN (Supervisé) :", className="text-white mt-4"),
        html.Div([
            html.Div([
                html.Span(r['metier'], className="result-highlight"),
                html.Small(f" Confiance : {r['score']}%"),
                dcc.Link(
                    " Voir Fiche ➜",
                    href=f"/ml?code={r['code']}",
                    className="ms-3",
                    style={"color": "#00d4ff", "text-decoration": "none"}
                )
            ], className="glass-card p-3 mb-2") for r in recs_knn_filtres
        ]),
    ]), source

if __name__ == "__main__":
    print(f"\n🚀 Système prêt. Validation par famille : {engine.accuracy}%")

    # Génère les images pour ton rapport
    engine.export_pedagogical_metrics()