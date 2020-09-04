import copy
import datetime as dt
import json
import pathlib

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output

from controls import COMMUNES, TYPE_LOCALS, NATURE_MUTATIONS

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").joinpath("features").resolve()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server

# Create controls
commune_options = [
    {"label": str(COMMUNES[commun]), "value": str(COMMUNES[commun])} for commun in COMMUNES
]

type_locals_options = [
    {"label": str(TYPE_LOCALS[type_local]), "value": str(TYPE_LOCALS[type_local])}
    for type_local in TYPE_LOCALS
]

nature_mutation_options = [
    {"label": str(NATURE_MUTATIONS[nature_mutation]), "value": str(NATURE_MUTATIONS[nature_mutation])}
    for nature_mutation in NATURE_MUTATIONS
]

# Load data
df_avg_fon_dep = pd.read_pickle(DATA_PATH.joinpath("avg_foncier_per_code_departement.pkl"))
df_count_mutation = pd.read_pickle(DATA_PATH.joinpath("count_number_mutation.pkl"))
df_mean_val_fon_per_time = pd.read_pickle(DATA_PATH.joinpath("mean_valeur_fonciere_per_time.pkl"))
df_num_per_pieces = pd.read_pickle(DATA_PATH.joinpath("number_per_pieces.pkl"))
df_surf_terr_per_local = pd.read_pickle(DATA_PATH.joinpath("surface_terrain_per_type_local.pkl"))
geo = json.load(open(DATA_PATH.joinpath("departements.geojson"), encoding="utf-8"))
# Create global chart template
mapbox_access_token = "pk.eyJ1IjoieGlwZTIzNSIsImEiOiJja2VsMjBlaGYybHl4MnlsdHJ5YXZ4bDg4In0.zngFi0d7kxnaCUXLY418YA"

# Create Layout
layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=50, r=50, b=50, t=50),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview",
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="light",
        center=dict(lon=2.35, lat=48.86),
        zoom=4.5,
    ),
)

# Create app layout
app.layout = html.Div(
    [
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [

                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Demandes de valeurs foncières",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "Overview", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("Pour plus d'info", id="learn-more-button"),
                            href="https://plot.ly/dash/pricing/",
                        )
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            "Filtré par année (or select range in histogram):",
                            className="control_label",
                        ),
                        dcc.RangeSlider(
                            id="year_slider",
                            min=2015,
                            max=2019,
                            value=[2018, 2019],
                            className="dcc_control",
                        ),
                        html.P("Filtré par type de local", className="control_label"),
                        dcc.Dropdown(
                            id="type_locals",
                            options=type_locals_options,
                            multi=True,
                            value=list(TYPE_LOCALS.values()),
                            className="dcc_control",
                        ),
                        html.P("Filter by nature de mutation:", className="control_label"),
                        dcc.Dropdown(
                            id="nature_mutations",
                            options=nature_mutation_options,
                            multi=True,
                            value=list(NATURE_MUTATIONS.values()),
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.H6(id="val_fonciere_text"), html.P("Valeurs fonciers")],
                                    id="val_fonciere",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="surfaceText"), html.P("Surface terrain (m²)")],
                                    id="surfaceTerrain",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="bienText"), html.P("Nombre de bien")],
                                    id="nombreBien",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="pieceText"), html.P("Nombre de Pieces")],
                                    id="nombrePieces",
                                    className="mini_container",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                        html.Div(
                            [dcc.Graph(id="count_graph", config={
                                'displayModeBar': False
                            })],
                            id="countGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="main_graph")],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="individual_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="pie_graph")],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="aggregate_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


def fitler_dataframe(df, type_locals, nature_mutations, year_slider):
    dff = df[
        df["Type local"].isin(type_locals)
        & df["Nature mutation"].isin(nature_mutations)
        & (df["Date mutation"] > dt.datetime(year_slider[0], 1, 1))
        & (df["Date mutation"] < dt.datetime(year_slider[1], 1, 1))
        ]
    return dff


@app.callback(
    Output("val_fonciere_text", "children"),
    [Input("nature_mutations", "value"),
     Input("type_locals", "value"),
     Input("year_slider", "value")]
)
def update_val_fonicere_text(nature_mutations, type_locals, year_slider):
    df = fitler_dataframe(df_mean_val_fon_per_time, nature_mutations, type_locals, year_slider)
    return int(df['Mean Valeur fonciere'].mean())


@app.callback(
    Output("surfaceText", "children"),
    [Input("nature_mutations", "value"),
     Input("type_locals", "value"),
     Input("year_slider", "value")]
)
def update_surface_text(nature_mutations, type_locals, year_slider):
    df = fitler_dataframe(df_surf_terr_per_local, type_locals, nature_mutations, year_slider)
    return int(df['Median Surface terrain'].mean())


@app.callback(
    Output("bienText", "children"),
    [Input("nature_mutations", "value"),
     Input("type_locals", "value"),
     Input("year_slider", "value")]
)
def update_bien_text(nature_mutations, type_locals, year_slider):
    df = fitler_dataframe(df_count_mutation, type_locals, nature_mutations, year_slider)
    return int(df['Count Nature mutation'].sum())


@app.callback(
    Output("pieceText", "children"),
    [Input("nature_mutations", "value"),
     Input("type_locals", "value"),
     Input("year_slider", "value")]
)
def update_bien_text(nature_mutations, type_locals, year_slider):
    df = fitler_dataframe(df_num_per_pieces, type_locals, nature_mutations, year_slider)
    return int(df['Nombre pieces principales'].mean())


@app.callback(
    Output("count_graph", "figure"),
    [Input("nature_mutations", "value"),
     Input("type_locals", "value"),
     Input("year_slider", "value")]
)
def count_graph(nature_mutations, type_locals, year_slider):
    layout_count = copy.deepcopy(layout)
    df = fitler_dataframe(df_mean_val_fon_per_time, nature_mutations, type_locals, year_slider)
    df.index = df["Date mutation"]
    df = df.resample("m").mean()
    data = [
        dict(
            type="scatter",
            x=df.index,
            y=df["Mean Valeur fonciere"],
            name="Mean Valeur fonciere",
            height=1000,
        ),
    ]
    layout_count["yaxis"] = dict(title="Valeur foncière")
    layout_count["xaxis"] = dict(
        title=dict(text="Date mutation", standoff=50),
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    layout_count['title'] = "Nombre de valeurs foncières par temps: de {} à {}".format(
        year_slider[0], year_slider[1]
    )
    layout_count["showlegend"] = False

    figure = dict(data=data, layout=layout_count)
    return figure


@app.callback(
    Output("individual_graph", "figure"),
    [Input("nature_mutations", "value"),
     Input("type_locals", "value"),
     Input("year_slider", "value")]
)
def main_graph(nature_mutations, type_locals, year_slider):
    layout_individual = copy.deepcopy(layout)
    df = fitler_dataframe(df_surf_terr_per_local, type_locals, nature_mutations, year_slider)
    data = [
        dict(
            type="scatter",
            mode="lines+markers",
            name=type_local,
            x=df[df['Type local'].isin([type_local])].set_index('Date mutation').resample('m').mean().index,
            y=df[df['Type local'].isin([type_local])].set_index('Date mutation').resample('m').mean()[
                'Median Surface terrain'],
            line=dict(shape="spline", smoothing=2, width=1),
            marker=dict(symbol="diamond-open"),
        ) for type_local in type_locals

    ]
    layout_individual['title'] = "Superficie par rapport au Nature de mutation: de {} à {}".format(
        year_slider[0], year_slider[1]
    )
    figure = dict(data=data, layout=layout_individual)
    return figure


@app.callback(Output("main_graph", "figure"),
              [Input("nature_mutations", "value"),
               Input("type_locals", "value"),
               Input("year_slider", "value")])
def map_graph(nature_mutations, type_locals, year_slider):
    layout_map = copy.deepcopy(layout)
    df = fitler_dataframe(df_avg_fon_dep, type_locals, nature_mutations, year_slider)
    df = df.groupby('code').mean()['Mean Valeur fonciere']
    df = pd.DataFrame({'code': df.index, 'valeur': df.values})
    L = len(geo['features'])
    for k in range(L):
        geo['features'][k]['id'] = f'{k}'
    pl_deep = [[0.0, 'rgb(253, 253, 204)'],
               [0.1, 'rgb(201, 235, 177)'],
               [0.2, 'rgb(145, 216, 163)'],
               [0.3, 'rgb(102, 194, 163)'],
               [0.4, 'rgb(81, 168, 162)'],
               [0.5, 'rgb(72, 141, 157)'],
               [0.6, 'rgb(64, 117, 152)'],
               [0.7, 'rgb(61, 90, 146)'],
               [0.8, 'rgb(65, 64, 123)'],
               [0.9, 'rgb(55, 44, 80)'],
               [1.0, 'rgb(39, 26, 44)']]
    data = [dict(type="choroplethmapbox", locations=[geo['features'][k]['id'] for k in range(L)], z=df.valeur,
                 colorscale=pl_deep,
                 geojson=geo,
                 marker_opacity=0.5, marker_line_width=0)]
    layout_map['title'] = "Map visualisation: de {} à {}".format(
        year_slider[0], year_slider[1]
    )
    figure = dict(data=data, layout=layout_map)
    return figure


@app.callback(Output("aggregate_graph", "figure"), [
    Input("nature_mutations", "value"),
    Input("type_locals", "value"),
    Input("year_slider", "value")
])
def aggregate_graph(nature_mutations, type_locals, year_slider):
    layout_bar = copy.deepcopy(layout)
    df = fitler_dataframe(df_num_per_pieces, type_locals, nature_mutations, year_slider)
    df = df.groupby('Nombre pieces principales').mean()['Count Nombre Pieces']
    data = [
        dict(
            type="bar",
            x=df[df.index < 10].index,
            y=df.values,
            colors='rgb(253, 253, 204)'
        )
    ]
    layout_bar["title"] = f"Nombre de Pieces <10: de {year_slider[0]} à {year_slider[1]}"
    layout_bar["yaxis"] = dict(title="Nombre de pièces")
    layout_bar["xaxis"] = dict(
        title=dict(text="Type de pieces", standoff=50))
    figure = dict(data=data, layout=layout_bar)
    return figure


@app.callback(Output("pie_graph", "figure"), [
    Input("type_locals", "value"),
    Input("year_slider", "value")
])
def pie_graph(type_locals, year_slider):
    layout_pie = copy.deepcopy(layout)
    df = df_count_mutation[
        df_count_mutation["Type local"].isin(type_locals)
        & (df_count_mutation["Date mutation"] > dt.datetime(year_slider[0], 1, 1))
        & (df_count_mutation["Date mutation"] < dt.datetime(year_slider[1], 1, 1))
        ]
    df = df['Nature mutation'].value_counts()
    data = [
        dict(
            type="pie",
            labels=list(NATURE_MUTATIONS.values()),
            values=df.values,
            name="Nombre de Biens",
            text=[
                "Total Vente",
                "Total Echange",
                "Total Vente en l'état futur d'achèvement",
                "Total Adjudication",
                "Total Vente terrain à bâtir",
                "Total Expropriation",
            ],
            hoverinfo="text+value+percent",
            textinfo="label+percent+name",
            hole=0.5,
            marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8", "#fac1e7", "#a9cb95", "#93d8d8"]),
        ),
    ]
    layout_pie["title"] = "Nombre de biens: {} to {}".format(
        year_slider[0], year_slider[1]
    )
    layout_pie["font"] = dict(color="#777777")
    layout_pie["legend"] = dict(
        font=dict(color="#CCCCCC", size="10"), orientation="h", bgcolor="rgba(0,0,0,0)"
    )

    figure = dict(data=data, layout=layout_pie)
    return figure


# Main


if __name__ == "__main__":
    app.run_server(debug=True)
