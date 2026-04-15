import dash
import dash_bootstrap_components as dbc
from dash import html


app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dash.page_container
])

server = app.server

if __name__ == "__main__":
    app.run(debug=True)