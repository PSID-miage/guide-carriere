import dash
from dash import html, dcc

dash.register_page(__name__, path="/")

layout = html.Div([
    
    html.H1("🚀 Career Coach", style={"textAlign": "center"}),

    html.P("Choisis une section :", style={"textAlign": "center"}),

    html.Div([
        dcc.Link("📊 Aller au Dashboard", href="/dashboard",
                 style={
                     "padding": "20px",
                     "backgroundColor": "#4CAF50",
                     "color": "white",
                     "textDecoration": "none",
                     "borderRadius": "10px",
                     "margin": "10px",
                     "display": "inline-block"
                 }),

        dcc.Link("🤖 Aller au ML", href="/ml",
                 style={
                     "padding": "20px",
                     "backgroundColor": "#2196F3",
                     "color": "white",
                     "textDecoration": "none",
                     "borderRadius": "10px",
                     "margin": "10px",
                     "display": "inline-block"
                 }),
    ], style={"textAlign": "center", "marginTop": "50px"})

])