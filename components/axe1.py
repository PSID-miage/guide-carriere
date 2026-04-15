import pandas as pd


def load_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, sep=",")
    df.columns = df.columns.str.replace('"', '').str.strip()
    return df


def is_active(series: pd.Series) -> pd.Series:
    return series.notna() & (series.astype(str).str.strip() != "")


def build_caracteristiques_metiers(
    df_structure: pd.DataFrame,
    df_rome: pd.DataFrame
) -> pd.DataFrame:
    df = df_structure.merge(
        df_rome[
            [
                "code_rome",
                "transition_num",
                "transition_eco",
                "transition_demo",
                "emploi_cadre",
                "emploi_reglemente",
            ]
        ],
        on="code_rome",
        how="left"
    ).drop_duplicates(subset=["code_rome"])

    blocs = []

    mapping = {
        "Transition numérique": "transition_num",
        "Transition écologique": "transition_eco",
        "Transition démographique": "transition_demo",
        "Emploi cadre": "emploi_cadre",
        "Emploi réglementé": "emploi_reglemente",
    }

    for label, col in mapping.items():
        temp = df[is_active(df[col])].copy()
        temp["caracteristique"] = label
        blocs.append(
            temp[
                [
                    "caracteristique",
                    "code_rome",
                    "libelle_rome",
                    "libelle_domaine_professionel",
                    "libelle_grand_domaine",
                ]
            ]
        )

    return pd.concat(blocs, ignore_index=True)


def prepare_axe1_data(data_path: str = "data/") -> dict:
    df_structure = load_csv(data_path + "unix_cr_gd_dp_v460_utf8.csv")
    df_appellations = load_csv(data_path + "unix_referentiel_appellation_v460_utf8.csv")
    df_rome = load_csv(data_path + "unix_referentiel_code_rome_v460_utf8.csv")

    df_structure = df_structure.drop_duplicates()
    df_appellations = df_appellations.drop_duplicates()
    df_rome = df_rome.drop_duplicates()

    # KPI
    kpis = {
        "nb_metiers": df_structure["code_rome"].nunique(),
        "nb_appellations": df_appellations["code_ogr"].nunique(),
        "nb_grands_domaines": df_structure["code_grand_domaine"].nunique(),
        "nb_domaines_professionnels": df_structure["code_domaine_professionel"].nunique()
    }

    # Graphique 1
    metiers_par_grand_domaine = (
        df_structure.groupby("libelle_grand_domaine")["code_rome"]
        .nunique()
        .reset_index(name="nb_metiers")
        .sort_values("nb_metiers", ascending=True)
    )

    # Graphique 2
    appellations_par_metier = (
        df_appellations.groupby("code_rome")["code_ogr"]
        .nunique()
        .reset_index(name="nb_appellations")
    )

    df_metiers_appellations = df_structure.merge(
        appellations_par_metier,
        on="code_rome",
        how="left"
    )

    df_metiers_appellations["nb_appellations"] = df_metiers_appellations["nb_appellations"].fillna(0)

    comparaison_grands_domaines = (
        df_metiers_appellations
        .groupby("libelle_grand_domaine")
        .agg(
            nb_metiers=("code_rome", "nunique"),
            nb_appellations=("nb_appellations", "sum")
        )
        .reset_index()
        .sort_values("nb_appellations", ascending=True)
    )

    # Graphique 3
    top10_domaines_appellations = (
        df_metiers_appellations
        .groupby(["libelle_grand_domaine", "libelle_domaine_professionel"])
        .agg(
            nb_metiers=("code_rome", "nunique"),
            nb_appellations=("nb_appellations", "sum")
        )
        .reset_index()
        .sort_values("nb_appellations", ascending=False)
        .head(10)
    )

    # Tags / donuts
    tags = {
        "Transition numérique": df_rome[is_active(df_rome["transition_num"])]["code_rome"].nunique(),
        "Transition écologique": df_rome[is_active(df_rome["transition_eco"])]["code_rome"].nunique(),
        "Transition démographique": df_rome[is_active(df_rome["transition_demo"])]["code_rome"].nunique(),
        "Emploi cadre": df_rome[is_active(df_rome["emploi_cadre"])]["code_rome"].nunique(),
        "Emploi réglementé": df_rome[is_active(df_rome["emploi_reglemente"])]["code_rome"].nunique(),
    }

    tags_metiers = pd.DataFrame({
        "caracteristique": list(tags.keys()),
        "nb_metiers": list(tags.values())
    })

    # Table interactive
    caracteristiques_metiers = build_caracteristiques_metiers(df_structure, df_rome)

    return {
        "kpis": kpis,
        "metiers_par_grand_domaine": metiers_par_grand_domaine,
        "comparaison_grands_domaines": comparaison_grands_domaines,
        "top10_domaines_appellations": top10_domaines_appellations,
        "tags_metiers": tags_metiers,
        "caracteristiques_metiers": caracteristiques_metiers
    }