import dash
from dash import html, dcc
import pandas as pd
import plotly.express as px

dash.register_page(__name__, path="/dashboard")

# ======================
# Charger dataset
# ======================
df = pd.read_csv("data/final_jobs.csv")

# ======================
# Préparer données
# ======================
df["nb_skills"] = df["skill"].apply(lambda x: len(x.split(",")))

# Top métiers
top_jobs = df.sort_values(by="nb_skills", ascending=False).head(10)

fig = px.bar(
    top_jobs,
    x="nb_skills",
    y="job_title",
    orientation="h",
    title="Top métiers avec le plus de compétences"
)

# ======================
# Layout
# ======================
layout = html.Div([

    html.H1("📊 Analyse du marché de l'emploi"),

    html.A("⬅ Retour accueil", href="/"),

    html.Br(), html.Br(),

    html.H2("🔝 Métiers les plus complexes"),

    dcc.Graph(figure=fig),

])