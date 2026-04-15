import dash
from dash import html, dcc, Input, Output, State, ALL, callback_context
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

from components.axe3 import render_axe3
from components.axe4 import render_axe4

dash.register_page(__name__, path='/dashboard')

# Chargement
df_mobi = pd.read_csv('data/unix_rubrique_mobilite_v460_utf8.csv')
df_rome = pd.read_csv('data/unix_referentiel_code_rome_v460_utf8.csv')
df_gd = pd.read_csv('data/unix_grand_domaine_v460_utf8.csv')
df_liens = pd.read_csv('data/unix_liens_rome_referentiels_v460_utf8.csv')
df_comp = pd.read_csv('data/unix_referentiel_competence_v460_utf8.csv')
df_riasec = pd.read_csv('data/unix_referentiel_code_rome_riasec_v460_utf8.csv')

# Nettoyage
for df in [df_mobi, df_rome, df_gd, df_liens, df_comp, df_riasec]:
    for col in df.columns:
        if 'code' in col.lower() or 'ogr' in col.lower(): 
            df[col] = df[col].astype(str).str.strip()

layout = dbc.Container([
    dcc.Store(id='active-metier-store'),
    render_axe3(df_gd), 
    render_axe4()
], fluid=True)

@dash.callback(
    [Output('metier-zoom-filter', 'options'), Output('metier-zoom-filter', 'value')],
    [Input('domaine-filter', 'value'), Input('active-metier-store', 'data')]
)
def update_metier_options(selected_domaine, stored_metier):
    df_metiers_filtres = df_rome[df_rome['code_rome'].str.startswith(selected_domaine)]
    options = [{'label': f"{row['code_rome']} - {row['libelle_rome']}", 'value': row['code_rome']} for _, row in df_metiers_filtres.iterrows()]
    return options, stored_metier

@dash.callback(
    Output('active-metier-store', 'data'),
    [Input({'type': 'btn-voir-fiche', 'index': ALL}, 'n_clicks'),
     Input('g7-net-graph', 'clickData'),
     Input('metier-zoom-filter', 'value')],
    prevent_initial_call=True
)
def handle_navigation(btn_clicks, clickData, dropdown_val):
    ctx = callback_context
    if not ctx.triggered: return dash.no_update
    trig_id = ctx.triggered[0]['prop_id']
    if 'btn-voir-fiche' in trig_id:
        import json
        return json.loads(trig_id.split('.')[0])['index']
    if 'g7-net-graph' in trig_id and clickData:
        return clickData['points'][0]['text'].split(':')[1].split('-')[0].strip()
    return dropdown_val

@dash.callback(
    [
        Output('g7-net-graph', 'figure'), Output('table-legende', 'data'),
        Output('g8-pivots-graph', 'figure'), Output('g10-potentiel-global', 'figure'),
        Output('section-axe4', 'style'), Output('fiche-titre-metier', 'children'),
        Output('metier-tags', 'children'), Output('fiche-competences', 'children'),
        Output('g12-radar-riasec', 'figure'), Output('container-metiers-similaires', 'children')
    ],
    [Input('domaine-filter', 'value'), Input('active-metier-store', 'data')]
)
def update_all_analytics(selected_domaine, active_metier):
    # Logique Axe 3 (Graphe)
    df_f = df_mobi[df_mobi['code_rome'].str.startswith(selected_domaine)].copy()
    G = nx.from_pandas_edgelist(df_f, source='code_rome', target='code_rome_cible', create_using=nx.DiGraph())
    d_dict = dict(G.degree) 
    pos = nx.spring_layout(G, k=0.4, iterations=30, seed=42)
    
    fig7 = go.Figure()
    edge_x, edge_y, active_edge_x, active_edge_y = [], [], [], []
    for edge in G.edges():
        if edge[0] in pos and edge[1] in pos:
            x0, y0 = pos[edge[0]]; x1, y1 = pos[edge[1]]
            if active_metier and (str(edge[0]) == str(active_metier) or str(edge[1]) == str(active_metier)):
                active_edge_x.extend([x0, x1, None]); active_edge_y.extend([y0, y1, None])
            else:
                edge_x.extend([x0, x1, None]); edge_y.extend([y0, y1, None])
    
    fig7.add_trace(go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#dfe6e9'), hoverinfo='none', mode='lines'))
    fig7.add_trace(go.Scatter(x=active_edge_x, y=active_edge_y, line=dict(width=2, color='#e74c3c'), hoverinfo='none', mode='lines'))
    
    node_x, node_y, node_text, colors, sizes = [], [], [], [], []
    for n in G.nodes():
        lib = df_rome[df_rome['code_rome'] == str(n)]['libelle_rome'].values
        node_text.append(f"Métier: {n} - {lib[0] if len(lib)>0 else ''}<br>Relations: {d_dict[n]}")
        node_x.append(pos[n][0]); node_y.append(pos[n][1])
        colors.append('#e74c3c' if str(n) == str(active_metier) else "#42b2c1")
        sizes.append(30 if str(n) == str(active_metier) else (d_dict[n]*2)+10)
    fig7.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers', marker=dict(size=sizes, color=colors, line=dict(color='white', width=1)), text=node_text, hoverinfo='text'))
    
    if active_metier and active_metier in pos:
        fx, fy = pos[active_metier]
        fig7.update_xaxes(range=[fx - 0.3, fx + 0.3]); fig7.update_yaxes(range=[fy - 0.3, fy + 0.3])
    
    fig7.update_layout(plot_bgcolor='white', margin=dict(t=0, b=0, l=0, r=0), showlegend=False, uirevision=selected_domaine,
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))

    df_pivots = pd.DataFrame(list(d_dict.items()), columns=['code_rome', 'relations_count']).nlargest(10, 'relations_count')
    df_pivots = df_pivots.merge(df_rome[['code_rome', 'libelle_rome']], on='code_rome', how='left')
    fig8 = go.Figure(go.Bar(x=df_pivots['relations_count'], y=df_pivots['libelle_rome'], orientation='h', marker=dict(color="#42b2c1")))

    df_moyennes = df_mobi.groupby(df_mobi['code_rome'].str[0]).size().reset_index(name='count').merge(df_gd, left_on='code_rome', right_on='code_grand_domaine')
    fig10 = go.Figure(go.Bar(x=df_moyennes['count'], y=df_moyennes['libelle_grand_domaine'], orientation='h', marker=dict(color="#42b2c1")))
    
    df_table_all = df_rome[df_rome['code_rome'].str.startswith(selected_domaine)].sort_values('code_rome')
    data_table = df_table_all[df_table_all['code_rome'] == active_metier].to_dict('records') if active_metier else df_table_all.to_dict('records')

    # Axe 4 logic
    if not active_metier or active_metier == "None" or active_metier not in df_rome['code_rome'].values:
        return fig7, data_table, fig8, fig10, {'display': 'none'}, "", [], [], go.Figure(), []

    m_info = df_rome[df_rome['code_rome'] == active_metier].iloc[0]
    liens_m = df_liens[df_liens['code_rome'] == active_metier]
    
    tags = [dbc.Badge("NUMÉRIQUE", color="info", className="px-3 py-2 me-2")] if str(m_info.get('transition_num')) == 'O' else []
    if str(m_info.get('transition_eco')) == 'O': tags.append(dbc.Badge("ÉCO-TRANSITION", color="success", className="px-3 py-2"))

    c_ids = liens_m[liens_m['code_compo_bloc'] == '5']['code_ogr'].unique()
    comp_labels = df_comp[df_comp['code_ogr'].isin(c_ids)]['libelle_competence'].unique()[:10]
    comp_list = [html.Div([html.Span("●", style={'color': '#42b2c1', 'marginRight': '15px', 'fontSize': '0.8rem'}), html.Span(c)], style={'padding': '8px 0', 'borderBottom': '1px solid #f1f2f6'}) for c in comp_labels]

    scores = [2]*6
    r_match = df_riasec[df_riasec['code_rome'] == active_metier]
    if not r_match.empty:
        maj = str(r_match.iloc[0].get('riasec_majeur', ''))
        for i, l in enumerate(['R','I','A','S','E','C']):
            if l == maj: scores[i] = 5
    fig12 = go.Figure(data=go.Scatterpolar(r=scores, theta=['Réaliste','Investigateur','Artistique','Social','Entreprenant','Conventionnel'], fill='toself', line=dict(color='#42b2c1', width=3)))
    fig12.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5], gridcolor="#f1f2f6")), height=380, margin=dict(t=40, b=40, l=60, r=60))

    targets = df_mobi[df_mobi['code_rome'] == active_metier]['code_rome_cible'].unique()[:4]
    sugg_cards = []
    for t in targets:
        t_lib = df_rome[df_rome['code_rome']==t]['libelle_rome'].values[0] if t in df_rome['code_rome'].values else "Inconnu"
        sugg_cards.append(dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Small(f"ROME {t}", style={'color': '#42b2c1', 'fontWeight': '800', 'fontSize': '0.85rem', 'display': 'block', 'marginBottom': '10px'}),
                    html.H5(t_lib, style={'fontWeight': '800', 'color': '#2c3e50', 'fontSize': '1.25rem', 'lineHeight': '1.4', 'minHeight': '60px'}),
                    html.Hr(style={'opacity': '0.1', 'margin': '20px 0'}),
                    html.Button(["Voir la fiche →"], id={'type': 'btn-voir-fiche', 'index': t}, style={'width': '100%', 'padding': '12px', 'borderRadius': '8px', 'border': 'none', 'backgroundColor': '#eef9fa', 'color': '#42b2c1', 'fontWeight': 'bold'})
                ], style={'padding': '25px'})
            ], className="border-0 shadow-sm h-100")
        ], lg=3, md=6))

    return (fig7, data_table, fig8, fig10, {'display': 'block'}, m_info['libelle_rome'], tags, comp_list, fig12, sugg_cards)