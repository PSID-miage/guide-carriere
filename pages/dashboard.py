
# pages/dashboard.py

import json
import dash
from dash import html, dcc, dash_table, Input, Output, ALL, callback, ctx, callback_context
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import networkx as nx
import dash_bootstrap_components as dbc

from components.axe1 import prepare_axe1_data
from components.axe2 import (
    load_liens, load_competences, load_metiers, load_cr_gd_dp_mapping,
    plot_top_competences, plot_category_distribution,
    plot_subcategory_distribution, plot_ratio_transverse,
    compute_domain_skill_summary, plot_domain_skill_summary,
    prepare_domain_job_skill_breakdown, plot_job_skill_breakdown,
)
from components.axe3 import render_axe3
from components.axe4 import render_axe4

dash.register_page(__name__, path="/dashboard")

# ════════════════════════════════════════════════════════════════════
# STYLES
# ════════════════════════════════════════════════════════════════════

_CARD = {
    "backgroundColor": "white",
    "padding": "25px",
    "borderRadius": "12px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.05)",
    "marginBottom": "30px"
}

_NOTE = {
    "backgroundColor": "#f8f9fb",
    "padding": "15px",
    "borderRadius": "10px",
    "marginTop": "10px"
}

# ════════════════════════════════════════════════════════════════════
# PALETTE COULEURS — ALIGNÉE AVEC LA HOME
# ════════════════════════════════════════════════════════════════════

HOME_CYAN = "#22D3EE"
HOME_BLUE = "#38BDF8"
HOME_BLUE_SOFT = "#60A5FA"
HOME_PURPLE = "#8B5CF6"
HOME_PURPLE_DARK = "#7C3AED"
HOME_MINT = "#99F6E4"
HOME_NAVY = "#0F172A"

# ════════════════════════════════════════════════════════════════════
# AXE 1 — DONNÉES & FIGURES
# ════════════════════════════════════════════════════════════════════

axe1 = prepare_axe1_data("data/")
kpis = axe1["kpis"]


def make_transitions_figure(selected=None):
    df = axe1["tags_metiers"][
        axe1["tags_metiers"]["caracteristique"].isin([
            "Transition numérique", "Transition écologique", "Transition démographique"
        ])
    ].copy()

    base_colors = {
        "Transition numérique": HOME_BLUE_SOFT,
        "Transition écologique": HOME_MINT,
        "Transition démographique": "#C4B5FD",
    }
    dark_colors = {
        "Transition numérique": HOME_BLUE,
        "Transition écologique": HOME_CYAN,
        "Transition démographique": HOME_PURPLE,
    }

    colors = [dark_colors[c] if c == selected else base_colors[c] for c in df["caracteristique"]]
    pulled = [0.08 if c == selected else 0 for c in df["caracteristique"]]

    fig = px.pie(
        df,
        names="caracteristique",
        values="nb_metiers",
        hole=0.45,
        title="Métiers liés aux transitions"
    )
    fig.update_traces(
        marker=dict(colors=colors),
        pull=pulled,
        textinfo="percent",
        textfont=dict(color=HOME_NAVY)
    )
    fig.update_layout(
        template="plotly_white",
        height=420,
        title_x=0.02,
        margin=dict(l=30, r=30, t=70, b=30),
        legend_title_text="",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=HOME_NAVY)
    )
    return fig


def make_autres_figure(selected=None):
    df = axe1["tags_metiers"][
        axe1["tags_metiers"]["caracteristique"].isin(["Emploi cadre", "Emploi réglementé"])
    ].copy()

    base_colors = {
        "Emploi cadre": "#C4B5FD",
        "Emploi réglementé": HOME_MINT,
    }
    dark_colors = {
        "Emploi cadre": HOME_PURPLE,
        "Emploi réglementé": HOME_CYAN,
    }

    colors = [dark_colors[c] if c == selected else base_colors[c] for c in df["caracteristique"]]
    pulled = [0.08 if c == selected else 0 for c in df["caracteristique"]]

    fig = px.pie(
        df,
        names="caracteristique",
        values="nb_metiers",
        hole=0.45,
        title="Autres caractéristiques métiers"
    )
    fig.update_traces(
        marker=dict(colors=colors),
        pull=pulled,
        textinfo="percent",
        textfont=dict(color=HOME_NAVY)
    )
    fig.update_layout(
        template="plotly_white",
        height=420,
        title_x=0.02,
        margin=dict(l=30, r=30, t=70, b=30),
        legend_title_text="",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=HOME_NAVY)
    )
    return fig


fig_metiers_grands_domaines = px.bar(
    axe1["metiers_par_grand_domaine"],
    x="nb_metiers",
    y="libelle_grand_domaine",
    orientation="h",
    text="nb_metiers",
    title="Répartition des métiers ROME par grand domaine",
    color="nb_metiers",
    color_continuous_scale=[
        [0.0, HOME_MINT],
        [0.35, HOME_CYAN],
        [0.7, HOME_BLUE],
        [1.0, HOME_PURPLE],
    ],
    labels={"nb_metiers": "Nombre de métiers", "libelle_grand_domaine": "Grand domaine"}
)
fig_metiers_grands_domaines.update_traces(textposition="outside", marker_line_width=0)
fig_metiers_grands_domaines.update_layout(
    height=550,
    template="plotly_white",
    title_x=0.02,
    xaxis_title="Nombre de métiers ROME",
    yaxis_title="",
    margin=dict(l=220, r=60, t=70, b=50),
    coloraxis_showscale=False,
    bargap=0.25,
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(color=HOME_NAVY)
)

fig_comparaison = px.bar_polar(
    axe1["comparaison_grands_domaines"],
    r="nb_appellations",
    theta="libelle_grand_domaine",
    color="nb_appellations",
    title="Volume d'appellations par grand domaine",
    labels={"nb_appellations": "Nombre d'appellations", "libelle_grand_domaine": "Grand domaine"},
    color_continuous_scale=[
        [0.0, HOME_MINT],
        [0.25, HOME_CYAN],
        [0.5, HOME_BLUE_SOFT],
        [0.75, HOME_BLUE],
        [1.0, HOME_PURPLE],
    ],
    custom_data=["libelle_grand_domaine", "nb_appellations", "nb_metiers"]
)
fig_comparaison.update_traces(
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "Nombre d'appellations : %{customdata[1]}<br>"
        "Nombre de métiers ROME : %{customdata[2]}<extra></extra>"
    )
)
fig_comparaison.update_layout(
    template="plotly_white",
    height=600,
    title_x=0.02,
    coloraxis_showscale=False,
    margin=dict(l=40, r=40, t=70, b=40),
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(color=HOME_NAVY)
)

fig_top10_appellations = px.bar(
    axe1["top10_domaines_appellations"],
    x="nb_appellations",
    y="libelle_domaine_professionel",
    orientation="h",
    text="nb_appellations",
    hover_data=["libelle_grand_domaine", "nb_metiers"],
    title="Top 10 des domaines professionnels par nombre d'appellations",
    labels={
        "nb_appellations": "Nombre d'appellations",
        "libelle_domaine_professionel": "Domaine professionnel"
    }
)
fig_top10_appellations.update_traces(marker_color=HOME_BLUE, textposition="outside")
fig_top10_appellations.update_layout(
    template="plotly_white",
    height=550,
    title_x=0.02,
    yaxis={"categoryorder": "total ascending"},
    xaxis_title="Nombre d'appellations",
    yaxis_title="",
    margin=dict(l=260, r=80, t=70, b=50),
    bargap=0.25,
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(color=HOME_NAVY)
)

# ════════════════════════════════════════════════════════════════════
# AXE 2 — DONNÉES & FIGURES
# ════════════════════════════════════════════════════════════════════

liens_axe2 = load_liens()
comp_axe2 = load_competences()
metiers_axe2 = load_metiers()
domain_df = load_cr_gd_dp_mapping()

_, fig_top_comp = plot_top_competences(liens_axe2, comp_axe2, top_n=15)
_, fig_cat_dist = plot_category_distribution(liens_axe2, comp_axe2)
_, fig_sub_dist = plot_subcategory_distribution(comp_axe2)
_, fig_ratio_trans = plot_ratio_transverse(liens_axe2, comp_axe2, metiers_axe2, top_n=10)
domain_summary_df = compute_domain_skill_summary(liens_axe2, domain_df)
domain_summary_df, fig_domain_summary = plot_domain_skill_summary(domain_summary_df)
domain_job_breakdown = prepare_domain_job_skill_breakdown(liens_axe2, comp_axe2, metiers_axe2, domain_df)

domain_options = [
    {"label": d, "value": d}
    for d in sorted(domain_job_breakdown["libelle_grand_domaine"].dropna().unique())
]

# ════════════════════════════════════════════════════════════════════
# AXES 3/4 — DONNÉES
# ════════════════════════════════════════════════════════════════════

df_mobi = pd.read_csv("data/unix_rubrique_mobilite_v460_utf8.csv")
df_rome = pd.read_csv("data/unix_referentiel_code_rome_v460_utf8.csv")
df_gd = pd.read_csv("data/unix_grand_domaine_v460_utf8.csv")
df_liens = pd.read_csv("data/unix_liens_rome_referentiels_v460_utf8.csv")
df_comp = pd.read_csv("data/unix_referentiel_competence_v460_utf8.csv", on_bad_lines="skip")
df_riasec = pd.read_csv("data/unix_referentiel_code_rome_riasec_v460_utf8.csv")

for _df in [df_mobi, df_rome, df_gd, df_liens, df_comp, df_riasec]:
    for col in _df.columns:
        if "code" in col.lower() or "ogr" in col.lower():
            _df[col] = _df[col].astype(str).str.strip()

# ════════════════════════════════════════════════════════════════════
# SECTIONS DE LAYOUT SÉPARÉES
# ════════════════════════════════════════════════════════════════════

def build_axe1_layout():
    return html.Div([
        dcc.Store(id="selected-caracteristique", data="Transition écologique"),

        html.Div([
            html.Div(style={
                'width': '60px',
                'height': '4px',
                'backgroundColor': '#2980b9',
                'marginBottom': '20px',
                'borderRadius': '2px'
            }),
            html.H2(
                "AXE 1 : PANORAMA DE L'EMPLOI",
                style={
                    'fontWeight': '800',
                    'color': "#2c3e50",
                    'letterSpacing': '0.5px',
                    'textTransform': 'uppercase'
                }
            ),
            html.P(
                f"Vue générale du référentiel ROME : {kpis['nb_metiers']} métiers, "
                f"{kpis['nb_appellations']} appellations professionnelles, "
                f"{kpis['nb_grands_domaines']} grands domaines.",
                style={'fontSize': '1.1rem', 'color': "#7f8c8d", 'maxWidth': '800px'}
            )
        ], className="mb-5 mt-5"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Strong("RÉPARTITION DES MÉTIERS"),
                        style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='g1-metiers-domaine', figure=fig_metiers_grands_domaines),
                            type="dot",
                            color="#2980b9"
                        )
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=8),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("KPIs", style={"fontWeight": "700", "marginBottom": "20px"}),
                        html.Div([
                            html.Div(
                                f"{k}: {v}",
                                style={
                                    "padding": "10px 0",
                                    "borderBottom": "1px solid #ecf0f1",
                                    "fontSize": "0.95rem"
                                }
                            )
                            for k, v in kpis.items()
                        ], style={"color": "#2c3e50"})
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=4)
        ], className="mb-4"),

       

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Strong("VOLUME D'APPELLATIONS PAR GRAND DOMAINE"),
                        style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='g4-polar', figure=fig_comparaison),
                            type="dot",
                            color="#2980b9"
                        )
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Strong("TOP 10 DOMAINES"),
                        style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='g5-top10', figure=fig_top10_appellations),
                            type="dot",
                            color="#2980b9"
                        )
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=6)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Strong("MÉTIERS LIÉS AUX TRANSITIONS"),
                        style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='g2-transitions', figure=make_transitions_figure("Transition écologique")),
                            type="dot",
                            color="#2980b9"
                        )
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Strong("EMPLOIS CADRE & RÉGLEMENTÉS"),
                        style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='g3-autres', figure=make_autres_figure()),
                            type="dot",
                            color="#2980b9"
                        )
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=6)
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardHeader(
                html.Strong("LISTE DES MÉTIERS PAR CARACTÉRISTIQUE"),
                style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
            ),
            dbc.CardBody([
                dcc.RadioItems(
                    id="filter-caracteristique",
                    options=[
                        {"label": "Transition numérique", "value": "Transition numérique"},
                        {"label": "Transition écologique", "value": "Transition écologique"},
                        {"label": "Transition démographique", "value": "Transition démographique"},
                        {"label": "Emploi cadre", "value": "Emploi cadre"},
                        {"label": "Emploi réglementé", "value": "Emploi réglementé"},
                    ],
                    value="Transition écologique",
                    inline=True,
                    style={"marginBottom": "20px"},
                    inputStyle={"marginRight": "6px", "marginLeft": "12px"},
                ),
                dash_table.DataTable(
                    id="table-metiers-caracteristique",
                    columns=[
                        {"name": "Code ROME", "id": "code_rome"},
                        {"name": "Métier", "id": "libelle_rome"},
                        {"name": "Grand domaine", "id": "libelle_grand_domaine"},
                        {"name": "Domaine professionnel", "id": "libelle_domaine_professionel"},
                    ],
                    data=[],
                    page_size=10,
                    sort_action="native",
                    filter_action="native",
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "textAlign": "left",
                        "padding": "10px",
                        "fontFamily": "Arial",
                        "fontSize": "14px",
                        "whiteSpace": "normal",
                        "height": "auto",
                    },
                    style_header={"backgroundColor": "#eaf2f8", "fontWeight": "bold"},
                )
            ])
        ], className="border-0 shadow-sm mb-5", style={"borderRadius": "8px", "paddingBottom": "20px"})
    ], style={"padding": "40px 60px", "backgroundColor": "white"})


def build_axe2_layout():
    return html.Div([
        html.Div([
            html.Div(style={
                'width': '60px',
                'height': '4px',
                'backgroundColor': '#27ae60',
                'marginBottom': '20px',
                'borderRadius': '2px'
            }),
            html.H2(
                "AXE 2 : COMPÉTENCES ET SAVOIRS",
                style={
                    'fontWeight': '800',
                    'color': "#2c3e50",
                    'letterSpacing': '0.5px',
                    'textTransform': 'uppercase'
                }
            ),
            html.P(
                "Analyse des compétences par métier, transversalité et spécialisation.",
                style={'fontSize': '1.1rem', 'color': "#7f8c8d", 'maxWidth': '800px'}
            )
        ], className="mb-5 mt-5"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Strong("TOP 15 COMPÉTENCES TRANSVERSALES"),
                        style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='g6-top-comp', figure=fig_top_comp),
                            type="dot",
                            color="#27ae60"
                        )
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Strong("RÉPARTITION DES CATÉGORIES"),
                        style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='g6b-cat', figure=fig_cat_dist),
                            type="dot",
                            color="#27ae60"
                        )
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=6)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Strong("SOUS-CATÉGORIES"),
                        style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='g6c-subcat', figure=fig_sub_dist),
                            type="dot",
                            color="#27ae60"
                        )
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Strong("MÉTIERS VALORISANT LA TRANSVERSALITÉ"),
                        style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='g6d-ratio', figure=fig_ratio_trans),
                            type="dot",
                            color="#27ae60"
                        )
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=6)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Strong("MOYENNE DE COMPÉTENCES PAR DOMAINE"),
                        style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
                    ),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(id='g6e-domain', figure=fig_domain_summary),
                            type="dot",
                            color="#27ae60"
                        )
                    ])
                ], className="border-0 shadow-sm", style={"borderRadius": "8px"})
            ], lg=12)
        ], className="mb-4"),

        dbc.Card([
            dbc.CardHeader(
                html.Strong("EXPLORER PAR DOMAINE ET MÉTIER"),
                style={"backgroundColor": "white", "borderBottom": "1px solid #f1f2f6"}
            ),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Choisissez un domaine :", style={"fontWeight": "600"}),
                        dcc.Dropdown(
                            id="domain-dropdown",
                            options=domain_options,
                            value=domain_options[0]["value"] if domain_options else None,
                            placeholder="Sélectionnez un domaine",
                        ),
                    ], md=6),
                    dbc.Col([
                        html.Label("Choisissez un métier :", style={"fontWeight": "600"}),
                        dcc.Dropdown(
                            id="job-dropdown",
                            options=[],
                            placeholder="Sélectionnez un métier",
                        ),
                    ], md=6),
                ]),
                html.Br(),
                dcc.Graph(id="job-breakdown"),
                html.Div(
                    id="job-kpi",
                    style={"marginTop": "10px", "fontWeight": "bold", "fontSize": "18px"},
                ),
            ])
        ], className="border-0 shadow-sm mb-5", style={"borderRadius": "8px", "paddingBottom": "20px"})
    ], style={"padding": "40px 60px", "backgroundColor": "white"})


def build_axe34_layout():
    return html.Div([
        dcc.Store(id="active-metier-store", data=None),
        dcc.Store(id="filtered-metiers-store", data=[]),
        render_axe3(df_gd),
        render_axe4(),
    ], style={"padding": "40px 60px", "backgroundColor": "white"})


# ════════════════════════════════════════════════════════════════════
# LAYOUT GLOBAL
# ════════════════════════════════════════════════════════════════════

layout = html.Div([
    dcc.Tabs(
        id="tabs-axes",
        value="axe1",
        parent_className="dashboard-tabs-wrapper",
        className="dashboard-tabs-container",
        children=[
            dcc.Tab(
                label="Axe 1 - Panorama",
                value="axe1",
                className="dashboard-tab",
                selected_className="dashboard-tab--selected",
            ),
            dcc.Tab(
                label="Axe 2 - Compétences",
                value="axe2",
                className="dashboard-tab",
                selected_className="dashboard-tab--selected",
            ),
            dcc.Tab(
                label="Axes 3/4 - Mobilités",
                value="axe3",
                className="dashboard-tab",
                selected_className="dashboard-tab--selected",
            ),
        ],
    ),

    html.Div(id="content-axe1", children=build_axe1_layout()),
    html.Div(id="content-axe2", style={"display": "none"}, children=build_axe2_layout()),
    html.Div(id="content-axe3", style={"display": "none"}, children=build_axe34_layout()),
], className="dashboard-page", style={
    "fontFamily": "Segoe UI, -apple-system, sans-serif",
    "backgroundColor": "#f8f9fb"
})

# ════════════════════════════════════════════════════════════════════
# CALLBACKS — ONGLETS
# ════════════════════════════════════════════════════════════════════

@callback(
    Output("content-axe1", "style"),
    Output("content-axe2", "style"),
    Output("content-axe3", "style"),
    Input("tabs-axes", "value"),
)
def toggle_tabs(tab):
    show = {"display": "block"}
    hide = {"display": "none"}

    if tab == "axe1":
        return show, hide, hide
    elif tab == "axe2":
        return hide, show, hide
    else:
        return hide, hide, show

# ════════════════════════════════════════════════════════════════════
# CALLBACKS — AXE 1
# ════════════════════════════════════════════════════════════════════

@callback(
    Output("selected-caracteristique", "data"),
    Input("g2-transitions", "clickData"),
    Input("g3-autres", "clickData"),
    Input("filter-caracteristique", "value"),
)
def update_selected_caracteristique(click_trans, click_autres, filter_val):
    triggered = ctx.triggered_id

    if triggered == "g2-transitions" and click_trans:
        return click_trans["points"][0]["label"]

    if triggered == "g3-autres" and click_autres:
        return click_autres["points"][0]["label"]

    return filter_val


@callback(
    Output("g2-transitions", "figure"),
    Output("g3-autres", "figure"),
    Output("table-metiers-caracteristique", "data"),
    Input("selected-caracteristique", "data"),
)
def update_figures_and_table(selected):
    df = axe1["caracteristiques_metiers"].copy()
    df_f = (
        df[df["caracteristique"] == selected]
        .drop_duplicates(subset=["code_rome"])
        .sort_values(["libelle_grand_domaine", "libelle_domaine_professionel", "libelle_rome"])
    )

    return (
        make_transitions_figure(selected),
        make_autres_figure(selected),
        df_f.to_dict("records"),
    )

# ════════════════════════════════════════════════════════════════════
# CALLBACKS — AXE 2
# ════════════════════════════════════════════════════════════════════

@callback(
    Output("job-dropdown", "options"),
    Output("job-dropdown", "value"),
    Input("domain-dropdown", "value"),
)
def update_job_dropdown(selected_domain):
    if not selected_domain:
        return [], None

    jobs = domain_job_breakdown[
        domain_job_breakdown["libelle_grand_domaine"] == selected_domain
    ]

    opts = [
        {"label": r["libelle_rome"], "value": r["code_rome"]}
        for _, r in jobs.sort_values("libelle_rome").iterrows()
    ]

    return opts, (opts[0]["value"] if opts else None)


@callback(
    Output("job-breakdown", "figure"),
    Output("job-kpi", "children"),
    Input("job-dropdown", "value"),
)
def update_job_breakdown(code):
    if not code:
        return go.Figure(), "Aucun métier sélectionné."

    fig = plot_job_skill_breakdown(domain_job_breakdown, code)
    row_df = domain_job_breakdown[domain_job_breakdown["code_rome"] == code]

    if row_df.empty:
        return fig, "Aucun métier sélectionné."

    row = row_df.iloc[0]
    cols = [c for c in row.index if c not in ["libelle_grand_domaine", "code_rome", "libelle_rome"]]
    total = int(sum(row[c] for c in cols))

    return fig, f"Métier : {row['libelle_rome']} — {total} compétences"

# ════════════════════════════════════════════════════════════════════
# CALLBACKS — AXES 3/4
# LOGIQUE CONSERVÉE DU PREMIER CODE
# ════════════════════════════════════════════════════════════════════

@dash.callback(
    [Output('metier-zoom-filter', 'options'),
     Output('filtered-metiers-store', 'data')],
    [Input('domaine-filter', 'value')],
    prevent_initial_call=False,
)
def update_metier_options(selected_domaine):
    if not selected_domaine:
        return [], []

    df_filtered = df_rome[df_rome['code_rome'].str.startswith(selected_domaine)].sort_values('code_rome')

    options = [
        {'label': f"{row['code_rome']} - {row['libelle_rome']}", 'value': row['code_rome']}
        for _, row in df_filtered.iterrows()
    ]

    metiers_data = df_filtered[['code_rome', 'libelle_rome']].to_dict('records')

    return options, metiers_data


@dash.callback(
    Output('active-metier-store', 'data'),
    [Input({'type': 'btn-voir-fiche', 'index': ALL}, 'n_clicks'),
     Input('g7-net-graph', 'clickData'),
     Input('metier-zoom-filter', 'value')],
    prevent_initial_call=True,
)
def handle_navigation(btn_clicks, clickData, dropdown_val):
    ctx2 = callback_context
    if not ctx2.triggered:
        return dash.no_update

    trig_id = ctx2.triggered[0]['prop_id']

    if 'btn-voir-fiche' in trig_id:
        return json.loads(trig_id.split('.')[0])['index']

    if 'g7-net-graph' in trig_id and clickData:
        return clickData['points'][0]['text'].split(':')[1].split('-')[0].strip()

    return dropdown_val


@dash.callback(
    [Output('g7-net-graph', 'figure'),
     Output('table-legende', 'data'),
     Output('g8-pivots-graph', 'figure'),
     Output('g10-potentiel-global', 'figure'),
     Output('section-axe4', 'style'),
     Output('fiche-titre-metier', 'children'),
     Output('metier-tags', 'children'),
     Output('fiche-competences', 'children'),
     Output('g12-radar-riasec', 'figure'),
     Output('container-metiers-similaires', 'children')],
    [Input('domaine-filter', 'value'),
     Input('active-metier-store', 'data')],
)
def update_all_analytics(selected_domaine, active_metier):
    if not selected_domaine:
        empty_fig = go.Figure()
        return empty_fig, [], empty_fig, empty_fig, {'display': 'none'}, "", [], [], empty_fig, []

    df_f = df_mobi[df_mobi['code_rome'].str.startswith(selected_domaine)].copy()

    if df_f.empty:
        empty_fig = go.Figure()
        return empty_fig, [], empty_fig, empty_fig, {'display': 'none'}, "", [], [], empty_fig, []

    G = nx.from_pandas_edgelist(
        df_f,
        source='code_rome',
        target='code_rome_cible',
        create_using=nx.DiGraph()
    )

    d_dict = dict(G.degree)
    pos = nx.spring_layout(G, k=0.4, iterations=30, seed=42)

    fig7 = go.Figure()
    edge_x, edge_y, active_edge_x, active_edge_y = [], [], [], []

    for edge in G.edges():
        if edge[0] in pos and edge[1] in pos:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]

            if active_metier and (str(edge[0]) == str(active_metier) or str(edge[1]) == str(active_metier)):
                active_edge_x.extend([x0, x1, None])
                active_edge_y.extend([y0, y1, None])
            else:
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

    fig7.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#dfe6e9'),
        hoverinfo='none',
        mode='lines'
    ))
    fig7.add_trace(go.Scatter(
        x=active_edge_x, y=active_edge_y,
        line=dict(width=2, color='#e74c3c'),
        hoverinfo='none',
        mode='lines'
    ))

    node_x, node_y, node_text, colors, sizes = [], [], [], [], []
    for n in G.nodes():
        lib = df_rome[df_rome['code_rome'] == str(n)]['libelle_rome'].values
        node_text.append(f"Métier: {n} - {lib[0] if len(lib) > 0 else ''}<br>Relations: {d_dict[n]}")
        node_x.append(pos[n][0])
        node_y.append(pos[n][1])
        colors.append('#e74c3c' if str(n) == str(active_metier) else "#42b2c1")
        sizes.append(30 if str(n) == str(active_metier) else (d_dict[n] * 2) + 10)

    fig7.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        marker=dict(size=sizes, color=colors, line=dict(color='white', width=1)),
        text=node_text,
        hoverinfo='text'
    ))

    if active_metier and active_metier in pos:
        fx, fy = pos[active_metier]
        fig7.update_xaxes(range=[fx - 0.3, fx + 0.3])
        fig7.update_yaxes(range=[fy - 0.3, fy + 0.3])

    fig7.update_layout(
        plot_bgcolor='white',
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=False,
        uirevision=selected_domaine,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    df_pivots = (
        pd.DataFrame(list(d_dict.items()), columns=['code_rome', 'relations_count'])
        .nlargest(10, 'relations_count')
        .merge(df_rome[['code_rome', 'libelle_rome']], on='code_rome', how='left')
    )
    fig8 = go.Figure(go.Bar(
        x=df_pivots['relations_count'],
        y=df_pivots['libelle_rome'],
        orientation='h',
        marker=dict(color="#42b2c1")
    ))
    fig8.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        height=400,
        yaxis=dict(autorange="reversed")
    )

    df_moyennes = (
        df_mobi.groupby(df_mobi['code_rome'].str[0]).size()
        .reset_index(name='count')
        .merge(df_gd, left_on='code_rome', right_on='code_grand_domaine')
    )
    fig10 = go.Figure(go.Bar(
        x=df_moyennes['count'],
        y=df_moyennes['libelle_grand_domaine'],
        orientation='h',
        marker=dict(color="#42b2c1")
    ))
    fig10.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        height=500
    )

    df_table_all = df_rome[df_rome['code_rome'].str.startswith(selected_domaine)].sort_values('code_rome')
    data_table = (
        df_table_all[df_table_all['code_rome'] == active_metier].to_dict('records')
        if active_metier else df_table_all.to_dict('records')
    )

    if not active_metier or active_metier == "None" or active_metier not in df_rome['code_rome'].values:
        return fig7, data_table, fig8, fig10, {'display': 'none'}, "", [], [], go.Figure(), []

    m_info = df_rome[df_rome['code_rome'] == active_metier].iloc[0]
    liens_m = df_liens[df_liens['code_rome'] == active_metier]

    tags = []
    if str(m_info.get('transition_num')) == 'O':
        tags.append(dbc.Badge("NUMÉRIQUE", color="info", className="px-3 py-2 me-2"))
    if str(m_info.get('transition_eco')) == 'O':
        tags.append(dbc.Badge("ÉCO-TRANSITION", color="success", className="px-3 py-2"))

    c_ids = liens_m[liens_m['code_compo_bloc'] == '5']['code_ogr'].unique()
    comp_labels = df_comp[df_comp['code_ogr'].isin(c_ids)]['libelle_competence'].unique()[:10]
    comp_list = [
        html.Div([
            html.Span("●", style={'color': '#42b2c1', 'marginRight': '15px', 'fontSize': '0.8rem'}),
            html.Span(c)
        ], style={'padding': '8px 0', 'borderBottom': '1px solid #f1f2f6'})
        for c in comp_labels
    ]

    scores = [2] * 6
    r_match = df_riasec[df_riasec['code_rome'] == active_metier]
    if not r_match.empty:
        maj = str(r_match.iloc[0].get('riasec_majeur', ''))
        for i, l in enumerate(['R', 'I', 'A', 'S', 'E', 'C']):
            if l == maj:
                scores[i] = 5

    fig12 = go.Figure(data=go.Scatterpolar(
        r=scores,
        theta=['Réaliste', 'Investigateur', 'Artistique', 'Social', 'Entreprenant', 'Conventionnel'],
        fill='toself',
        line=dict(color='#42b2c1', width=3)
    ))
    fig12.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5], gridcolor="#f1f2f6")),
        height=380,
        margin=dict(t=40, b=40, l=60, r=60)
    )

    targets = df_mobi[df_mobi['code_rome'] == active_metier]['code_rome_cible'].unique()[:4]
    sugg_cards = []
    for t in targets:
        t_lib = (
            df_rome[df_rome['code_rome'] == t]['libelle_rome'].values[0]
            if t in df_rome['code_rome'].values else "Inconnu"
        )
        sugg_cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Small(
                            f"ROME {t}",
                            style={
                                'color': '#42b2c1',
                                'fontWeight': '800',
                                'fontSize': '0.85rem',
                                'display': 'block',
                                'marginBottom': '10px'
                            }
                        ),
                        html.H5(
                            t_lib,
                            style={
                                'fontWeight': '800',
                                'color': '#2c3e50',
                                'fontSize': '1.25rem',
                                'lineHeight': '1.4',
                                'minHeight': '60px'
                            }
                        ),
                        html.Hr(style={'opacity': '0.1', 'margin': '20px 0'}),
                        html.Button(
                            "Voir la fiche →",
                            id={'type': 'btn-voir-fiche', 'index': t},
                            style={
                                'width': '100%',
                                'padding': '12px',
                                'borderRadius': '8px',
                                'border': 'none',
                                'backgroundColor': '#eef9fa',
                                'color': '#42b2c1',
                                'fontWeight': 'bold'
                            }
                        )
                    ], style={'padding': '25px'})
                ], className="border-0 shadow-sm h-100")
            ], lg=3, md=6)
        )

    return (
        fig7, data_table, fig8, fig10, {'display': 'block'},
        m_info['libelle_rome'], tags, comp_list, fig12, sugg_cards
    )
