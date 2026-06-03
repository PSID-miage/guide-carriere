import os
import sys
import argparse
import traceback
import warnings
import json
import hashlib
import threading
import base64
import io

from sklearn.exceptions import EfficiencyWarning

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", category=EfficiencyWarning)

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_CURRENT_DIR) == "pages":
    _ROOT = os.path.dirname(_CURRENT_DIR)
else:
    _ROOT = _CURRENT_DIR

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, ctx

from urllib.parse import parse_qs, unquote
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
#from sentence_transformers import SentenceTransformer

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    dash.register_page(__name__, path="/ml", name="Analyse Profil")
except Exception:
    pass


class ROMEAIEngine:
    def __init__(self, data_path="data/", model_type="tfidf", output_dir=None):
        self.data_path = os.path.join(_ROOT, "data")
        self.model_type = model_type.lower().strip()

        if self.model_type not in ["tfidf", "camembert"]:
            raise ValueError("model_type doit être 'tfidf' ou 'camembert'.")

        self.model_name = "dangvantuan/sentence-camembert-base"
        self.batch_size = 32
        self.default_tfidf_threshold = 10.0
        self.default_camembert_threshold = 42.0
        self.max_text_chars = None

        self.output_dir = output_dir or os.path.join(
            self.data_path,
            "resultats_validation",
            self.model_type
        )
        os.makedirs(self.output_dir, exist_ok=True)

        self.cache_dir = os.path.join(self.data_path, "cache_camembert")
        self.embedding_cache_path = os.path.join(self.cache_dir, "embeddings_camembert.npy")
        self.embedding_meta_path = os.path.join(self.cache_dir, "embeddings_camembert_meta.json")
        os.makedirs(self.cache_dir, exist_ok=True)

        print(f"📂 [MOTEUR ML] Chemin absolu de DATA utilisé : {self.data_path}")
        print(f"🧪 [MOTEUR ML] Type de modèle : {self.model_type}")

        self.df_trained = self._build_knowledge_base()

        if self.df_trained.empty:
            self.df_trained = pd.DataFrame({
                "libelle_rome": ["Dataset vide"],
                "code_rome": ["N/A"],
                "all_text_knowledge": [""],
                "source": ["none"],
                "description": [""],
                "competences": [""],
                "libelle_competence": [[]],
                "libelle_savoir": [[]],
                "offre_url": [""]
            })

        if self.model_type == "tfidf":
            self._fit_tfidf()
        else:
            self._fit_camembert()

    def _fit_tfidf(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            max_df=0.5,
            min_df=2,
            stop_words=["ce", "le", "la", "de", "du", "en", "et", "un", "une", "des", "les", "pour"]
        )

        self.embedding_matrix = self.vectorizer.fit_transform(self.df_trained["all_text_knowledge"])

        self.knn_model = KNeighborsClassifier(n_neighbors=5, metric="cosine")
        self.knn_model.fit(self.embedding_matrix, self.df_trained["code_rome"])

        print("✅ TF-IDF + KNN initialisé")

    def _fit_camembert(self):
        print(f"🧠 [MOTEUR ML] Modèle sémantique utilisé : {self.model_name}")

        self.embedder = self._load_embedder()
        self.embedding_matrix = self._load_or_create_embeddings(
            self.df_trained["all_text_knowledge"].tolist()
        )

        self.knn_model = KNeighborsClassifier(n_neighbors=5, metric="cosine")
        self.knn_model.fit(self.embedding_matrix, self.df_trained["code_rome"])

        print("✅ CamemBERT + KNN initialisé")

    def _load_embedder(self):
        from sentence_transformers import SentenceTransformer
        try:
            return SentenceTransformer(self.model_name, local_files_only=True)
        except Exception:
            return SentenceTransformer(self.model_name)

    def _prepare_texts(self, texts):
        prepared = [str(t).lower().strip() for t in texts]

        if self.max_text_chars is not None:
            prepared = [t[:self.max_text_chars] for t in prepared]

        return prepared

    def _cache_signature(self, texts):
        prepared = self._prepare_texts(texts)
        text_hash = hashlib.sha256(
            "\n".join(prepared).encode("utf-8", errors="ignore")
        ).hexdigest()

        files = [
            "unix_referentiel_code_rome_v460_utf8.csv",
            "unix_liens_rome_referentiels_v460_utf8.csv",
            "unix_referentiel_competence_v460_utf8.csv",
            "unix_referentiel_savoir_v460_utf8.csv",
            "offres_ft_m18.csv"
        ]

        signature = {
            "model_name": self.model_name,
            "n_rows": int(len(self.df_trained)),
            "max_text_chars": self.max_text_chars,
            "text_hash": text_hash,
            "files": {}
        }

        for name in files:
            path = os.path.join(self.data_path, name)
            if os.path.exists(path):
                signature["files"][name] = {
                    "size": os.path.getsize(path),
                    "mtime": os.path.getmtime(path)
                }

        return signature

    def _load_or_create_embeddings(self, texts):
        signature = self._cache_signature(texts)

        if os.path.exists(self.embedding_cache_path) and os.path.exists(self.embedding_meta_path):
            try:
                with open(self.embedding_meta_path, "r", encoding="utf-8") as f:
                    old_signature = json.load(f)

                vectors = np.load(self.embedding_cache_path)

                if old_signature == signature and vectors.shape[0] == len(texts):
                    print(f"♻️ Embeddings CamemBERT chargés depuis le cache : {self.embedding_cache_path}")
                    return vectors

                print("⚠️ Cache CamemBERT existant mais non compatible, recalcul nécessaire.")
            except Exception:
                print("⚠️ Cache CamemBERT illisible, recalcul nécessaire.")

        print(f"🔢 Création du cache CamemBERT : {len(texts)} textes à encoder")
        vectors = self._encode_texts(texts)

        np.save(self.embedding_cache_path, vectors)

        with open(self.embedding_meta_path, "w", encoding="utf-8") as f:
            json.dump(signature, f, ensure_ascii=False, indent=2)

        print(f"✅ Cache CamemBERT sauvegardé : {self.embedding_cache_path}")
        return vectors

    def _encode_texts(self, texts):
        prepared = self._prepare_texts(texts)

        return self.embedder.encode(
            prepared,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True if len(prepared) > 50 else False
        )

    def _transform_texts(self, texts):
        if self.model_type == "tfidf":
            return self.vectorizer.transform([str(t).lower().strip() for t in texts])

        return self._encode_texts(texts)

    def _get_first_existing_column(self, df, candidates):
        for col in candidates:
            if col in df.columns:
                return col
        return None

    def _build_knowledge_base(self):
        try:
            def safe_read(name):
                path = os.path.join(self.data_path, name)
                if not os.path.exists(path):
                    print(f"❌ Fichier introuvable : {path}")
                    return pd.DataFrame()

                return pd.read_csv(
                    path,
                    sep=None,
                    engine="python",
                    encoding="utf-8",
                    on_bad_lines="skip"
                )

            df_rome = safe_read("unix_referentiel_code_rome_v460_utf8.csv")
            df_liens = safe_read("unix_liens_rome_referentiels_v460_utf8.csv")
            df_comp = safe_read("unix_referentiel_competence_v460_utf8.csv")
            df_savoir = safe_read("unix_referentiel_savoir_v460_utf8.csv")

            rome_rows = pd.DataFrame()

            if not df_rome.empty:
                for df in [df_rome, df_liens, df_comp, df_savoir]:
                    if not df.empty:
                        df.columns = df.columns.str.strip()

                df_rome = df_rome[df_rome["code_rome"].str.startswith("M18", na=False)]

                comp_merged = df_liens[df_liens["code_compo_bloc"] == 5].merge(
                    df_comp,
                    on="code_ogr",
                    how="inner"
                )
                agg_comp = comp_merged.groupby("code_rome")["libelle_competence"].apply(list).reset_index()

                savoir_merged = df_liens.merge(
                    df_savoir,
                    left_on="code_ogr",
                    right_on="code_ogr_savoir",
                    how="inner"
                )
                agg_savoir = savoir_merged.groupby("code_rome")["libelle_savoir"].apply(list).reset_index()

                rome_rows = df_rome.merge(agg_comp, on="code_rome", how="left").merge(
                    agg_savoir,
                    on="code_rome",
                    how="left"
                )

                rome_rows["libelle_competence"] = rome_rows["libelle_competence"].apply(
                    lambda x: x if isinstance(x, list) else []
                )
                rome_rows["libelle_savoir"] = rome_rows["libelle_savoir"].apply(
                    lambda x: x if isinstance(x, list) else []
                )

                rome_rows["all_text_knowledge"] = (
                    rome_rows["libelle_rome"].fillna("") + " " +
                    rome_rows["libelle_competence"].apply(lambda x: " ".join(x)) + " " +
                    rome_rows["libelle_savoir"].apply(lambda x: " ".join(x))
                ).str.lower().str.strip()

                rome_rows["source"] = "rome"
                rome_rows["description"] = ""
                rome_rows["competences"] = rome_rows["libelle_competence"].apply(lambda x: " | ".join(x))
                rome_rows["offre_url"] = ""

                rome_rows = rome_rows[
                    [
                        "code_rome",
                        "libelle_rome",
                        "all_text_knowledge",
                        "source",
                        "description",
                        "competences",
                        "libelle_competence",
                        "libelle_savoir",
                        "offre_url"
                    ]
                ]

                print(f"📚 {len(rome_rows)} fiches ROME M18 chargées")

            df_offres = safe_read("offres_ft_m18.csv")
            offres_rows = pd.DataFrame()

            if not df_offres.empty:
                df_offres.columns = df_offres.columns.str.strip()

                url_col = self._get_first_existing_column(
                    df_offres,
                    [
                        "url",
                        "url_offre",
                        "lien",
                        "lien_offre",
                        "origineOffre_urlOrigine",
                        "origine_url",
                        "offre_url"
                    ]
                )

                if url_col:
                    df_offres["offre_url"] = df_offres[url_col].fillna("")
                else:
                    df_offres["offre_url"] = ""

                if "description" not in df_offres.columns:
                    df_offres["description"] = ""

                if "competences" not in df_offres.columns:
                    df_offres["competences"] = ""

                if "libelle_offre" not in df_offres.columns:
                    df_offres["libelle_offre"] = df_offres.get("intitule", "")

                df_offres["all_text_knowledge"] = (
                    df_offres["libelle_offre"].fillna("") + " " +
                    df_offres["description"].fillna("") + " " +
                    df_offres["competences"].fillna("")
                ).str.lower().str.strip()

                df_offres["libelle_rome"] = df_offres["libelle_offre"].fillna("Offre sans titre")
                df_offres["source"] = "offre"
                df_offres["libelle_competence"] = [[] for _ in range(len(df_offres))]
                df_offres["libelle_savoir"] = [[] for _ in range(len(df_offres))]

                offres_rows = df_offres[
                    [
                        "code_rome",
                        "libelle_rome",
                        "all_text_knowledge",
                        "source",
                        "description",
                        "competences",
                        "libelle_competence",
                        "libelle_savoir",
                        "offre_url"
                    ]
                ]

                print(f"💼 {len(offres_rows)} offres FT chargées")

            if rome_rows.empty and offres_rows.empty:
                return pd.DataFrame()

            combined = pd.concat([rome_rows, offres_rows], ignore_index=True)
            combined = combined[combined["all_text_knowledge"].str.len() > 20].reset_index(drop=True)
            combined["doc_id"] = combined.index.astype(int)

            print(f"🎯 Total base de connaissances : {len(combined)} lignes")
            return combined

        except Exception as e:
            print(f"❌ Erreur build_knowledge_base : {e}")
            return pd.DataFrame()

    def predict(self, user_input, top_n=3, threshold_score=None):
        if not user_input or len(str(user_input).strip()) < 30:
            return "SIGNAL_INSUFFISANT"

        if threshold_score is None:
            if self.model_type == "tfidf":
                threshold_score = self.default_tfidf_threshold
            else:
                threshold_score = self.default_camembert_threshold

        user_vec = self._transform_texts([user_input])

        if self.model_type == "tfidf" and getattr(user_vec, "nnz", 1) == 0:
            return "HORS_PERIMETRE"

        distances, indices = self.knn_model.kneighbors(user_vec, n_neighbors=top_n)

        results = []
        
        seen_rome_codes = set() # Pour éviter les doublons dans les 3 résultats

        for i, idx in enumerate(indices[0]):
            row = self.df_trained.iloc[int(idx)]
            score = round((1 - distances[0][i]) * 100, 1)

            # On récupère le code ROME (qu'il vienne d'une offre ou d'un métier)
            rome_code = row['code_rome']
            
            if rome_code not in seen_rome_codes and score >= (threshold_score or self.default_tfidf_threshold):
                # On va chercher la fiche ROME officielle
                fiche_rome = self.get_rome_reference_by_code(rome_code)
                if fiche_rome is not None:
                    results.append({
                        "doc_id": int(fiche_rome.name), # ID de la fiche ROME
                        "metier": fiche_rome["libelle_rome"],
                        "code": rome_code,
                        "score": score
                    })
                    seen_rome_codes.add(rome_code)

        if not results:
            return "HORS_PERIMETRE"

        return results

    def get_document_detail(self, doc_id):
        try:
            doc_id = int(doc_id)
            if doc_id < 0 or doc_id >= len(self.df_trained):
                return None

            row = self.df_trained.iloc[doc_id]
            return row
        except Exception:
            return None

    def get_rome_reference_by_code(self, code_rome):
        try:
            rows = self.df_trained[
                (self.df_trained["code_rome"] == code_rome) &
                (self.df_trained["source"] == "rome")
            ]

            if rows.empty:
                return None

            return rows.iloc[0]
        except Exception:
            return None

    def validate_accuracy_on_cvs(self, cv_path="data/cv_annotes.csv"):
        from sklearn.metrics import confusion_matrix, classification_report
        from data.groupes_thematiques import get_groupe

        df_cv = pd.read_csv(os.path.join(self.data_path, "cv_annotes.csv"))

        print(f"\n🎯 Validation sur {len(df_cv)} CV étiquetés\n")

        correct_top1 = 0
        correct_top3 = 0
        correct_groupe = 0

        y_true_groupe, y_pred_groupe = [], []

        for _, row in df_cv.iterrows():
            recs = self.predict(row["cv_text"], top_n=3)

            if recs in ["SIGNAL_INSUFFISANT", "HORS_PERIMETRE"]:
                print(f"  ⚠️  CV {row['cv_id']} ignoré")
                continue

            codes_pred = [r["code"] for r in recs]
            code_vrai = row["code_rome_manuel"]
            groupe_vrai = row["groupe_thematique"]
            groupe_pred = get_groupe(codes_pred[0])

            if codes_pred[0] == code_vrai:
                correct_top1 += 1

            if code_vrai in codes_pred:
                correct_top3 += 1

            if groupe_vrai == groupe_pred:
                correct_groupe += 1

            y_true_groupe.append(groupe_vrai)
            y_pred_groupe.append(groupe_pred)

        n = len(y_true_groupe)

        if n == 0:
            raise ValueError("Aucun CV exploitable pour la validation.")

        metrics = {
            "n_cv": n,
            "top1_fine": correct_top1 / n,
            "top3_fine": correct_top3 / n,
            "accuracy_groupe": correct_groupe / n,
        }

        print("📊 Résultats globaux :")
        print(f"   • Accuracy top-1 (ROME exact)    : {metrics['top1_fine']:.2%}")
        print(f"   • Accuracy top-3 (ROME exact)    : {metrics['top3_fine']:.2%}")
        print(f"   • Accuracy groupe thématique     : {metrics['accuracy_groupe']:.2%}  ⬅️ métrique principale")

        report = classification_report(y_true_groupe, y_pred_groupe, zero_division=0)

        print("\n📋 Classification report (par groupe thématique) :")
        print(report)

        with open(os.path.join(self.output_dir, "classification_report.txt"), "w", encoding="utf-8") as f:
            f.write(report)

        labels = sorted(set(y_true_groupe + y_pred_groupe))
        cm = confusion_matrix(y_true_groupe, y_pred_groupe, labels=labels)

        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
        plt.title(f"Matrice de confusion — par groupe thématique ({self.model_type})")
        plt.ylabel("Vrai groupe (annotation manuelle)")
        plt.xlabel("Groupe prédit (KNN)")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "validation_accuracy_groupe.png"), dpi=150)
        plt.close()

        print(f"📈 Figure : {os.path.join(self.output_dir, 'validation_accuracy_groupe.png')}")

        return metrics

    def ablation_study_offres(self, cv_path="data/cv_annotes.csv"):
        from data.groupes_thematiques import get_groupe

        df_cv = pd.read_csv(os.path.join(self.data_path, "cv_annotes.csv"))

        print("\n🔬 Étude d'ablation : ROME seul vs ROME + offres FT")

        df_rome_only = self.df_trained[self.df_trained["source"] == "rome"].reset_index(drop=True)

        if self.model_type == "tfidf":
            model_a = TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=5000,
                max_df=0.5,
                min_df=2,
                stop_words=["ce", "le", "la", "de", "du", "en", "et", "un", "une", "des", "les", "pour"]
            )
            X_a = model_a.fit_transform(df_rome_only["all_text_knowledge"])
        else:
            model_a = None
            X_a = self._encode_texts(df_rome_only["all_text_knowledge"].tolist())

        knn_a = KNeighborsClassifier(n_neighbors=5, metric="cosine")
        knn_a.fit(X_a, df_rome_only["code_rome"])

        def evaluate(knn, df_train, vectorizer=None):
            top1, groupe = 0, 0

            for _, row in df_cv.iterrows():
                if self.model_type == "tfidf":
                    user_vec = vectorizer.transform([str(row["cv_text"]).lower().strip()])
                else:
                    user_vec = self._encode_texts([row["cv_text"]])

                _, indices = knn.kneighbors(user_vec, n_neighbors=1)
                pred_code = df_train.iloc[indices[0][0]]["code_rome"]

                if pred_code == row["code_rome_manuel"]:
                    top1 += 1

                if get_groupe(pred_code) == row["groupe_thematique"]:
                    groupe += 1

            return top1 / len(df_cv), groupe / len(df_cv)

        acc_a_top1, acc_a_groupe = evaluate(knn_a, df_rome_only, model_a)

        if self.model_type == "tfidf":
            acc_b_top1, acc_b_groupe = evaluate(self.knn_model, self.df_trained, self.vectorizer)
        else:
            acc_b_top1, acc_b_groupe = evaluate(self.knn_model, self.df_trained)

        ablation_metrics = {
            "rome_only_top1": acc_a_top1,
            "rome_only_groupe": acc_a_groupe,
            "rome_plus_offres_top1": acc_b_top1,
            "rome_plus_offres_groupe": acc_b_groupe,
            "gain_top1": acc_b_top1 - acc_a_top1,
            "gain_groupe": acc_b_groupe - acc_a_groupe,
        }

        print(f"\n   Variante A — ROME seul ({len(df_rome_only)} docs entraînement) :")
        print(f"      • Top-1 fine    : {acc_a_top1:.2%}")
        print(f"      • Acc groupe    : {acc_a_groupe:.2%}")

        print(f"\n   Variante B — ROME + offres ({len(self.df_trained)} docs entraînement) :")
        print(f"      • Top-1 fine    : {acc_b_top1:.2%}")
        print(f"      • Acc groupe    : {acc_b_groupe:.2%}")

        print(f"\n   ➜ Gain top-1 fine  : {(acc_b_top1 - acc_a_top1) * 100:+.1f} pts")
        print(f"   ➜ Gain acc groupe  : {(acc_b_groupe - acc_a_groupe) * 100:+.1f} pts")

        fig, ax = plt.subplots(figsize=(8, 5))

        labels = ["Top-1 fine\n(94 codes)", "Accuracy\ngroupe thématique"]
        x = np.arange(len(labels))
        width = 0.35

        ax.bar(x - width / 2, [acc_a_top1, acc_a_groupe], width, label="ROME seul", color="#FF9999")
        ax.bar(x + width / 2, [acc_b_top1, acc_b_groupe], width, label="ROME + offres FT", color="#66B2FF")
        ax.set_ylabel("Accuracy")
        ax.set_title(f"Apport des offres France Travail — {self.model_type}")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.set_ylim(0, 1)

        for i, (a, b) in enumerate(zip([acc_a_top1, acc_a_groupe], [acc_b_top1, acc_b_groupe])):
            ax.text(i - width / 2, a + 0.02, f"{a:.0%}", ha="center", fontsize=9)
            ax.text(i + width / 2, b + 0.02, f"{b:.0%}", ha="center", fontsize=9)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "ablation_offres.png"), dpi=150)
        plt.close()

        print(f"📈 Figure : {os.path.join(self.output_dir, 'ablation_offres.png')}")

        return ablation_metrics

    def validate_non_determinism(self, cv_path="data/cv_annotes.csv", n_runs=20, sample_frac=0.9):
        from collections import Counter

        df_cv = pd.read_csv(os.path.join(self.data_path, "cv_annotes.csv"))

        print(f"\n🎲 Validation non-déterminisme : {n_runs} runs × {len(df_cv)} CV")

        preds_par_cv = {cv_id: [] for cv_id in df_cv["cv_id"]}

        if self.model_type == "camembert":
            cv_embeddings = self._encode_texts(df_cv["cv_text"].fillna("").tolist())
        else:
            cv_embeddings = None

        for run in range(n_runs):
            train_sample = self.df_trained.sample(frac=sample_frac, random_state=run)

            if self.model_type == "tfidf":
                train_run = train_sample.reset_index(drop=True)
                vec_run = TfidfVectorizer(
                    ngram_range=(1, 3),
                    max_features=5000,
                    max_df=0.5,
                    min_df=2,
                    stop_words=["ce", "le", "la", "de", "du", "en", "et", "un", "une", "des", "les", "pour"]
                )
                X_run = vec_run.fit_transform(train_run["all_text_knowledge"])
            else:
                idx_run = train_sample.index.to_numpy()
                X_run = self.embedding_matrix[idx_run]
                train_run = train_sample.reset_index(drop=True)
                vec_run = None

            knn_run = KNeighborsClassifier(n_neighbors=5, metric="cosine")
            knn_run.fit(X_run, train_run["code_rome"])

            for row_pos, row in df_cv.reset_index(drop=True).iterrows():
                if self.model_type == "tfidf":
                    user_vec = vec_run.transform([str(row["cv_text"]).lower().strip()])
                else:
                    user_vec = cv_embeddings[row_pos].reshape(1, -1)

                _, indices = knn_run.kneighbors(user_vec, n_neighbors=1)
                pred = train_run.iloc[indices[0][0]]["code_rome"]
                preds_par_cv[row["cv_id"]].append(pred)

            if (run + 1) % 5 == 0:
                print(f"   Run {run + 1}/{n_runs} ok")

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

        df_export = pd.DataFrame(detail)
        df_export.to_csv(os.path.join(self.output_dir, "non_determinism_detail.csv"), index=False)

        stab_moy = float(np.mean(list(stabilite_par_cv.values())))
        stab_med = float(np.median(list(stabilite_par_cv.values())))
        n_unstable = sum(1 for s in stabilite_par_cv.values() if s < 0.7)

        stability_metrics = {
            "stabilite_moyenne": stab_moy,
            "stabilite_mediane": stab_med,
            "n_cv_instables": n_unstable,
        }

        print("\n📊 Résultats stabilité :")
        print(f"   • Stabilité moyenne          : {stab_moy:.2%}")
        print(f"   • Stabilité médiane          : {stab_med:.2%}")
        print(f"   • CV instables (< 70%)       : {n_unstable}/{len(df_cv)}")

        plt.figure(figsize=(12, 6))

        sorted_stab = sorted(stabilite_par_cv.values(), reverse=True)
        cv_labels = [d["cv_id"] for d in sorted(detail, key=lambda x: -x["stabilite"])]
        colors = ["#66BB6A" if s >= 0.7 else "#FFA726" if s >= 0.5 else "#EF5350" for s in sorted_stab]

        plt.bar(range(len(sorted_stab)), sorted_stab, color=colors)
        plt.axhline(y=stab_moy, color="blue", linestyle="--", label=f"Stabilité moyenne : {stab_moy:.2%}")
        plt.axhline(y=0.7, color="red", linestyle=":", label="Seuil acceptable (70%)")
        plt.xticks(range(len(sorted_stab)), cv_labels, rotation=45, ha="right", fontsize=8)
        plt.ylabel(f"% accord top-1 sur {n_runs} runs")
        plt.title(f"Non-déterminisme du modèle KNN — {self.model_type}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "validation_non_determinisme.png"), dpi=150)
        plt.close()

        print(f"📈 Figure : {os.path.join(self.output_dir, 'validation_non_determinisme.png')}")

        return stability_metrics
    
    def get_offres_by_rome(self, code_rome, limit=3):
        # Filtre sur la base de données entière pour trouver les offres liées
        offres = self.df_trained[
            (self.df_trained['code_rome'] == code_rome) & 
            (self.df_trained['source'] == 'offre')
        ]
        return offres.head(limit).to_dict('records')


_engine_singleton = None
_engine_lock = threading.Lock()


def get_engine():
    global _engine_singleton

    if _engine_singleton is None:
        with _engine_lock:
            if _engine_singleton is None:
                _engine_singleton = ROMEAIEngine(model_type="tfidf")

    return _engine_singleton


def _clean_display(value):
    if value is None:
        return ""

    value = str(value).strip()

    if value.lower() in ["nan", "none", "null"]:
        return ""

    return value


def _as_list(value, limit=10):
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()][:limit]

    value = _clean_display(value)

    if value:
        parts = [p.strip() for p in value.replace(";", "|").replace(",", "|").split("|") if p.strip()]
        return parts[:limit]

    return []


def get_ml_main_layout():
    return html.Div([
        html.Div([
            html.H1(["Analyse Profil & ", html.Span("Machine Learning", className="gradient-text")]),
            html.P("Recommandation de métiers IT à partir d'un CV.")
        ], className="analysis-hero text-center mb-5"),

        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Button("Texte", id="mode-cv-btn", n_clicks=1, className="mode-btn active"),
                        html.Button("PDF", id="mode-pdf-btn", n_clicks=0, className="mode-btn")
                    ], className="mode-switch mb-4"),

                    dcc.Textarea(
                        id="cv-text",
                        className="modern-textarea mb-4",
                        placeholder="Décrivez votre parcours..."
                    ),

                    dcc.Upload(
                        id="upload-data",
                        children=html.Div(["Déposer PDF"]),
                        className="pdf-upload-zone mb-4",
                        style={"display": "none"}
                    ),

                    dbc.Button(
                        "Lancer l'Analyse",
                        id="analyze-btn",
                        className="hero-primary-btn w-100"
                    ),

                    dcc.Link(
                        "Voir la validation des modèles",
                        href="/validation",
                        className="btn btn-outline-info w-100 mt-3"
                    )
                ], className="glass-card p-4")
            ], lg=8)
        ], justify="center"),

        html.Div(id="analysis-preview", className="mt-5")
    ])

def construire_url_ft(rome_code):
    return f"https://candidat.francetravail.fr/offres/recherche?rome={rome_code}"

def get_detail_layout(code_rome):
    # 1. Récupération des données ROME
    df = get_engine().df_trained
    rome_data = df[(df['code_rome'] == code_rome) & (df['source'] == 'rome')]

    if rome_data.empty:
        return html.Div([
            dcc.Link("← Retour à l'analyse", href="/ml", className="back-link mb-4"),
            dbc.Alert("Fiche métier ROME introuvable.", color="warning")
        ], className="landing-container")

    row = rome_data.iloc[0]
    offres = get_engine().get_offres_by_rome(code_rome)

    # Styles
    text_style = {"color": "#EAF2FF", "fontSize": "16px", "lineHeight": "1.8", "whiteSpace": "pre-line"}
    soft_text_style = {"color": "#BFD0E8", "fontSize": "15px", "lineHeight": "1.7"}
    title_style = {"color": "#FFFFFF", "fontWeight": "700"}
    card_style = {"background": "rgba(20, 34, 58, 0.92)", "border": "1px solid rgba(255, 255, 255, 0.12)", "borderRadius": "22px", "boxShadow": "0 18px 45px rgba(0, 0, 0, 0.25)"}
    badge_style = {"background": "linear-gradient(90deg, #27D3FF, #7C5CFF)", "color": "#FFFFFF", "padding": "8px 14px", "borderRadius": "999px", "fontWeight": "700", "display": "inline-block", "marginBottom": "16px"}

    # Extraction des données
    title = row.get("libelle_rome", "Métier inconnu")
    skills = _as_list(row.get("libelle_competence", []), limit=12)
    savoirs = _as_list(row.get("libelle_savoir", []), limit=12)

    return html.Div([
        dcc.Link("← Retour à l'analyse", href="/ml", className="back-link mb-4", style={"color": "#8FE7FF", "fontWeight": "600", "textDecoration": "none"}),

        # Header
        html.Div([
            html.Span("Fiche Métier ROME", style=badge_style),
            html.H1(title, className="gradient-text mb-3"),
            html.P(f"Code ROME : {code_rome}", style=soft_text_style),
        ], className="glass-card p-4 mb-4", style=card_style),

        # Grille principale
        dbc.Row([
            # Colonne 1 : Compétences & Savoirs
            dbc.Col([
                html.Div([
                    html.H4("Compétences clés", className="mb-3", style=title_style),
                    html.Ul([html.Li(c, style={**text_style, "marginBottom": "10px"}) for c in skills], style={"paddingLeft": "22px"}),
                    
                    html.H4("Savoirs associés", className="mt-4 mb-3", style=title_style),
                    html.Ul([html.Li(s, style={**text_style, "marginBottom": "10px"}) for s in savoirs], style={"paddingLeft": "22px"}),
                ], className="glass-card p-4 h-100", style=card_style)
            ], lg=7, className="mb-4"),

           # Colonne 2 : Offres France Travail
            dbc.Col([
                html.Div([
                    html.H4(f"Offres France Travail ({len(offres)})", className="mb-3", style=title_style),
                    
                    # 1. Liste des titres des offres (juste visuel)
                    html.Div([
                        html.Div([
                            html.P(o.get('libelle_rome', 'Offre'), className="fw-bold text-white mb-0"),
                        ], className="glass-card p-3 mb-2", style={"background": "rgba(255,255,255,0.05)"})
                        for o in offres[:5]
                    ]) if offres else html.P("Aucune offre disponible.", style=text_style),
                    
                    # 2. Bouton unique de redirection générale
                    html.A(
                        "Voir toutes les offres sur France Travail",
                        href=construire_url_ft(code_rome),
                        target="_blank",
                        className="btn btn-primary mt-3 w-100",
                        style={"background": "linear-gradient(90deg, #27D3FF, #7C5CFF)", "border": "none", "fontWeight": "600"}
                    ) if offres else None
                    
                ], className="glass-card p-4 h-100", style=card_style)
            ], lg=5, className="mb-4")
        ])
    ], className="landing-container")


layout = html.Div([
    dcc.Location(id="url-ml", refresh=False),
    html.Div(id="page-content-ml", className="landing-container")
])


@callback(
    Output("page-content-ml", "children"),
    Input("url-ml", "search")
)
def router(search):
    if search:
        params = parse_qs(search.lstrip("?"))
        if "doc_id" in params:
            return get_detail_layout(unquote(params["doc_id"][0]))

    return get_ml_main_layout()


@callback(
    [
        Output("cv-text", "style"),
        Output("upload-data", "style"),
        Output("mode-cv-btn", "className"),
        Output("mode-pdf-btn", "className")
    ],
    [
        Input("mode-cv-btn", "n_clicks"),
        Input("mode-pdf-btn", "n_clicks")
    ]
)
def toggle(n1, n2):
    if ctx.triggered_id == "mode-pdf-btn":
        return {"display": "none"}, {"display": "block"}, "mode-btn", "mode-btn active"

    return {"display": "block"}, {"display": "none"}, "mode-btn active", "mode-btn"


@callback(
    [
        Output("analysis-preview", "children"),
        Output("cv-data-store", "data")
    ],
    Input("analyze-btn", "n_clicks"),
    State("cv-text", "value"),
    State("upload-data", "contents"),
    State("mode-cv-btn", "className")
)
def execute(n, text, pdf, c1):
    if not n:
        raise dash.exceptions.PreventUpdate

    source = text or ""

    if "active" not in c1 and pdf:
        if PyPDF2 is None:
            return dbc.Alert("PyPDF2 n'est pas installé.", color="danger"), ""

        try:
            decoded = base64.b64decode(pdf.split(",")[1])
            reader = PyPDF2.PdfReader(io.BytesIO(decoded))
            source = " ".join([p.extract_text() or "" for p in reader.pages])
        except Exception:
            return dbc.Alert("Erreur lors de la lecture du PDF.", color="danger"), ""

    recs = get_engine().predict(source)

    if recs == "SIGNAL_INSUFFISANT":
        return dbc.Alert("Texte trop court pour l'analyse.", color="warning"), source

    if recs == "HORS_PERIMETRE":
        return html.Div([
            dbc.Alert(
                [
                    html.H5("🚫 Profil hors périmètre", className="alert-heading fw-bold"),
                    html.P(
                        "Les compétences détectées ne correspondent pas suffisamment aux métiers de l'Informatique et du Numérique "
                        "(Famille ROME M18). Le modèle refuse la classification pour éviter un faux résultat."
                    )
                ],
                color="white",
                className="mt-4 glass-card"
            )
        ]), source

    return html.Div([
        html.H4("Métiers recommandés :", className="text-white mt-4"),
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.Span(r["metier"], className="result-highlight"),
                        html.Small(
                            f" Match : {r['score']}%",
                            className="text-white fw-bold",
                            style={"fontSize": "1.1em"}
                        )
                    ], className="d-flex justify-content-between align-items-center mb-1"),

                    dbc.Progress(
                        value=r["score"],
                        color="success" if r["score"] >= 20.0 else "warning",
                        className="mb-2",
                        style={"height": "12px"}
                    ),

                    html.Div([
                        html.Small(
                            # Remplace la ligne problématique par celle-ci :
                            f"Code ROME : {r.get('code', 'N/A')} | Source : {r.get('source', 'Fiche ROME')}",
                            className="text-muted"
                        ),

                        dcc.Link(
                            "Voir détail",
                            href=f"/ml?doc_id={r['code']}", # On envoie le code ROME ici
                            className="btn btn-sm btn-outline-info ms-3"
                        )
                    ], className="d-flex justify-content-between align-items-center")
                ])
            ], className="glass-card p-3 mb-2") for r in recs
        ])
    ]), source


def _safe(label, fn, *args, **kwargs):
    print("\n" + "=" * 60)
    print(label)
    print("=" * 60)

    try:
        result = fn(*args, **kwargs)
        print(f"✅ {label} OK")
        return result
    except Exception as e:
        print(f"❌ {label} a planté : {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


def _save_summary(model_type, output_dir, accuracy, ablation, stability):
    summary = {"model_type": model_type}

    if accuracy:
        summary.update(accuracy)

    if ablation:
        summary.update(ablation)

    if stability:
        summary.update(stability)

    pd.DataFrame([summary]).to_csv(os.path.join(output_dir, "metrics_summary.csv"), index=False)

    with open(os.path.join(output_dir, "metrics_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


def run_validations(model_type="tfidf"):
    output_dir = os.path.join(_ROOT, "data", "resultats_validation", model_type)
    os.makedirs(output_dir, exist_ok=True)

    eng = ROMEAIEngine(model_type=model_type, output_dir=output_dir)

    accuracy = _safe("VALIDATION 1 — ACCURACY", eng.validate_accuracy_on_cvs)
    ablation = _safe("ÉTUDE D'ABLATION — APPORT DES OFFRES FT", eng.ablation_study_offres)
    stability = _safe("VALIDATION 2 — NON-DÉTERMINISME", eng.validate_non_determinism, n_runs=20)

    return _save_summary(model_type, output_dir, accuracy, ablation, stability)


def run_both_validations():
    results = []

    results.append(run_validations("tfidf"))
    results.append(run_validations("camembert"))

    comparison_path = os.path.join(_ROOT, "data", "resultats_validation", "comparaison_tfidf_camembert.csv")
    pd.DataFrame(results).to_csv(comparison_path, index=False)

    print(f"\n📊 Comparaison sauvegardée : {comparison_path}")


def run_dash_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
    app.layout = html.Div([
        dcc.Store(id="cv-data-store", data={}),
        layout
    ])
    app.run(debug=False, use_reloader=False, dev_tools_hot_reload=False, port=8050)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["app", "validate"],
        default="app",
        help="'app' lance le dashboard Dash, 'validate' lance les validations.",
    )

    parser.add_argument(
        "--model",
        choices=["tfidf", "camembert", "both"],
        default="tfidf",
        help="Modèle à utiliser pour la validation.",
    )

    args = parser.parse_args()

    if args.mode == "app":
        run_dash_app()
    elif args.model == "both":
        run_both_validations()
    else:
        run_validations(args.model)