import dash
from dash import html, dcc

dash.register_page(__name__, path="/ml")

layout = html.Div([

    html.H1("🤖 ML Career Coach"),

    dcc.Link("⬅ Retour accueil", href="/"),

    html.Br(), html.Br(),

    html.P("Entre tes compétences :"),

    dcc.Textarea(
        placeholder="ex: python, sql, machine learning",
        style={"width": "50%", "height": 100}
    ),

    html.Br(), html.Br(),

    html.Button("Analyser", style={
        "padding": "10px 20px",
        "backgroundColor": "#4CAF50",
        "color": "white",
        "border": "none",
        "borderRadius": "5px"
    })

])