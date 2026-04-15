import dash
from dash import html, dcc
import plotly.express as px

from components.axe1 import prepare_axe1_data

dash.register_page(__name__, path="/dashboard")

axe1 = prepare_axe1_data("data/")

kpis = axe1["kpis"]

fig_metiers_grands_domaines = px.bar(
    axe1["metiers_par_grand_domaine"],
    x="nb_metiers",
    y="libelle_grand_domaine",
    orientation="h",
    text="nb_metiers",
    title="Répartition des métiers ROME par grand domaine",
    color="nb_metiers",
    color_continuous_scale="Teal",
    labels={
        "nb_metiers": "Nombre de métiers",
        "libelle_grand_domaine": "Grand domaine"
    }
)

fig_metiers_grands_domaines.update_traces(
    textposition="outside",
    marker_line_width=0
)

fig_metiers_grands_domaines.update_layout(
    height=550,
    template="plotly_white",
    title_x=0.02,
    xaxis_title="Nombre de métiers ROME",
    yaxis_title="",
    margin=dict(l=220, r=60, t=70, b=50),
    coloraxis_showscale=False,
    bargap=0.25
)

fig_comparaison = px.bar_polar(
    axe1["comparaison_grands_domaines"],
    r="nb_appellations",
    theta="libelle_grand_domaine",
    color="nb_appellations",
    title="Volume d’appellations par grand domaine",
    labels={
        "nb_appellations": "Nombre d’appellations",
        "libelle_grand_domaine": "Grand domaine"
    },
    color_continuous_scale="Teal",
    custom_data=["libelle_grand_domaine", "nb_appellations", "nb_metiers"]
)

fig_comparaison.update_traces(
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "Nombre d’appellations : %{customdata[1]}<br>"
        "Nombre de métiers ROME : %{customdata[2]}<extra></extra>"
    )
)

fig_comparaison.update_layout(
    template="plotly_white",
    height=600,
    title_x=0.02,
    coloraxis_showscale=False,
    margin=dict(l=40, r=40, t=70, b=40)
)

fig_top10_appellations = px.bar(
    axe1["top10_domaines_appellations"],
    x="nb_appellations",
    y="libelle_domaine_professionel",
    orientation="h",
    text="nb_appellations",
    hover_data=["libelle_grand_domaine", "nb_metiers"],
    title="Top 10 des domaines professionnels par nombre d’appellations",
    labels={
        "nb_appellations": "Nombre d’appellations",
        "libelle_domaine_professionel": "Domaine professionnel"
    }
)

fig_top10_appellations.update_traces(
    marker_color="#2E86AB",
    textposition="outside"
)

fig_top10_appellations.update_layout(
    template="plotly_white",
    height=550,
    title_x=0.02,
    yaxis={"categoryorder": "total ascending"},
    xaxis_title="Nombre d’appellations",
    yaxis_title="",
    margin=dict(l=260, r=80, t=70, b=50),
    bargap=0.25
)

fig_transitions = px.pie(
    axe1["tags_metiers"][
        axe1["tags_metiers"]["caracteristique"].isin([
            "Transition numérique",
            "Transition écologique",
            "Transition démographique"
        ])
    ],
    names="caracteristique",
    values="nb_metiers",
    hole=0.45,
    title="Métiers liés aux transitions",
    color="caracteristique",
    color_discrete_map={
        "Transition numérique": "#A8DADC",
        "Transition écologique": "#CDEAC0",
        "Transition démographique": "#F4C2C2"
    }
)

fig_transitions.update_traces(
    textinfo="percent+label"
)

fig_transitions.update_layout(
    template="plotly_white",
    height=420,
    title_x=0.02,
    margin=dict(l=30, r=30, t=70, b=30),
    legend_title_text=""
)

fig_autres = px.pie(
    axe1["tags_metiers"][
        axe1["tags_metiers"]["caracteristique"].isin([
            "Emploi cadre",
            "Emploi réglementé"
        ])
    ],
    names="caracteristique",
    values="nb_metiers",
    hole=0.45,
    title="Autres caractéristiques métiers",
    color="caracteristique",
    color_discrete_map={
        "Emploi cadre": "#CDB4DB",
        "Emploi réglementé": "#FFD6A5"
    }
)

fig_autres.update_traces(
    textinfo="percent+label"
)

fig_autres.update_layout(
    template="plotly_white",
    height=420,
    title_x=0.02,
    margin=dict(l=30, r=30, t=70, b=30),
    legend_title_text=""
)

fig_transitions.update_traces(textinfo="percent")
fig_autres.update_traces(textinfo="percent")

layout = html.Div([

    html.Div([
        html.H1(
            "Dashboard ROME",
            style={
                "marginBottom": "10px",
                "color": "#1f2d3d"
            }
        ),

        html.P(
            "Problématique générale : Comment le marché des métiers est-il structuré en France, "
            "et comment les compétences permettent-elles d’expliquer les proximités et les évolutions possibles entre métiers ?",
            style={
                "fontSize": "18px",
                "color": "#444",
                "marginBottom": "25px",
                "lineHeight": "1.6",
                "width": "100%"
            }
        ),

        html.H2(
            "Axe 1 — Cartographie du référentiel ROME",
            style={
                "color": "#2E86AB",
                "marginBottom": "10px"
            }
        ),

        html.P(
            "Question de l’axe : Comment le référentiel ROME est-il structuré ? "
            "Existe-t-il une concentration des métiers et des appellations dans certains domaines ?",
            style={
                "fontSize": "17px",
                "color": "#555",
                "marginBottom": "15px",
                "lineHeight": "1.6",
                "width": "100%"
            }
        ),

        html.P(
            "Cet axe propose une lecture macro du référentiel en analysant la répartition des métiers, "
            "des appellations et de certaines caractéristiques transversales.",
            style={
                "fontSize": "15px",
                "color": "#666",
                "marginBottom": "0",
                "lineHeight": "1.6",
                "width": "100%"
            }
        ),
    ], style={
        "backgroundColor": "#f8fbff",
        "padding": "30px",
        "borderRadius": "12px",
        "marginBottom": "30px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
        "width": "100%",
        "boxSizing": "border-box"
    }),

    html.Div([
        html.Div([
            html.H3(kpis["nb_metiers"], style={"marginBottom": "5px", "color": "#1f2d3d"}),
            html.P("Métiers ROME", style={"margin": "0", "color": "#666"})
        ], style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "10px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
            "flex": "1",
            "textAlign": "center"
        }),

        html.Div([
            html.H3(kpis["nb_appellations"], style={"marginBottom": "5px", "color": "#1f2d3d"}),
            html.P("Appellations / emplois", style={"margin": "0", "color": "#666"})
        ], style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "10px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
            "flex": "1",
            "textAlign": "center"
        }),

        html.Div([
            html.H3(kpis["nb_grands_domaines"], style={"marginBottom": "5px", "color": "#1f2d3d"}),
            html.P("Grands domaines", style={"margin": "0", "color": "#666"})
        ], style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "10px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
            "flex": "1",
            "textAlign": "center"
        }),

        html.Div([
            html.H3(kpis["nb_domaines_professionnels"], style={"marginBottom": "5px", "color": "#1f2d3d"}),
            html.P("Domaines professionnels", style={"margin": "0", "color": "#666"})
        ], style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "10px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.05)",
            "flex": "1",
            "textAlign": "center"
        }),
    ], style={
        "display": "flex",
        "gap": "20px",
        "marginBottom": "30px"
    }),

    html.Div([
        html.H3(
            "Répartition des métiers ROME par grand domaine",
            style={"color": "#1f2d3d", "marginBottom": "10px"}
        ),
        html.P(
            "Objectif : proposer une lecture macro de la structure du référentiel ROME en identifiant "
            "les grands domaines les plus et les moins représentés.",
            style={
                "color": "#555",
                "fontSize": "15px",
                "lineHeight": "1.6",
                "marginBottom": "10px"
            }
        ),
        dcc.Graph(figure=fig_metiers_grands_domaines),
        html.Div([
            html.H4("À retenir", style={"marginTop": "0", "color": "#2E86AB"}),
            html.P(
                "Ce graphique met en évidence la répartition des métiers entre les 14 grands domaines du référentiel. "
                "Il permet de repérer les grands pôles d’activité, mais aussi les domaines plus spécialisés. "
                "Une forte concentration de métiers dans certains domaines peut traduire une plus grande diversité de fonctions "
                "professionnelles, tandis que les domaines moins représentés renvoient à des secteurs plus ciblés.",
                style={"marginBottom": "0", "lineHeight": "1.6", "color": "#444"}
            )
        ], style={
            "backgroundColor": "#f8f9fb",
            "padding": "15px",
            "borderRadius": "10px",
            "marginTop": "10px"
        })
    ], style={
        "backgroundColor": "white",
        "padding": "25px",
        "borderRadius": "12px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.05)",
        "marginBottom": "30px"
    }),

    html.Div([
        html.H3(
            "Volume d’appellations par grand domaine",
            style={"color": "#1f2d3d", "marginBottom": "10px"}
        ),
        html.P(
            "Objectif : mesurer la diversité des intitulés d’emploi associés aux différents grands domaines du référentiel.",
            style={
                "color": "#555",
                "fontSize": "15px",
                "lineHeight": "1.6",
                "marginBottom": "10px"
            }
        ),
        dcc.Graph(figure=fig_comparaison),
        html.Div([
            html.H4("À retenir", style={"marginTop": "0", "color": "#2E86AB"}),
            html.P(
                "Contrairement au graphique précédent, qui s’intéresse aux métiers ROME, celui-ci se concentre sur les appellations, "
                "c’est-à-dire les intitulés d’emploi concrets associés aux métiers. "
                "Il permet donc d’évaluer la richesse terminologique et la diversité des dénominations présentes dans chaque grand domaine.",
                style={"marginBottom": "0", "lineHeight": "1.6", "color": "#444"}
            )
        ], style={
            "backgroundColor": "#f8f9fb",
            "padding": "15px",
            "borderRadius": "10px",
            "marginTop": "10px"
        })
    ], style={
        "backgroundColor": "white",
        "padding": "25px",
        "borderRadius": "12px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.05)",
        "marginBottom": "30px"
    }),

    html.Div([
        html.H3(
            "Top 10 des domaines professionnels par nombre d’appellations",
            style={"color": "#1f2d3d", "marginBottom": "10px"}
        ),
        html.P(
            "Objectif : affiner l’analyse en identifiant les domaines professionnels qui concentrent le plus grand nombre d’intitulés d’emploi.",
            style={
                "color": "#555",
                "fontSize": "15px",
                "lineHeight": "1.6",
                "marginBottom": "10px"
            }
        ),
        dcc.Graph(figure=fig_top10_appellations),
        html.Div([
            html.H4("À retenir", style={"marginTop": "0", "color": "#2E86AB"}),
            html.P(
                "Ce graphique propose un zoom sur les domaines professionnels les plus riches en appellations. "
                "Il permet d’identifier les domaines où la granularité est la plus forte, c’est-à-dire ceux où un même domaine "
                "regroupe de nombreux intitulés d’emploi proches, spécialisés ou contextualisés.",
                style={"marginBottom": "0", "lineHeight": "1.6", "color": "#444"}
            )
        ], style={
            "backgroundColor": "#f8f9fb",
            "padding": "15px",
            "borderRadius": "10px",
            "marginTop": "10px"
        })
    ], style={
        "backgroundColor": "white",
        "padding": "25px",
        "borderRadius": "12px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.05)",
        "marginBottom": "30px"
    }),

    html.Div([
        html.H3(
            "Caractéristiques transversales des métiers",
            style={"color": "#1f2d3d", "marginBottom": "10px"}
        ),
        html.P(
            "Cette partie distingue les métiers liés aux grandes transitions actuelles "
            "des métiers marqués par des caractéristiques statutaires ou réglementaires.",
            style={
                "color": "#555",
                "fontSize": "15px",
                "lineHeight": "1.6",
                "marginBottom": "20px"
            }
        ),

        html.Div([
            html.Div([
                dcc.Graph(figure=fig_transitions),
                html.Div([
                    html.H4("À retenir", style={"marginTop": "0", "color": "#2E86AB"}),
                    html.P(
                        "Ce graphique met en évidence la part des métiers associés aux transitions écologique, "
                        "numérique et démographique. Il apporte une lecture complémentaire du référentiel en montrant "
                        "que certains métiers sont directement liés aux grandes transformations actuelles du marché du travail.",
                        style={"marginBottom": "0", "lineHeight": "1.6", "color": "#444"}
                    )
                ], style={
                    "backgroundColor": "#f8f9fb",
                    "padding": "12px",
                    "borderRadius": "10px",
                    "marginTop": "10px"
                })
            ], style={"width": "48%"}),

            html.Div([
                dcc.Graph(figure=fig_autres),
                html.Div([
                    html.H4("À retenir", style={"marginTop": "0", "color": "#2E86AB"}),
                    html.P(
                        "Ce graphique distingue les métiers cadres des métiers réglementés. "
                        "Il permet d’ajouter une lecture plus statutaire du référentiel, en complément "
                        "de la lecture sectorielle et des grandes transitions.",
                        style={"marginBottom": "0", "lineHeight": "1.6", "color": "#444"}
                    )
                ], style={
                    "backgroundColor": "#f8f9fb",
                    "padding": "12px",
                    "borderRadius": "10px",
                    "marginTop": "10px"
                })
            ], style={"width": "48%"})
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "flex-start",
            "gap": "20px"
        })
    ], style={
        "backgroundColor": "white",
        "padding": "25px",
        "borderRadius": "12px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.05)",
        "marginBottom": "30px"
    })

], style={
    "padding": "30px 40px",
    "backgroundColor": "#f5f7fa",
    "fontFamily": "Arial, sans-serif",
    "width": "100%",
    "boxSizing": "border-box"
})