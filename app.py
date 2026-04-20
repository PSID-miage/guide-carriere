
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.title = "Career Navigator | Carrière & Compétences"

app.layout = html.Div(
    [
        dcc.Store(id="skills-store", data={}),
        dcc.Store(id="cv-data-store", data={}),
        dcc.Store(id="analysis-store", data={}),

        html.Div(dash.page_container, className="page-wrapper"),
    ],
    className="app-shell",
)

server = app.server

if __name__ == "__main__":
    app.run(debug=True)