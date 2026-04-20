
from __future__ import annotations

import os
import pandas as pd
import plotly.express as px


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Palette alignée avec la home
HOME_CYAN = "#22D3EE"
HOME_BLUE = "#38BDF8"
HOME_BLUE_SOFT = "#60A5FA"
HOME_PURPLE = "#8B5CF6"
HOME_MINT = "#99F6E4"
HOME_NAVY = "#0F172A"


def load_liens() -> pd.DataFrame:
    """
    Charge la table des liaisons métier compétence (code_rome ↔ code_ogr) et
    filtre pour ne garder que les compétences (code_compo_bloc == 5).
    """
    liens_path = os.path.join(DATA_DIR, "unix_liens_rome_referentiels_v460_utf8.csv")
    df = pd.read_csv(liens_path)
    return df[df["code_compo_bloc"] == 5].copy()


def load_competences() -> pd.DataFrame:
    """
    Charge le référentiel des compétences (libellé, catégorie, sous-catégorie).
    """
    path = os.path.join(DATA_DIR, "unix_referentiel_competence_v460_utf8.csv")
    return pd.read_csv(path)


def load_metiers() -> pd.DataFrame:
    """
    Charge le référentiel des métiers (code_rome ↔ libellé_rome).
    """
    path = os.path.join(DATA_DIR, "unix_referentiel_code_rome_v460_utf8.csv")
    return pd.read_csv(path)


def load_cr_gd_dp_mapping() -> pd.DataFrame:
    """
    Charge la table d’association métier : grand domaine (code_rome : libelle_grand_domaine)
    depuis le fichier `unix_cr_gd_dp_v460_utf8.csv`.
    """
    path = os.path.join(DATA_DIR, "unix_cr_gd_dp_v460_utf8.csv")
    df = pd.read_csv(path)
    return df[["code_rome", "libelle_grand_domaine"]]


def plot_top_competences(liens: pd.DataFrame, competences: pd.DataFrame, top_n: int = 15):
    counts = (
        liens.groupby("code_ogr")["code_rome"]
        .nunique()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index(name="Nombre de métiers concernés")
    )
    df = counts.merge(competences[["code_ogr", "libelle_competence"]], on="code_ogr", how="left")
    fig = px.bar(
        df,
        x="Nombre de métiers concernés",
        y="libelle_competence",
        orientation="h",
        title=f"Top {top_n} compétences transversales",
        labels={"libelle_competence": "Compétence"},
        color_discrete_sequence=[HOME_BLUE],
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(color=HOME_NAVY),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return df, fig


def plot_category_distribution(liens: pd.DataFrame, competences: pd.DataFrame):
    merged = liens.merge(competences[["code_ogr", "cat_comp"]], on="code_ogr", how="left")
    cat_counts = merged["cat_comp"].value_counts(dropna=False).reset_index()
    cat_counts.columns = ["Catégorie", "Nombre d'occurrences"]
    fig = px.bar(
        cat_counts,
        x="Catégorie",
        y="Nombre d'occurrences",
        title="Part des catégories de compétences",
        color_discrete_sequence=[HOME_CYAN],
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(color=HOME_NAVY),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return cat_counts, fig


def plot_subcategory_distribution(competences: pd.DataFrame):
    sub_counts = competences["sous_cat_comp"].value_counts().reset_index()
    sub_counts.columns = ["Sous-catégorie", "Nombre de compétences"]
    fig = px.bar(
        sub_counts,
        x="Sous-catégorie",
        y="Nombre de compétences",
        title="Répartition des sous-catégories de compétences",
        color_discrete_sequence=[HOME_PURPLE],
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(color=HOME_NAVY),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return sub_counts, fig


def plot_ratio_transverse(liens: pd.DataFrame, competences: pd.DataFrame, metiers: pd.DataFrame, top_n: int = 10):
    total_comp = liens.groupby("code_rome")["code_ogr"].nunique().rename("total_comp")
    comp_transverse = (
        liens.merge(competences[["code_ogr", "sous_cat_comp"]], on="code_ogr", how="left")
        .query("sous_cat_comp == 'Transverse'")
        .groupby("code_rome")["code_ogr"]
        .nunique()
        .rename("nb_transverse")
    )
    ratio = pd.concat([total_comp, comp_transverse], axis=1).fillna(0)
    ratio["Part de compétences transversales"] = ratio["nb_transverse"] / ratio["total_comp"]
    ratio = ratio.reset_index().merge(metiers[["code_rome", "libelle_rome"]], on="code_rome", how="left")
    top_ratio = ratio.sort_values("Part de compétences transversales", ascending=False).head(top_n)
    fig = px.bar(
        top_ratio,
        x="Part de compétences transversales",
        y="libelle_rome",
        orientation="h",
        title=f"Top {top_n} métiers valorisant les compétences transversales",
        labels={"libelle_rome": "Métier"},
        color_discrete_sequence=[HOME_BLUE_SOFT],
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(color=HOME_NAVY),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return top_ratio, fig


def compute_domain_skill_summary(liens: pd.DataFrame, domain_df: pd.DataFrame):
    job_counts = liens.groupby("code_rome")["code_ogr"].nunique().rename("Nombre de compétences").reset_index()
    job_domain = job_counts.merge(domain_df, on="code_rome", how="left")
    summary = job_domain.groupby("libelle_grand_domaine").agg(
        Moyenne_competences=("Nombre de compétences", "mean"),
        Nombre_de_metiers=("code_rome", "count"),
    ).reset_index()
    return summary


def plot_domain_skill_summary(summary_df: pd.DataFrame):
    fig = px.bar(
        summary_df,
        x="libelle_grand_domaine",
        y="Moyenne_competences",
        title="Nombre moyen de compétences par domaine",
        labels={"libelle_grand_domaine": "Domaine", "Moyenne_competences": "Moyenne de compétences"},
        color_discrete_sequence=[HOME_PURPLE],
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(color=HOME_NAVY),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return summary_df, fig


def prepare_domain_job_skill_breakdown(liens: pd.DataFrame, competences: pd.DataFrame, metiers: pd.DataFrame, domain_df: pd.DataFrame):
    merged = (
        liens.merge(domain_df, on="code_rome", how="left")
             .merge(competences[["code_ogr", "sous_cat_comp", "cat_comp"]], on="code_ogr", how="left")
    )
    pivot_sub = merged.pivot_table(
        index=["libelle_grand_domaine", "code_rome"],
        columns="sous_cat_comp",
        values="code_ogr",
        aggfunc=pd.Series.nunique,
        fill_value=0
    ).reset_index()
    se = (
        merged[merged["cat_comp"] == "Savoir-être professionnel"]
        .groupby(["libelle_grand_domaine", "code_rome"])["code_ogr"]
        .nunique()
        .rename("Savoir-être")
        .reset_index()
    )
    breakdown = pivot_sub.merge(se, on=["libelle_grand_domaine", "code_rome"], how="left").fillna(0)
    breakdown = breakdown.merge(metiers[["code_rome", "libelle_rome"]], on="code_rome", how="left")
    return breakdown


def plot_job_skill_breakdown(job_skill_counts: pd.DataFrame, selected_code_rome: str):
    row = job_skill_counts[job_skill_counts["code_rome"] == selected_code_rome]
    if row.empty:
        return px.bar(title="Métier non trouvé")

    row = row.iloc[0]
    cols = [c for c in row.index if c not in ["libelle_grand_domaine", "code_rome", "libelle_rome"]]
    data = pd.DataFrame({
        "Type de compétence": cols,
        "Nombre": [int(row[c]) for c in cols],
    })

    fig = px.bar(
        data,
        x="Type de compétence",
        y="Nombre",
        title=f"Répartition des compétences pour {row['libelle_rome']}",
        color="Type de compétence",
        color_discrete_sequence=[
            HOME_MINT,
            HOME_CYAN,
            HOME_BLUE_SOFT,
            HOME_BLUE,
            HOME_PURPLE,
        ],
    )
    fig.update_layout(
        template="plotly_white",
        font=dict(color=HOME_NAVY),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return fig