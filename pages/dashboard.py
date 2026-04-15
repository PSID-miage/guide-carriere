from __future__ import annotations

import dash
from dash import html, dcc
from dash.dependencies import Input, Output

# Enregistrement de la page
dash.register_page(__name__, path="/dashboard")

# Import des fonctions du module axe2
from components.axe2 import (
    load_liens,
    load_competences,
    load_metiers,
    load_cr_gd_dp_mapping,
    plot_top_competences,
    plot_category_distribution,
    plot_subcategory_distribution,
    plot_ratio_transverse,
    compute_domain_skill_summary,
    plot_domain_skill_summary,
    prepare_domain_job_skill_breakdown,
    plot_job_skill_breakdown,
)

# Chargement des données
liens = load_liens()
competences = load_competences()
metiers = load_metiers()
domain_df = load_cr_gd_dp_mapping()

# Graphiques globaux
top_comp_df, fig_top_comp = plot_top_competences(liens, competences, top_n=15)
cat_dist_df, fig_cat_dist = plot_category_distribution(liens, competences)
sub_dist_df, fig_sub_dist = plot_subcategory_distribution(competences)
ratio_df, fig_ratio_trans = plot_ratio_transverse(liens, competences, metiers, top_n=10)

# Domaines : résumé et figure
domain_summary_df = compute_domain_skill_summary(liens, domain_df)
domain_summary_df, fig_domain_summary = plot_domain_skill_summary(domain_summary_df)

# Préparation de la table domaine métier
domain_job_breakdown = prepare_domain_job_skill_breakdown(liens, competences, metiers, domain_df)

# Liste des domaines pour le dropdown
domain_options = [
    {"label": dom, "value": dom} for dom in sorted(domain_job_breakdown["libelle_grand_domaine"].unique())
]

# Layout du dashboard
layout = html.Div(
    style={"padding": "30px"},
    children=[
        html.H1(" Axe 2 : Analyse des compétences"),
        html.P(
            "Explorez les compétences qui structurent le marché des métiers. "
            "Filtrez par domaine et par métier pour découvrir la répartition détaillée des compétences par type."
        ),

        # 1. Top compétences
        html.H2("1️⃣ Compétences transversales"),
        html.P("Compétences apparaissant dans le plus de métiers."),
        dcc.Graph(figure=fig_top_comp),

        # 2. Répartition des catégories
        html.H2("2️⃣ Répartition des catégories"),
        html.P("Part des savoir-faire et des savoir-être en nombre d’occurrences."),
        dcc.Graph(figure=fig_cat_dist),

        # 3. Répartition des sous-catégories
        html.H2("3️⃣ Répartition des sous-catégories"),
        html.P("Typologie des compétences (Technique, Expert, Transverse)."),
        dcc.Graph(figure=fig_sub_dist),

        # 4. Métiers favorisant les compétences transversales
        html.H2("4️⃣ Métiers valorisant les compétences transversales"),
        html.P("Classement des métiers selon la part de compétences de sous-catégorie Transverse."),
        dcc.Graph(figure=fig_ratio_trans),

        # 5. Domaine : moyenne de compétences par métier
        html.H2("5️⃣ Compétences moyennes par domaine"),
        html.P("Comparaison des domaines selon le nombre moyen de compétences par métier."),
        dcc.Graph(figure=fig_domain_summary),

        # 6. Filtres par domaine et métier
        html.H2("6️⃣ Explorer par domaine et métier"),
        html.Div([
            html.Div([
                html.Label("Choisissez un domaine :"),
                dcc.Dropdown(
                    id="domain-dropdown",
                    options=domain_options,
                    value=domain_options[0]["value"],
                    placeholder="Sélectionnez un domaine",
                ),
            ], style={"width": "48%", "display": "inline-block"}),

            html.Div([
                html.Label("Choisissez un métier :"),
                dcc.Dropdown(
                    id="job-dropdown",
                    options=[],  # rempli dynamiquement
                    placeholder="Sélectionnez un métier",
                ),
            ], style={"width": "48%", "display": "inline-block", "marginLeft": "4%"}),
        ]),

        html.Br(),

        # 7. Graphique dynamique et KPI
        dcc.Graph(id="job-breakdown"),
        html.Div(
            id="job-kpi",
            style={"marginTop": "10px", "fontWeight": "bold", "fontSize": "18px"},
        ),
    ]
)
@dash.callback(
    Output("job-dropdown", "options"),
    Output("job-dropdown", "value"),
    Input("domain-dropdown", "value"),
)
def update_job_dropdown(selected_domain: str):
    """Met à jour les métiers disponibles lorsque l'utilisateur change de domaine."""
    jobs_in_domain = domain_job_breakdown[domain_job_breakdown["libelle_grand_domaine"] == selected_domain]
    options = [
        {"label": row["libelle_rome"], "value": row["code_rome"]}
        for _, row in jobs_in_domain.sort_values("libelle_rome").iterrows()
    ]
    # Sélectionner le premier métier par défaut
    value = options[0]["value"] if options else None
    return options, value

# Callback : mise à jour du graphique et du KPI pour le métier sélectionné
@dash.callback(
    Output("job-breakdown", "figure"),
    Output("job-kpi", "children"),
    Input("job-dropdown", "value"),
)
def update_job_breakdown(selected_job_code: str):
    """Affiche la répartition des compétences par type pour le métier sélectionné."""
    # Génère le graphique
    fig = plot_job_skill_breakdown(domain_job_breakdown, selected_job_code)
    # Récupère la ligne du DataFrame pour calculer le total
    job_data = domain_job_breakdown[domain_job_breakdown["code_rome"] == selected_job_code]
    if job_data.empty:
        return fig, "Aucun métier sélectionné."
    row = job_data.iloc[0]
    # Somme des colonnes de compétences
    cols = [c for c in row.index if c not in ["libelle_grand_domaine", "code_rome", "libelle_rome"]]
    total_competences = int(sum([row[c] for c in cols]))
    kpi_text = f"Métier : {row['libelle_rome']} — Total de compétences : {total_competences}"
    return fig, kpi_text