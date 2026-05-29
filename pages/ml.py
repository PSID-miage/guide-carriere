import pandas as pd
import numpy as np
import base64
import io
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx
import time
import os
import matplotlib.pyplot as plt
import seaborn as sns

# --- IMPORTS NAVIGATION & ML ---
from urllib.parse import parse_qs, unquote
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split, cross_val_score, learning_curve, KFold
from sklearn.metrics import mean_absolute_error

# Import extraction PDF
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    dash.register_page(__name__, path="/ml", name="Analyse Profil")
except Exception:
    # On est en mode script standalone (pas dans le contexte Dash) - on ignore.
    pass

# ==========================================================
# PARTIE 1 : MOTEUR DE MACHINE LEARNING (ROMEAIEngine)
# ==========================================================

class ROMEAIEngine:
    def __init__(self, data_path="data/"):
        self.data_path = data_path
        self.df_trained = self._build_knowledge_base()

        if self.df_trained.empty:
            self.df_trained = pd.DataFrame({
                'libelle_rome': ['Dataset vide'], 'code_rome': ['N/A'],
                'all_text_knowledge': [''], 'source': ['none']
            })

        # Vectorisation TF-IDF (inchangé)
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            max_df=0.5,
            min_df=2,
            stop_words=['ce', 'le', 'la', 'de', 'du', 'en', 'et',
                        'un', 'une', 'des', 'les', 'pour']
        )

        # ❌ SUPPRIMÉ : train_test_split (on n'en a plus besoin)
        # ✅ On entraîne sur TOUTE la base (ROME + offres)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df_trained['all_text_knowledge'])

        # KNN (inchangé)
        self.knn_model = KNeighborsClassifier(n_neighbors=5, metric='cosine')
        self.knn_model.fit(self.tfidf_matrix, self.df_trained['code_rome'])

    def _build_knowledge_base(self):
        """Construit la base de connaissances pour le KNN.
    Train = fiches ROME M18 (référentiel) + offres FT M18 (API).
    Les CV étiquetés (cv_annotes.csv) NE SONT PAS LUS ICI — ils sont
    uniquement utilisés en validation.
    """
        try:
            def safe_read(name):
                path = os.path.join(self.data_path, name)
                if not os.path.exists(path):
                    return pd.DataFrame()
                return pd.read_csv(path, sep=None, engine='python',
                                encoding='utf-8', on_bad_lines='skip')

            # === SOURCE 1 : FICHES ROME (référentiel théorique) ===
            df_rome = safe_read("unix_referentiel_code_rome_v460_utf8.csv")
            df_liens = safe_read("unix_liens_rome_referentiels_v460_utf8.csv")
            df_comp = safe_read("unix_referentiel_competence_v460_utf8.csv")
            df_savoir = safe_read("unix_referentiel_savoir_v460_utf8.csv")

            rome_rows = pd.DataFrame()
            if not df_rome.empty:
                for df in [df_rome, df_liens, df_comp, df_savoir]:
                    if not df.empty:
                        df.columns = df.columns.str.strip()

                # Filtre M18 dès le départ pour alléger le calcul
                df_rome = df_rome[df_rome['code_rome'].str.startswith('M18', na=False)]

                # Agrégation compétences
                comp_merged = df_liens[df_liens['code_compo_bloc'] == 5].merge(
                    df_comp, on='code_ogr', how='inner')
                agg_comp = comp_merged.groupby('code_rome')['libelle_competence'].apply(list).reset_index()

                # Agrégation savoirs
                savoir_merged = df_liens.merge(
                    df_savoir, left_on='code_ogr', right_on='code_ogr_savoir', how='inner')
                agg_savoir = savoir_merged.groupby('code_rome')['libelle_savoir'].apply(list).reset_index()

                rome_rows = df_rome.merge(agg_comp, on='code_rome', how='left') \
                                .merge(agg_savoir, on='code_rome', how='left')
                rome_rows['all_text_knowledge'] = (
                    rome_rows['libelle_rome'].fillna('') + " " +
                    rome_rows['libelle_competence'].apply(
                        lambda x: " ".join(x) if isinstance(x, list) else "") + " " +
                    rome_rows['libelle_savoir'].apply(
                        lambda x: " ".join(x) if isinstance(x, list) else "")
                ).str.lower().str.strip()
                rome_rows['source'] = 'rome'
                rome_rows = rome_rows[['code_rome', 'libelle_rome',
                                    'all_text_knowledge', 'source']]
                print(f"📚 {len(rome_rows)} fiches ROME M18 chargées")

            # === SOURCE 2 : OFFRES FRANCE TRAVAIL (données du monde réel) ===
            df_offres = safe_read("offres_ft_m18.csv")
            offres_rows = pd.DataFrame()
            if not df_offres.empty:
                df_offres['all_text_knowledge'] = (
                    df_offres['libelle_offre'].fillna('') + " " +
                    df_offres['description'].fillna('') + " " +
                    df_offres['competences'].fillna('')
                ).str.lower().str.strip()
                df_offres['libelle_rome'] = df_offres['libelle_offre']
                df_offres['source'] = 'offre'
                offres_rows = df_offres[['code_rome', 'libelle_rome',
                                        'all_text_knowledge', 'source']]
                print(f"💼 {len(offres_rows)} offres FT chargées")

            # === COMBINAISON ===
            if rome_rows.empty and offres_rows.empty:
                return pd.DataFrame()
            combined = pd.concat([rome_rows, offres_rows], ignore_index=True)
            # On filtre les textes trop courts (bruit)
            combined = combined[combined['all_text_knowledge'].str.len() > 20]
            print(f"🎯 Total base de connaissances : {len(combined)} lignes")
            return combined

        except Exception as e:
            print(f"❌ Erreur build_knowledge_base : {e}")
            return pd.DataFrame()

    def predict(self, user_input, top_n=3):
        if not user_input or len(user_input) < 30:
            return "SIGNAL_INSUFFISANT"
        user_vec = self.vectorizer.transform([user_input.lower()])
        distances, indices = self.knn_model.kneighbors(user_vec, n_neighbors=top_n)

        results = []
        for i, idx in enumerate(indices[0]):
            row = self.df_trained.iloc[idx]   # ⬅️ self.df_trained au lieu de self.train_df
            results.append({
                'metier': row['libelle_rome'],
                'code': row['code_rome'],
                'source': row['source'],       # ⬅️ on indique si match vient de ROME ou d'une offre
                'score': round((1 - distances[0][i]) * 100, 1)
            })
        return results

    # ==========================================================
    # ÉVALUATION SCIENTIFIQUE (Stabilité, Apprentissage, Résidus)
    # ==========================================================

    def export_validation_scientifique(self):
        print("📊 Génération des graphiques de validation...")
        X = self.vectorizer.fit_transform(self.df_trained['all_text_knowledge'])
        y = self.df_trained['code_rome']
        cv_strat = KFold(n_splits=5, shuffle=True, random_state=42)

        # 1. STABILITÉ (Cross-Validation)
        scores = cross_val_score(self.knn_model, X, y, cv=cv_strat)
        plt.figure(figsize=(10, 6))
        plt.bar(range(1, 6), scores, color='skyblue', edgecolor='white')
        plt.axhline(y=np.mean(scores), color='red', linestyle='--', label=f'Mean: {np.mean(scores):.2f}')
        plt.title("Stabilité du modèle (Cross-Validation)"); plt.xlabel("Folds"); plt.ylabel("Accuracy")
        plt.legend(); plt.savefig("validation_croisee_master.png"); plt.close()

        # 2. APPRENTISSAGE (Learning Curve)
        ts, tr, te = learning_curve(self.knn_model, X, y, cv=cv_strat, train_sizes=np.linspace(0.1, 1.0, 5))
        plt.figure(figsize=(10, 6))
        plt.plot(ts, np.mean(tr, axis=1), 'o-', color="r", label="Score Entraînement")
        plt.plot(ts, np.mean(te, axis=1), 'o-', color="g", label="Score Validation")
        plt.title("Courbe d'Apprentissage (Détection Overfitting)"); plt.xlabel("Echantillons"); plt.ylabel("Score")
        plt.legend(); plt.grid(True); plt.savefig("courbe_apprentissage_master.png"); plt.close()

        # 3. RÉSIDUS (Écart de prédiction)
        X_test = self.vectorizer.transform(self.test_df['all_text_knowledge'])
        dist, _ = self.knn_model.kneighbors(X_test, n_neighbors=1)
        residus = dist.flatten()
        plt.figure(figsize=(10, 6))
        plt.scatter(range(len(residus)), residus, alpha=0.6, color='blue')
        plt.axhline(y=np.mean(residus), color='red', linestyle='--', label=f'MAE: {np.mean(residus):.3f}')
        plt.title("Analyse des résidus : Écart de prédiction KNN"); plt.ylabel("Distance Cosinus"); plt.legend()
        plt.savefig("metrics_prediction_residus.png"); plt.close()

def validate_accuracy_on_cvs(self, cv_path="data/cv_annotes.csv"):
    """
    VALIDATION 1 — Accuracy sur les 24 CV étiquetés manuellement.
    Mesure :
        - Top-1 exact (code ROME précis)
        - Top-3 exact (le bon code est dans le top 3)
        - Accuracy par groupe thématique (validation 'coarse')
    """
    from sklearn.metrics import confusion_matrix, classification_report
    from data.groupes_thematiques import get_groupe, GROUPES_LIST

    df_cv = pd.read_csv(os.path.join(self.data_path, "cv_annotes.csv"))
    print(f"\\n🎯 Validation sur {len(df_cv)} CV étiquetés\\n")

    correct_top1 = 0
    correct_top3 = 0
    correct_groupe = 0
    y_true_code, y_pred_code = [], []
    y_true_groupe, y_pred_groupe = [], []

    for _, row in df_cv.iterrows():
        recs = self.predict(row['cv_text'], top_n=3)
        if recs == "SIGNAL_INSUFFISANT":
            print(f"  ⚠️  CV {row['cv_id']} trop court, ignoré")
            continue

        codes_pred = [r['code'] for r in recs]
        code_vrai = row['code_rome_manuel']
        groupe_vrai = row['groupe_thematique']
        groupe_pred = get_groupe(codes_pred[0])

        # Top-1 et Top-3
        if codes_pred[0] == code_vrai:
            correct_top1 += 1
        if code_vrai in codes_pred:
            correct_top3 += 1
        # Groupe thématique
        if groupe_vrai == groupe_pred:
            correct_groupe += 1

        y_true_code.append(code_vrai)
        y_pred_code.append(codes_pred[0])
        y_true_groupe.append(groupe_vrai)
        y_pred_groupe.append(groupe_pred)

    n = len(y_true_code)
    metrics = {
        "n_cv": n,
        "top1_fine": correct_top1 / n,
        "top3_fine": correct_top3 / n,
        "accuracy_groupe": correct_groupe / n,
    }

    # === AFFICHAGE ===
    print(f"📊 Résultats globaux :")
    print(f"   • Accuracy top-1 (ROME exact)    : {metrics['top1_fine']:.2%}")
    print(f"   • Accuracy top-3 (ROME exact)    : {metrics['top3_fine']:.2%}")
    print(f"   • Accuracy groupe thématique     : {metrics['accuracy_groupe']:.2%}  ⬅️ métrique principale")

    # === CLASSIFICATION REPORT par GROUPE (lisible) ===
    print(f"\\n📋 Classification report (par groupe thématique) :")
    print(classification_report(y_true_groupe, y_pred_groupe, zero_division=0))

    # === MATRICE DE CONFUSION (groupe) ===
    labels = sorted(set(y_true_groupe + y_pred_groupe))
    cm = confusion_matrix(y_true_groupe, y_pred_groupe, labels=labels)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=labels, yticklabels=labels)
    plt.title("Matrice de confusion — par groupe thématique")
    plt.ylabel("Vrai groupe (annotation manuelle)")
    plt.xlabel("Groupe prédit (KNN)")
    plt.tight_layout()
    plt.savefig("data/validation_accuracy_groupe.png", dpi=150)
    plt.close()
    print(f"📈 Figure : data/validation_accuracy_groupe.png")

    return metrics

def ablation_study_offres(self, cv_path="data/cv_annotes.csv"):
    """
    BONUS — Étude d'ablation : mesure l'apport quantitatif des offres FT
    par rapport à un entraînement sur ROME seul.
    Démontre que l'enrichissement par les offres améliore la prédiction.
    """
    from copy import deepcopy
    from data.groupes_thematiques import get_groupe

    df_cv = pd.read_csv(os.path.join(self.data_path, "cv_annotes.csv"))
    print(f"\\n🔬 Étude d'ablation : ROME seul vs ROME + offres FT")

    # === VARIANTE A : ROME SEUL ===
    df_rome_only = self.df_trained[self.df_trained['source'] == 'rome'].reset_index(drop=True)
    vec_a = TfidfVectorizer(
        ngram_range=(1, 3), max_features=5000, max_df=0.5, min_df=2,
        stop_words=['ce', 'le', 'la', 'de', 'du', 'en', 'et', 'un', 'une', 'des', 'les', 'pour']
    )
    X_a = vec_a.fit_transform(df_rome_only['all_text_knowledge'])
    knn_a = KNeighborsClassifier(n_neighbors=5, metric='cosine')
    knn_a.fit(X_a, df_rome_only['code_rome'])

    # === VARIANTE B : ROME + OFFRES (config actuelle = self) ===

    # Évaluation des deux variantes sur les mêmes 24 CV
    def evaluate(vec, knn, df_train):
        top1, groupe = 0, 0
        for _, row in df_cv.iterrows():
            user_vec = vec.transform([row['cv_text'].lower()])
            _, indices = knn.kneighbors(user_vec, n_neighbors=1)
            pred_code = df_train.iloc[indices[0][0]]['code_rome']
            if pred_code == row['code_rome_manuel']:
                top1 += 1
            if get_groupe(pred_code) == row['groupe_thematique']:
                groupe += 1
        return top1 / len(df_cv), groupe / len(df_cv)

    acc_a_top1, acc_a_groupe = evaluate(vec_a, knn_a, df_rome_only)
    acc_b_top1, acc_b_groupe = evaluate(self.vectorizer, self.knn_model, self.df_trained)

    print(f"\\n   Variante A — ROME seul ({len(df_rome_only)} docs entraînement) :")
    print(f"      • Top-1 fine    : {acc_a_top1:.2%}")
    print(f"      • Acc groupe    : {acc_a_groupe:.2%}")
    print(f"\\n   Variante B — ROME + offres ({len(self.df_trained)} docs entraînement) :")
    print(f"      • Top-1 fine    : {acc_b_top1:.2%}")
    print(f"      • Acc groupe    : {acc_b_groupe:.2%}")
    print(f"\\n   ➜ Gain top-1 fine  : {(acc_b_top1 - acc_a_top1)*100:+.1f} pts")
    print(f"   ➜ Gain acc groupe  : {(acc_b_groupe - acc_a_groupe)*100:+.1f} pts")

    # Visualisation comparative
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = ['Top-1 fine\\n(94 codes)', 'Accuracy\\ngroupe thématique']
    x = np.arange(len(labels))
    width = 0.35
    ax.bar(x - width/2, [acc_a_top1, acc_a_groupe], width, label='ROME seul', color='#FF9999')
    ax.bar(x + width/2, [acc_b_top1, acc_b_groupe], width, label='ROME + offres FT', color='#66B2FF')
    ax.set_ylabel('Accuracy')
    ax.set_title("Apport des offres France Travail à la performance du KNN")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.set_ylim(0, 1)
    for i, (a, b) in enumerate(zip([acc_a_top1, acc_a_groupe], [acc_b_top1, acc_b_groupe])):
        ax.text(i - width/2, a + 0.02, f'{a:.0%}', ha='center', fontsize=9)
        ax.text(i + width/2, b + 0.02, f'{b:.0%}', ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig("data/ablation_offres.png", dpi=150)
    plt.close()
    print(f"📈 Figure : data/ablation_offres.png")

    return {
        "rome_only": {"top1": acc_a_top1, "groupe": acc_a_groupe},
        "rome_plus_offres": {"top1": acc_b_top1, "groupe": acc_b_groupe},
    }

def validate_non_determinism(self, cv_path="data/cv_annotes.csv", n_runs=20, sample_frac=0.9):
    """
    VALIDATION 2 — Mesure la stabilité du modèle face au non-déterminisme.
    On ré-entraîne le KNN n_runs fois en samplant 90% du training set
    avec un random_state différent à chaque run.
    Pour chaque CV, on regarde si la prédiction top-1 reste stable.
    """
    from collections import Counter
    from data.groupes_thematiques import get_groupe

    df_cv = pd.read_csv(os.path.join(self.data_path, "cv_annotes.csv"))
    print(f"\\n🎲 Validation non-déterminisme : {n_runs} runs × {len(df_cv)} CV")

    # Pour chaque CV, on stocke la liste des prédictions top-1 sur N runs
    preds_par_cv = {cv_id: [] for cv_id in df_cv['cv_id']}

    for run in range(n_runs):
        # Sample 90% du training avec random_state variable
        train_run = self.df_trained.sample(frac=sample_frac, random_state=run).reset_index(drop=True)

        vec_run = TfidfVectorizer(
            ngram_range=(1, 3), max_features=5000, max_df=0.5, min_df=2,
            stop_words=['ce', 'le', 'la', 'de', 'du', 'en', 'et',
                        'un', 'une', 'des', 'les', 'pour']
        )
        X_run = vec_run.fit_transform(train_run['all_text_knowledge'])
        knn_run = KNeighborsClassifier(n_neighbors=5, metric='cosine')
        knn_run.fit(X_run, train_run['code_rome'])

        for _, row in df_cv.iterrows():
            user_vec = vec_run.transform([row['cv_text'].lower()])
            _, indices = knn_run.kneighbors(user_vec, n_neighbors=1)
            pred = train_run.iloc[indices[0][0]]['code_rome']
            preds_par_cv[row['cv_id']].append(pred)

        if (run + 1) % 5 == 0:
            print(f"   Run {run+1}/{n_runs} ok")

    # Calcul de la stabilité par CV (modalité top-1 sur N runs)
    stabilite_par_cv = {}
    detail = []
    for cv_id, preds in preds_par_cv.items():
        c = Counter(preds)
        mode_code, mode_count = c.most_common(1)[0]
        stabilite = mode_count / n_runs
        stabilite_par_cv[cv_id] = stabilite
        detail.append({
            "cv_id": cv_id,
            "stabilite": stabilite,
            "code_modal": mode_code,
            "n_codes_uniques": len(c),
        })

    df_detail = pd.DataFrame(detail).sort_values("stabilite", ascending=False)
    df_detail.to_csv("data/non_determinism_detail.csv", index=False)

    stab_moy = np.mean(list(stabilite_par_cv.values()))
    stab_med = np.median(list(stabilite_par_cv.values()))
    n_unstable = sum(1 for s in stabilite_par_cv.values() if s < 0.7)

    print(f"\\n📊 Résultats stabilité :")
    print(f"   • Stabilité moyenne          : {stab_moy:.2%}")
    print(f"   • Stabilité médiane          : {stab_med:.2%}")
    print(f"   • CV instables (< 70%)       : {n_unstable}/{len(df_cv)}")

    # === VISUALISATION ===
    plt.figure(figsize=(12, 6))
    sorted_stab = sorted(stabilite_par_cv.values(), reverse=True)
    cv_labels = [d['cv_id'] for d in sorted(detail, key=lambda x: -x['stabilite'])]
    colors = ['#66BB6A' if s >= 0.7 else '#FFA726' if s >= 0.5 else '#EF5350' for s in sorted_stab]
    plt.bar(range(len(sorted_stab)), sorted_stab, color=colors)
    plt.axhline(y=stab_moy, color='blue', linestyle='--',
                label=f'Stabilité moyenne : {stab_moy:.2%}')
    plt.axhline(y=0.7, color='red', linestyle=':',
                label='Seuil acceptable (70%)')
    plt.xticks(range(len(sorted_stab)), cv_labels, rotation=45, ha='right', fontsize=8)
    plt.ylabel(f"% accord top-1 sur {n_runs} runs")
    plt.title(f"Non-déterminisme du modèle KNN ({n_runs} runs avec resampling)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("data/validation_non_determinisme.png", dpi=150)
    plt.close()
    print(f"📈 Figure : data/validation_non_determinisme.png")

    return {
        "stabilite_moyenne": stab_moy,
        "stabilite_mediane": stab_med,
        "n_cv_instables": n_unstable,
        "detail": stabilite_par_cv,
    }      

# ==========================================================
# PARTIE 2 : INTERFACE DASH
# ==========================================================

engine = ROMEAIEngine()

def get_ml_main_layout():
    return html.Div([
        html.Div([
            html.H1(["Analyse Profil & ", html.Span("Machine Learning", className="gradient-text")]),
            html.P("Validation scientifique du modèle KNN complétée.")
        ], className="analysis-hero text-center mb-5"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([html.Button("Texte", id="mode-cv-btn", n_clicks=1, className="mode-btn active"), 
                              html.Button("PDF", id="mode-pdf-btn", n_clicks=0, className="mode-btn")], className="mode-switch mb-4"),
                    dcc.Textarea(id="cv-text", className="modern-textarea mb-4", placeholder="Décrivez votre parcours..."),
                    dcc.Upload(id="upload-data", children=html.Div(['Déposer PDF']), className="pdf-upload-zone mb-4", style={"display":"none"}),
                    dbc.Button("Lancer l'Analyse", id="analyze-btn", className="hero-primary-btn w-100"),
                ], className="glass-card p-4")
            ], lg=8)
        ], justify="center"),
        html.Div(id="analysis-preview", className="mt-5")
    ])

layout = html.Div([dcc.Location(id='url-ml'), dcc.Store(id='cv-data-store', storage_type='session'), html.Div(id='page-content-ml', className="landing-container")])

@callback(Output('page-content-ml', 'children'), [Input('url-ml', 'search')])
def router(search):
    return get_ml_main_layout()

@callback([Output("cv-text", "style"), Output("upload-data", "style"), Output("mode-cv-btn", "className"), Output("mode-pdf-btn", "className")], 
          [Input("mode-cv-btn", "n_clicks"), Input("mode-pdf-btn", "n_clicks")])
def toggle(n1, n2):
    if ctx.triggered_id == "mode-pdf-btn": return {"display":"none"}, {"display":"block"}, "mode-btn", "mode-btn active"
    return {"display":"block"}, {"display":"none"}, "mode-btn active", "mode-btn"

@callback([Output("analysis-preview", "children"), Output("cv-data-store", "data")], 
          Input("analyze-btn", "n_clicks"), State("cv-text", "value"), State("upload-data", "contents"), State("mode-cv-btn", "className"))
def execute(n, text, pdf, c1):
    if not n: raise dash.exceptions.PreventUpdate
    source = text
    if "active" not in c1 and pdf:
        try:
            decoded = base64.b64decode(pdf.split(',')[1])
            reader = PyPDF2.PdfReader(io.BytesIO(decoded)); source = " ".join([p.extract_text() for p in reader.pages])
        except: return dbc.Alert("Erreur PDF", color="danger"), ""
    
    recs = engine.predict(source)
    if recs == "SIGNAL_INSUFFISANT": return dbc.Alert("Texte trop court pour l'IA", color="warning"), ""
    
    return html.Div([
        html.H4("Métiers Recommandés :", className="text-white mt-4"),
        html.Div([html.Div([
            html.Span(r['metier'], className="result-highlight"), 
            html.Small(f" Match : {r['score']}%")
        ], className="glass-card p-3 mb-2") for r in recs])
    ]), source

if __name__ == "__main__":
    engine.export_validation_scientifique()
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
    app.layout = layout
    app.run(debug=True, port=8050)

if __name__ == "__main__":
    engine = ROMEAIEngine()

    print("\\n" + "=" * 60)
    print("VALIDATION 1 — ACCURACY")
    print("=" * 60)
    engine.validate_accuracy_on_cvs()

    print("\\n" + "=" * 60)
    print("ÉTUDE D'ABLATION — APPORT DES OFFRES FT")
    print("=" * 60)
    engine.ablation_study_offres()

    print("\\n" + "=" * 60)
    print("VALIDATION 2 — NON-DÉTERMINISME")
    print("=" * 60)
    engine.validate_non_determinism(n_runs=20)