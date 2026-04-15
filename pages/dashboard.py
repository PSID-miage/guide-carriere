# pages/dashboard.py — version unifiée axe1 + axe2 + axe3/4

import json
import dash
from dash import html, dcc, dash_table, Input, Output, State, ALL, callback, ctx, callback_context
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
# AXE 1 — Données & figures
# ════════════════════════════════════════════════════════════════════

axe1 = prepare_axe1_data("data/")
kpis = axe1["kpis"]

def make_transitions_figure(selected=None):
    df = axe1["tags_metiers"][
        axe1["tags_metiers"]["caracteristique"].isin([
            "Transition numérique", "Transition écologique", "Transition démographique"
        ])
    ].copy()
    base_colors  = {"Transition numérique": "#A8DADC", "Transition écologique": "#CDEAC0", "Transition démographique": "#F4C2C2"}
    dark_colors  = {"Transition numérique": "#6FAFC1", "Transition écologique": "#8FBC8F",  "Transition démographique": "#D98C8C"}
    colors  = [dark_colors[c] if c == selected else base_colors[c] for c in df["caracteristique"]]
    pulled  = [0.08 if c == selected else 0 for c in df["caracteristique"]]
    fig = px.pie(df, names="caracteristique", values="nb_metiers", hole=0.45, title="Métiers liés aux transitions")
    fig.update_traces(marker=dict(colors=colors), pull=pulled, textinfo="percent")
    fig.update_layout(template="plotly_white", height=420, title_x=0.02,
                      margin=dict(l=30, r=30, t=70, b=30), legend_title_text="")
    return fig

def make_autres_figure(selected=None):
    df = axe1["tags_metiers"][
        axe1["tags_metiers"]["caracteristique"].isin(["Emploi cadre", "Emploi réglementé"])
    ].copy()
    base_colors = {"Emploi cadre": "#CDB4DB", "Emploi réglementé": "#FFD6A5"}
    dark_colors = {"Emploi cadre": "#9F86C0", "Emploi réglementé": "#E9A96B"}
    colors = [dark_colors[c] if c == selected else base_colors[c] for c in df["caracteristique"]]
    pulled = [0.08 if c == selected else 0 for c in df["caracteristique"]]
    fig = px.pie(df, names="caracteristique", values="nb_metiers", hole=0.45, title="Autres caractéristiques métiers")
    fig.update_traces(marker=dict(colors=colors), pull=pulled, textinfo="percent")
    fig.update_layout(template="plotly_white", height=420, title_x=0.02,
                      margin=dict(l=30, r=30, t=70, b=30), legend_title_text="")
    return fig

fig_metiers_grands_domaines = px.bar(
    axe1["metiers_par_grand_domaine"], x="nb_metiers", y="libelle_grand_domaine",
    orientation="h", text="nb_metiers", title="Répartition des métiers ROME par grand domaine",
    color="nb_metiers", color_continuous_scale="Blues",
    labels={"nb_metiers": "Nombre de métiers", "libelle_grand_domaine": "Grand domaine"}
)
fig_metiers_grands_domaines.update_traces(textposition="outside", marker_line_width=0)
fig_metiers_grands_domaines.update_layout(
    height=550, template="plotly_white", title_x=0.02,
    xaxis_title="Nombre de métiers ROME", yaxis_title="",
    margin=dict(l=220, r=60, t=70, b=50), coloraxis_showscale=False, bargap=0.25
)

fig_comparaison = px.bar_polar(
    axe1["comparaison_grands_domaines"], r="nb_appellations", theta="libelle_grand_domaine",
    color="nb_appellations", title="Volume d'appellations par grand domaine",
    labels={"nb_appellations": "Nombre d'appellations", "libelle_grand_domaine": "Grand domaine"},
    color_continuous_scale=[[0.0,"#dbe9f6"],[0.25,"#b8d4ea"],[0.5,"#8bbbd9"],[0.75,"#5b9ec9"],[1.0,"#2f6fa3"]],
    custom_data=["libelle_grand_domaine", "nb_appellations", "nb_metiers"]
)
fig_comparaison.update_traces(hovertemplate=(
    "<b>%{customdata[0]}</b><br>"
    "Nombre d'appellations : %{customdata[1]}<br>"
    "Nombre de métiers ROME : %{customdata[2]}<extra></extra>"
))
fig_comparaison.update_layout(template="plotly_white", height=600, title_x=0.02,
    coloraxis_showscale=False, margin=dict(l=40, r=40, t=70, b=40))

fig_top10_appellations = px.bar(
    axe1["top10_domaines_appellations"], x="nb_appellations", y="libelle_domaine_professionel",
    orientation="h", text="nb_appellations",
    hover_data=["libelle_grand_domaine", "nb_metiers"],
    title="Top 10 des domaines professionnels par nombre d'appellations",
    labels={"nb_appellations": "Nombre d'appellations", "libelle_domaine_professionel": "Domaine professionnel"}
)
fig_top10_appellations.update_traces(marker_color="#2E86AB", textposition="outside")
fig_top10_appellations.update_layout(
    template="plotly_white", height=550, title_x=0.02,
    yaxis={"categoryorder": "total ascending"}, xaxis_title="Nombre d'appellations",
    yaxis_title="", margin=dict(l=260, r=80, t=70, b=50), bargap=0.25
)

# ════════════════════════════════════════════════════════════════════
# AXE 2 — Données & figures
# ════════════════════════════════════════════════════════════════════

liens_axe2   = load_liens()
comp_axe2    = load_competences()
metiers_axe2 = load_metiers()
domain_df    = load_cr_gd_dp_mapping()

_, fig_top_comp    = plot_top_competences(liens_axe2, comp_axe2, top_n=15)
_, fig_cat_dist    = plot_category_distribution(liens_axe2, comp_axe2)
_, fig_sub_dist    = plot_subcategory_distribution(comp_axe2)
_, fig_ratio_trans = plot_ratio_transverse(liens_axe2, comp_axe2, metiers_axe2, top_n=10)
domain_summary_df  = compute_domain_skill_summary(liens_axe2, domain_df)
domain_summary_df, fig_domain_summary = plot_domain_skill_summary(domain_summary_df)
domain_job_breakdown = prepare_domain_job_skill_breakdown(liens_axe2, comp_axe2, metiers_axe2, domain_df)
domain_options = [{"label": d, "value": d} for d in sorted(domain_job_breakdown["libelle_grand_domaine"].unique())]

# ════════════════════════════════════════════════════════════════════
# AXE 3/4 — Données
# ════════════════════════════════════════════════════════════════════

df_mobi   = pd.read_csv('data/unix_rubrique_mobilite_v460_utf8.csv')
df_rome   = pd.read_csv('data/unix_referentiel_code_rome_v460_utf8.csv')
df_gd     = pd.read_csv('data/unix_grand_domaine_v460_utf8.csv')
df_liens  = pd.read_csv('data/unix_liens_rome_referentiels_v460_utf8.csv')
df_comp   = pd.read_csv('data/unix_referentiel_competence_v460_utf8.csv', on_bad_lines='skip')
df_riasec = pd.read_csv('data/unix_referentiel_code_rome_riasec_v460_utf8.csv')

for _df in [df_mobi, df_rome, df_gd, df_liens, df_comp, df_riasec]:
    for col in _df.columns:
        if 'code' in col.lower() or 'ogr' in col.lower():
            _df[col] = _df[col].astype(str).str.strip()

# ════════════════════════════════════════════════════════════════════
# LAYOUT
# ════════════════════════════════════════════════════════════════════

_CARD = {"backgroundColor": "white", "padding": "25px", "borderRadius": "12px",
         "boxShadow": "0 2px 8px rgba(0,0,0,0.05)", "marginBottom": "30px"}
_NOTE = {"backgroundColor": "#f8f9fb", "padding": "15px", "borderRadius": "10px", "marginTop": "10px"}

layout = html.Div([

    # ── Onglets ──────────────────────────────────────────────────────
    dcc.Tabs(id="tabs-axes", value="axe1", style={"marginBottom": "30px"}, children=[
        dcc.Tab(label="Axe 1 - Cartographie", value="axe1"),
        dcc.Tab(label="Axe 2 - Compétences",  value="axe2"),
        dcc.Tab(label="Axes 3/4 - Mobilités",  value="axe3"),
    ]),

    # ── Axe 1 ────────────────────────────────────────────────────────
    html.Div(id="content-axe1", children=[

        dcc.Store(id="selected-caracteristique", data="Transition écologique"),

        # En-tête
        html.Div([
            html.H1("Dashboard ROME", style={"marginBottom": "10px", "color": "#1f2d3d"}),
            html.P("Problématique générale : Comment le marché des métiers est-il structuré en France, "
                   "et comment les compétences permettent-elles d'expliquer les proximités et les évolutions possibles entre métiers ?",
                   style={"fontSize": "18px", "color": "#444", "marginBottom": "25px", "lineHeight": "1.6"}),
            html.H2("AXE 1 : CARTOGRAPHIE DU RÉFÉRENTIEL ROME", style={'fontWeight': '800', 'color': "#0A0A0A", 'letterSpacing': '0.5px'}),
            html.P("Question de l'axe : Comment le référentiel ROME est-il structuré ? "
                   "Existe-t-il une concentration des métiers et des appellations dans certains domaines ?",
                   style={"fontSize": "17px", "color": "#555", "lineHeight": "1.6"}),
        ], style={"backgroundColor": "#f8fbff", "padding": "30px", "borderRadius": "12px",
                  "marginBottom": "30px", "boxShadow": "0 2px 8px rgba(0,0,0,0.06)"}),

        # KPIs
        html.Div([
            html.Div([html.H3(kpis["nb_metiers"]),          html.P("Métiers ROME")],
                     style={"backgroundColor":"white","padding":"20px","borderRadius":"10px","flex":"1","textAlign":"center","boxShadow":"0 1px 4px rgba(0,0,0,0.05)"}),
            html.Div([html.H3(kpis["nb_appellations"]),     html.P("Appellations / emplois")],
                     style={"backgroundColor":"white","padding":"20px","borderRadius":"10px","flex":"1","textAlign":"center","boxShadow":"0 1px 4px rgba(0,0,0,0.05)"}),
            html.Div([html.H3(kpis["nb_grands_domaines"]),  html.P("Grands domaines")],
                     style={"backgroundColor":"white","padding":"20px","borderRadius":"10px","flex":"1","textAlign":"center","boxShadow":"0 1px 4px rgba(0,0,0,0.05)"}),
            html.Div([html.H3(kpis["nb_domaines_professionnels"]), html.P("Domaines professionnels")],
                     style={"backgroundColor":"white","padding":"20px","borderRadius":"10px","flex":"1","textAlign":"center","boxShadow":"0 1px 4px rgba(0,0,0,0.05)"}),
        ], style={"display":"flex","gap":"20px","marginBottom":"30px"}),

        # Graphique 1
        html.Div([
            html.H3("Répartition des métiers ROME par grand domaine", style={"color":"#1f2d3d","marginBottom":"10px"}),
            html.P("Objectif : proposer une lecture macro de la structure du référentiel ROME.",
                   style={"color":"#555","fontSize":"15px","lineHeight":"1.6","marginBottom":"10px"}),
            dcc.Graph(figure=fig_metiers_grands_domaines),
            html.Div([html.H4("À retenir", style={"marginTop":"0","color":"#2E86AB"}),
                      html.P("Ce graphique met en évidence la répartition des métiers entre les 14 grands domaines du référentiel. "
                             "Il permet de repérer les grands pôles d'activité, mais aussi les domaines plus spécialisés.",
                             style={"marginBottom":"0","lineHeight":"1.6","color":"#444"})], style=_NOTE)
        ], style=_CARD),

        # Graphique 2
        html.Div([
            html.H3("Volume d'appellations par grand domaine", style={"color":"#1f2d3d","marginBottom":"10px"}),
            html.P("Objectif : mesurer la diversité des intitulés d'emploi associés aux différents grands domaines.",
                   style={"color":"#555","fontSize":"15px","lineHeight":"1.6","marginBottom":"10px"}),
            dcc.Graph(figure=fig_comparaison),
            html.Div([html.H4("À retenir", style={"marginTop":"0","color":"#2E86AB"}),
                      html.P("Ce graphique se concentre sur les appellations, c'est-à-dire les intitulés d'emploi concrets associés aux métiers.",
                             style={"marginBottom":"0","lineHeight":"1.6","color":"#444"})], style=_NOTE)
        ], style=_CARD),

        # Graphique 3
        html.Div([
            html.H3("Top 10 des domaines professionnels par nombre d'appellations", style={"color":"#1f2d3d","marginBottom":"10px"}),
            html.P("Objectif : affiner l'analyse en identifiant les domaines qui concentrent le plus d'intitulés d'emploi.",
                   style={"color":"#555","fontSize":"15px","lineHeight":"1.6","marginBottom":"10px"}),
            dcc.Graph(figure=fig_top10_appellations),
            html.Div([html.H4("À retenir", style={"marginTop":"0","color":"#2E86AB"}),
                      html.P("Ce graphique identifie les domaines où la granularité est la plus forte.",
                             style={"marginBottom":"0","lineHeight":"1.6","color":"#444"})], style=_NOTE)
        ], style=_CARD),

        # Donuts interactifs
        html.Div([
            html.H3("Caractéristiques transversales des métiers", style={"color":"#1f2d3d","marginBottom":"10px"}),
            html.P("Cliquez sur une caractéristique dans un donut pour afficher les métiers correspondants.",
                   style={"color":"#555","fontSize":"15px","lineHeight":"1.6","marginBottom":"20px"}),
            html.Div([
                html.Div([
                    dcc.Graph(id="fig-transitions", figure=make_transitions_figure("Transition écologique")),
                    html.Div([html.H4("À retenir", style={"marginTop":"0","color":"#2E86AB"}),
                              html.P("Part des métiers liés aux transitions écologique, numérique et démographique.",
                                     style={"marginBottom":"0","lineHeight":"1.6","color":"#444"})], style=_NOTE)
                ], style={"width":"48%"}),
                html.Div([
                    dcc.Graph(id="fig-autres", figure=make_autres_figure(None)),
                    html.Div([html.H4("À retenir", style={"marginTop":"0","color":"#2E86AB"}),
                              html.P("Distingue les métiers cadres des métiers réglementés.",
                                     style={"marginBottom":"0","lineHeight":"1.6","color":"#444"})], style=_NOTE)
                ], style={"width":"48%"}),
            ], style={"display":"flex","justifyContent":"space-between","alignItems":"flex-start","gap":"20px"}),
        ], style=_CARD),

        # Table filtrée
        html.Div([
            html.H3("Liste des métiers par caractéristique", style={"color":"#1f2d3d","marginBottom":"10px"}),
            dcc.RadioItems(
                id="filter-caracteristique",
                options=[
                    {"label": "Transition numérique",    "value": "Transition numérique"},
                    {"label": "Transition écologique",   "value": "Transition écologique"},
                    {"label": "Transition démographique","value": "Transition démographique"},
                    {"label": "Emploi cadre",            "value": "Emploi cadre"},
                    {"label": "Emploi réglementé",       "value": "Emploi réglementé"},
                ],
                value="Transition écologique", inline=True,
                style={"marginBottom":"20px"},
                inputStyle={"marginRight":"6px","marginLeft":"12px"}
            ),
            dash_table.DataTable(
                id="table-metiers-caracteristique",
                columns=[
                    {"name": "Code ROME",           "id": "code_rome"},
                    {"name": "Métier",               "id": "libelle_rome"},
                    {"name": "Grand domaine",         "id": "libelle_grand_domaine"},
                    {"name": "Domaine professionnel", "id": "libelle_domaine_professionel"},
                ],
                data=[], page_size=10, sort_action="native", filter_action="native",
                style_table={"overflowX":"auto"},
                style_cell={"textAlign":"left","padding":"10px","fontFamily":"Arial","fontSize":"14px",
                            "whiteSpace":"normal","height":"auto"},
                style_header={"backgroundColor":"#eaf2f8","fontWeight":"bold"}
            )
        ], style=_CARD),

    ]),  # fin content-axe1

    # ── Axe 2 ────────────────────────────────────────────────────────
    html.Div(id="content-axe2", style={"display": "none"}, children=[
        html.H2("AXE 2 : ANALYSE DES COMPÉTENCES", style={'fontWeight': '800', 'color': "#0A0A0A", 'letterSpacing': '0.5px'}),
        html.Div([
            html.H3("Compétences les plus transversales"), html.P("Compétences apparaissant dans le plus de métiers."),
            dcc.Graph(figure=fig_top_comp)
        ], style=_CARD),
        html.Div([
            html.H3("Répartition des catégories"), html.P("Part des savoir-faire et des savoir-être en nombre d'occurrences."),
            dcc.Graph(figure=fig_cat_dist)
        ], style=_CARD),
        html.Div([
            html.H3("Répartition des sous-catégories"), html.P("Typologie des compétences (Technique, Expert, Transverse)."),
            dcc.Graph(figure=fig_sub_dist)
        ], style=_CARD),
        html.Div([
            html.H3("Métiers valorisant les compétences transversales"),
            html.P("Classement des métiers selon la part de compétences de sous-catégorie Transverse."),
            dcc.Graph(figure=fig_ratio_trans)
        ], style=_CARD),
        html.Div([
            html.H3("Compétences moyennes par domaine"),
            html.P("Comparaison des domaines selon le nombre moyen de compétences par métier."),
            dcc.Graph(figure=fig_domain_summary)
        ], style=_CARD),
        html.Div([
            html.H3("Explorer par domaine et métier"),
            html.Div([
                html.Div([html.Label("Domaine :"),
                          dcc.Dropdown(id="domain-dropdown", options=domain_options, value=domain_options[0]["value"])],
                         style={"width":"48%","display":"inline-block"}),
                html.Div([html.Label("Métier :"),
                          dcc.Dropdown(id="job-dropdown", options=[], placeholder="Sélectionnez un métier")],
                         style={"width":"48%","display":"inline-block","marginLeft":"4%"}),
            ]),
            html.Br(),
            dcc.Graph(id="job-breakdown"),
            html.Div(id="job-kpi", style={"fontWeight":"bold","fontSize":"18px","marginTop":"10px"}),
        ], style=_CARD),
    ]),  # fin content-axe2

    # ── Axe 3/4 ──────────────────────────────────────────────────────
    html.Div(id="content-axe3", style={"display": "none"}, children=[
        dcc.Store(id='active-metier-store'),
        dbc.Container([
            render_axe3(df_gd),
            render_axe4()
        ], fluid=True),
    ]),  # fin content-axe3

], style={"padding":"30px 40px","backgroundColor":"#f5f7fa",
          "fontFamily":"Arial, sans-serif","width":"100%","boxSizing":"border-box"})

# ════════════════════════════════════════════════════════════════════
# CALLBACKS — visibilité des onglets
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
# CALLBACKS — Axe 1
# ════════════════════════════════════════════════════════════════════

@callback(
    Output("selected-caracteristique", "data"),
    Output("filter-caracteristique",   "value"),
    Input("fig-transitions",          "clickData"),
    Input("fig-autres",               "clickData"),
    Input("filter-caracteristique",   "value"),
)
def update_selected_caracteristique(click_trans, click_autres, filter_val):
    triggered = ctx.triggered_id
    if triggered == "fig-transitions" and click_trans:
        v = click_trans["points"][0]["label"]
        return v, v
    if triggered == "fig-autres" and click_autres:
        v = click_autres["points"][0]["label"]
        return v, v
    return filter_val, filter_val

@callback(
    Output("fig-transitions",                  "figure"),
    Output("fig-autres",                       "figure"),
    Output("table-metiers-caracteristique",    "data"),
    Input("selected-caracteristique",          "data"),
)
def update_figures_and_table(selected):
    df = axe1["caracteristiques_metiers"].copy()
    df_f = (df[df["caracteristique"] == selected]
              .drop_duplicates(subset=["code_rome"])
              .sort_values(["libelle_grand_domaine", "libelle_domaine_professionel", "libelle_rome"]))
    return make_transitions_figure(selected), make_autres_figure(selected), df_f.to_dict("records")

# ════════════════════════════════════════════════════════════════════
# CALLBACKS — Axe 2
# ════════════════════════════════════════════════════════════════════

@callback(
    Output("job-dropdown", "options"),
    Output("job-dropdown", "value"),
    Input("domain-dropdown", "value"),
)
def update_job_dropdown(selected_domain):
    jobs = domain_job_breakdown[domain_job_breakdown["libelle_grand_domaine"] == selected_domain]
    opts = [{"label": r["libelle_rome"], "value": r["code_rome"]}
            for _, r in jobs.sort_values("libelle_rome").iterrows()]
    return opts, (opts[0]["value"] if opts else None)

@callback(
    Output("job-breakdown", "figure"),
    Output("job-kpi",       "children"),
    Input("job-dropdown",   "value"),
)
def update_job_breakdown(code):
    fig = plot_job_skill_breakdown(domain_job_breakdown, code)
    row_df = domain_job_breakdown[domain_job_breakdown["code_rome"] == code]
    if row_df.empty:
        return fig, "Aucun métier sélectionné."
    row  = row_df.iloc[0]
    cols = [c for c in row.index if c not in ["libelle_grand_domaine", "code_rome", "libelle_rome"]]
    return fig, f"Métier : {row['libelle_rome']} — {int(sum(row[c] for c in cols))} compétences"

# ════════════════════════════════════════════════════════════════════
# CALLBACKS — Axe 3/4
# ════════════════════════════════════════════════════════════════════

@dash.callback(
    [Output('metier-zoom-filter', 'options'), Output('metier-zoom-filter', 'value')],
    [Input('domaine-filter', 'value'), Input('active-metier-store', 'data')],
)
def update_metier_options(selected_domaine, stored_metier):
    df_f = df_rome[df_rome['code_rome'].str.startswith(selected_domaine)]
    opts = [{'label': f"{r['code_rome']} - {r['libelle_rome']}", 'value': r['code_rome']}
            for _, r in df_f.iterrows()]
    return opts, stored_metier

@dash.callback(
    Output('active-metier-store', 'data'),
    [Input({'type': 'btn-voir-fiche', 'index': ALL}, 'n_clicks'),
     Input('g7-net-graph',       'clickData'),
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
    [Output('g7-net-graph',              'figure'),
     Output('table-legende',             'data'),
     Output('g8-pivots-graph',           'figure'),
     Output('g10-potentiel-global',      'figure'),
     Output('section-axe4',              'style'),
     Output('fiche-titre-metier',        'children'),
     Output('metier-tags',               'children'),
     Output('fiche-competences',         'children'),
     Output('g12-radar-riasec',          'figure'),
     Output('container-metiers-similaires', 'children')],
    [Input('domaine-filter',       'value'),
     Input('active-metier-store',  'data')],
)
def update_all_analytics(selected_domaine, active_metier):
    # ── Graphe de mobilité (Axe 3) ───────────────────────────────────
    df_f = df_mobi[df_mobi['code_rome'].str.startswith(selected_domaine)].copy()
    G    = nx.from_pandas_edgelist(df_f, source='code_rome', target='code_rome_cible', create_using=nx.DiGraph())
    d_dict = dict(G.degree)
    pos    = nx.spring_layout(G, k=0.4, iterations=30, seed=42)

    fig7 = go.Figure()
    edge_x, edge_y, active_edge_x, active_edge_y = [], [], [], []
    for edge in G.edges():
        if edge[0] in pos and edge[1] in pos:
            x0, y0 = pos[edge[0]]; x1, y1 = pos[edge[1]]
            if active_metier and (str(edge[0]) == str(active_metier) or str(edge[1]) == str(active_metier)):
                active_edge_x.extend([x0, x1, None]); active_edge_y.extend([y0, y1, None])
            else:
                edge_x.extend([x0, x1, None]); edge_y.extend([y0, y1, None])

    fig7.add_trace(go.Scatter(x=edge_x,        y=edge_y,        line=dict(width=0.5, color='#dfe6e9'), hoverinfo='none', mode='lines'))
    fig7.add_trace(go.Scatter(x=active_edge_x, y=active_edge_y, line=dict(width=2,   color='#e74c3c'), hoverinfo='none', mode='lines'))

    node_x, node_y, node_text, colors, sizes = [], [], [], [], []
    for n in G.nodes():
        lib = df_rome[df_rome['code_rome'] == str(n)]['libelle_rome'].values
        node_text.append(f"Métier: {n} - {lib[0] if len(lib) > 0 else ''}<br>Relations: {d_dict[n]}")
        node_x.append(pos[n][0]); node_y.append(pos[n][1])
        colors.append('#e74c3c' if str(n) == str(active_metier) else "#42b2c1")
        sizes.append(30 if str(n) == str(active_metier) else (d_dict[n] * 2) + 10)
    fig7.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers',
                              marker=dict(size=sizes, color=colors, line=dict(color='white', width=1)),
                              text=node_text, hoverinfo='text'))

    if active_metier and active_metier in pos:
        fx, fy = pos[active_metier]
        fig7.update_xaxes(range=[fx - 0.3, fx + 0.3])
        fig7.update_yaxes(range=[fy - 0.3, fy + 0.3])

    fig7.update_layout(plot_bgcolor='white', margin=dict(t=0, b=0, l=0, r=0),
                       showlegend=False, uirevision=selected_domaine,
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))

    df_pivots = (pd.DataFrame(list(d_dict.items()), columns=['code_rome', 'relations_count'])
                   .nlargest(10, 'relations_count')
                   .merge(df_rome[['code_rome', 'libelle_rome']], on='code_rome', how='left'))
    fig8 = go.Figure(go.Bar(x=df_pivots['relations_count'], y=df_pivots['libelle_rome'],
                            orientation='h', marker=dict(color="#42b2c1")))
    fig8.update_layout(paper_bgcolor='white', plot_bgcolor='white', height=400,
                       yaxis=dict(autorange="reversed"))

    df_moyennes = (df_mobi.groupby(df_mobi['code_rome'].str[0]).size()
                          .reset_index(name='count')
                          .merge(df_gd, left_on='code_rome', right_on='code_grand_domaine'))
    fig10 = go.Figure(go.Bar(x=df_moyennes['count'], y=df_moyennes['libelle_grand_domaine'],
                             orientation='h', marker=dict(color="#42b2c1")))
    fig10.update_layout(paper_bgcolor='white', plot_bgcolor='white', height=500)

    df_table_all = df_rome[df_rome['code_rome'].str.startswith(selected_domaine)].sort_values('code_rome')
    data_table = (df_table_all[df_table_all['code_rome'] == active_metier].to_dict('records')
                  if active_metier else df_table_all.to_dict('records'))

    # ── Fiche métier (Axe 4) ─────────────────────────────────────────
    if not active_metier or active_metier == "None" or active_metier not in df_rome['code_rome'].values:
        return fig7, data_table, fig8, fig10, {'display': 'none'}, "", [], [], go.Figure(), []

    m_info  = df_rome[df_rome['code_rome'] == active_metier].iloc[0]
    liens_m = df_liens[df_liens['code_rome'] == active_metier]

    tags = ([dbc.Badge("NUMÉRIQUE", color="info", className="px-3 py-2 me-2")]
            if str(m_info.get('transition_num')) == 'O' else [])
    if str(m_info.get('transition_eco')) == 'O':
        tags.append(dbc.Badge("ÉCO-TRANSITION", color="success", className="px-3 py-2"))

    c_ids       = liens_m[liens_m['code_compo_bloc'] == '5']['code_ogr'].unique()
    comp_labels = df_comp[df_comp['code_ogr'].isin(c_ids)]['libelle_competence'].unique()[:10]
    comp_list   = [html.Div([
                      html.Span("●", style={'color': '#42b2c1', 'marginRight': '15px', 'fontSize': '0.8rem'}),
                      html.Span(c)
                  ], style={'padding': '8px 0', 'borderBottom': '1px solid #f1f2f6'})
                  for c in comp_labels]

    scores  = [2] * 6
    r_match = df_riasec[df_riasec['code_rome'] == active_metier]
    if not r_match.empty:
        maj = str(r_match.iloc[0].get('riasec_majeur', ''))
        for i, l in enumerate(['R', 'I', 'A', 'S', 'E', 'C']):
            if l == maj:
                scores[i] = 5
    fig12 = go.Figure(data=go.Scatterpolar(
        r=scores,
        theta=['Réaliste', 'Investigateur', 'Artistique', 'Social', 'Entreprenant', 'Conventionnel'],
        fill='toself', line=dict(color='#42b2c1', width=3)
    ))
    fig12.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5], gridcolor="#f1f2f6")),
                        height=380, margin=dict(t=40, b=40, l=60, r=60))

    targets    = df_mobi[df_mobi['code_rome'] == active_metier]['code_rome_cible'].unique()[:4]
    sugg_cards = []
    for t in targets:
        t_lib = (df_rome[df_rome['code_rome'] == t]['libelle_rome'].values[0]
                 if t in df_rome['code_rome'].values else "Inconnu")
        sugg_cards.append(dbc.Col([
            dbc.Card([dbc.CardBody([
                html.Small(f"ROME {t}", style={'color':'#42b2c1','fontWeight':'800','fontSize':'0.85rem','display':'block','marginBottom':'10px'}),
                html.H5(t_lib, style={'fontWeight':'800','color':'#2c3e50','fontSize':'1.25rem','lineHeight':'1.4','minHeight':'60px'}),
                html.Hr(style={'opacity':'0.1','margin':'20px 0'}),
                html.Button("Voir la fiche →", id={'type':'btn-voir-fiche','index':t},
                            style={'width':'100%','padding':'12px','borderRadius':'8px','border':'none',
                                   'backgroundColor':'#eef9fa','color':'#42b2c1','fontWeight':'bold'})
            ], style={'padding':'25px'})], className="border-0 shadow-sm h-100")
        ], lg=3, md=6))

    return (fig7, data_table, fig8, fig10, {'display': 'block'},
            m_info['libelle_rome'], tags, comp_list, fig12, sugg_cards)