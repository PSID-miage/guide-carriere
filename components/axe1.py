import pandas as pd


def load_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, sep=",")
    df.columns = df.columns.str.replace('"', '').str.strip()
    return df


def prepare_axe1_data(data_path: str = "data/") -> dict:
    df_structure = load_csv(data_path + "unix_cr_gd_dp_v460_utf8.csv")
    df_appellations = load_csv(data_path + "unix_referentiel_appellation_v460_utf8.csv")
    df_rome = load_csv(data_path + "unix_referentiel_code_rome_v460_utf8.csv")

    # Nettoyage minimal
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

    # Métiers par grand domaine
    metiers_par_grand_domaine = (
        df_structure.groupby("libelle_grand_domaine")["code_rome"]
        .nunique()
        .reset_index(name="nb_metiers")
        .sort_values("nb_metiers", ascending=True)
    )

    # Appellations par métier puis rattachement aux domaines
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

    df_metiers_appellations["nb_appellations"] = (
        df_metiers_appellations["nb_appellations"].fillna(0)
    )

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
    comparaison_grands_domaines["appellations_par_metier"] = (
        comparaison_grands_domaines["nb_appellations"] / comparaison_grands_domaines["nb_metiers"]
    ).round(1)

    # Top 10 domaines professionnels par appellations
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

    # Tags métier
    tags = {
        "Transition numérique": df_rome["transition_num"].notna().sum(),
        "Transition écologique": df_rome["transition_eco"].notna().sum(),
        "Transition démographique": df_rome["transition_demo"].notna().sum(),
        "Emploi cadre": df_rome["emploi_cadre"].notna().sum(),
        "Emploi réglementé": df_rome["emploi_reglemente"].notna().sum(),
    }

    tags_metiers = pd.DataFrame({
        "caracteristique": list(tags.keys()),
        "nb_metiers": list(tags.values())
    }).sort_values("nb_metiers", ascending=True)

    return {
        "kpis": kpis,
        "metiers_par_grand_domaine": metiers_par_grand_domaine,
        "comparaison_grands_domaines": comparaison_grands_domaines,
        "top10_domaines_appellations": top10_domaines_appellations,
        "tags_metiers": tags_metiers
    }