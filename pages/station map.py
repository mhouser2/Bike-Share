from dash import Dash, dash_table, Input, Output, dcc, html, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash
import re
import os
from dashboard_functions import get_dataframe_redshift


mapboxtoken = os.getenv("mapboxtoken")

description_string = """
This dashboard visualizes the current active bike share stations in the selected, colored and sized by the number of trips either started or ended there. 
Clicking on any station will update the rightmost graph and the table below. 
"""

fig_height = 650

dash.register_page(
    __name__,
    title="Station Map",
    path="/",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)


top_stations_df = get_dataframe_redshift("SELECT * FROM top_station_by_city")


def serve_layout_station_comparison():
    return dbc.Container(
        [
            html.H1("Bike Share Station Map"),
            html.Div(description_string, style=dict(width="50%")),
            html.Hr(),
            dbc.Col(
                dcc.Dropdown(
                    value="Boston",
                    options=[
                        "Boston",
                        "Chicago",
                        "New York City",
                        "San Francisco",
                        "Washington DC",
                    ],
                    id="city-select",
                    clearable=False,
                ),
                width=4,
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="graph-all"), width=6),
                    dbc.Col(dcc.Graph(id="graph-specific"), width=6),
                ]
            ),
            html.Hr(),
            html.Div(id="table"),
            html.Br(),
        ],
        fluid=True,
    )


layout = serve_layout_station_comparison


@dash.callback(
    Output(component_id="graph-specific", component_property="figure"),
    Output(component_id="table", component_property="children"),
    Input(component_id="city-select", component_property="value"),
    Input(component_id="graph-all", component_property="clickData"),
    Input(component_id="graph-specific", component_property="clickData"),
)
def gather_data(city, clickdata, clickdata2):

    most_recent = ctx.triggered_id
    if most_recent == "graph-all":
        clickdata_name = re.split(r" \(\d", clickdata["points"][0]["text"])[0]
    elif most_recent == "graph-specific":
        clickdata_name = re.split(r" \(\d", clickdata2["points"][0]["text"])[0]
    else:
        clickdata_name = top_stations_df[top_stations_df["city"] == city][
            "station_name"
        ].iloc[0]

    query_location = f"""
    SELECT longitude, latitude
    from stations
    where station_name = '{clickdata_name}'"""

    coords = get_dataframe_redshift(query_location).values
    station_long, station_lat = coords[0][0], coords[0][1]

    get_end_stations_query = f"""
            SELECT s.station_name, s.longitude, s.latitude, COUNT(ride_id) number_of_trips, 
            AVG(CASE WHEN  member_casual = 'member' THEN 1.00 ELSE 0.00 END) percent_member,
            PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY t.duration) median_duration
            FROM trips t
            INNER JOIN stations s on t.end_station_id = s.station_id
			INNER JOIN stations s2  on s2.station_id = t.start_station_id
            WHERE s2.station_name = '{clickdata_name}'
            group by s.station_name, s.longitude, s.latitude
            ORDER BY 4 desc
            LIMIT 25
                """

    end_stations_df = get_dataframe_redshift(get_end_stations_query)
    end_stations_df.columns = [
        "station_name",
        "longitude",
        "latitude",
        "Number of Trips",
        "Percent Member",
        "Median Duration",
    ]

    explanation_string = f"""
    The following table summarizes the end stations of trips beginning at the station located at {clickdata_name}.
    Member percent is the percent of rides done by a member to the Bluebike program, as opposed to a customer on a one time trip.
    \n\nBecause the data does not contain the exact route followed, the trip distance metric is the distance "as the crow flies."
    As such, the distance travelled by bike is always larger than found below. Relatedly, the median trip speed will also be lower than described.
    """

    if end_stations_df.empty:
        return None
    end_stations_df["size"] = (
        10
        * (
            end_stations_df["Number of Trips"]
            - end_stations_df["Number of Trips"].min()
        )
        / (
            end_stations_df["Number of Trips"].max()
            - end_stations_df["Number of Trips"].min()
        )
    ) + 10

    end_stations_df["name_trips"] = (
        end_stations_df["station_name"]
        + " ("
        + end_stations_df["Number of Trips"].astype(str)
        + " trips)"
    )

    fig = go.Figure(layout={"height": fig_height})
    fig.add_trace(
        go.Scattermapbox(
            mode="markers",
            lon=end_stations_df["longitude"],
            lat=end_stations_df["latitude"],
            text=end_stations_df["name_trips"],
            hoverinfo="text",
            marker=go.scattermapbox.Marker(
                colorscale="blues",
                size=end_stations_df["size"],
                allowoverlap=False,
                color=end_stations_df["Number of Trips"],
                showscale=True,
            ),
        )
    )

    fig.add_trace(
        go.Scattermapbox(
            name=clickdata_name,
            mode="markers",
            lon=[station_long, station_long],
            lat=[station_lat, station_lat],
            text=clickdata_name,
            hoverinfo="text",
            marker=dict(symbol="marker", size=20),
        )
    )

    fig.update_layout(
        title=f"Top 25 Stations from {clickdata_name}",
        showlegend=False,
        font={"size": 16},
        mapbox=dict(
            accesstoken=mapboxtoken,
            style="dark",
            center=go.layout.mapbox.Center(
                lat=float(station_lat), lon=float(station_long)
            ),
            zoom=12.5,
        ),
    )

    end_stations_df = end_stations_df.drop(
        ["latitude", "longitude", "size", "name_trips"], axis=1
    ).round(2)

    table = dash_table.DataTable(
        data=end_stations_df.to_dict("records"),
        columns=[{"station_name": i, "id": i} for i in end_stations_df.columns],
        sort_action="native",
        style_cell={"textAlign": "left"},
        page_size=10,
    )
    return fig, dbc.Row(
        [
            dbc.Row(html.H4(f"Top 25 stations from {clickdata_name}")),
            dbc.Row(html.Div(explanation_string, style=dict(width="55%"))),
            dbc.Row(html.Br()),
            dbc.Row(dbc.Col(table, width=6)),
        ]
    )


@dash.callback(
    Output(component_id="graph-all", component_property="figure"),
    Input(component_id="city-select", component_property="value"),
)
def main_graph(city):

    query = f"""
        select s.station_name, s.latitude, s.longitude, n_trips 
            from
            stations s
            INNER join
            (
            select start_station_id, count(start_station_id) as n_trips
            from trips group by start_station_id
            ) trip_count_subquery
            on s.station_id=trip_count_subquery.start_station_id
            where city = '{city}'
            ORDER BY n_trips desc
        """
    data = get_dataframe_redshift(query)
    data["n_trips"] = data["n_trips"].fillna(0)

    data["size"] = np.log(data["n_trips"])
    data["name_trips"] = (
        data["station_name"] + " (" + data["n_trips"].astype(str) + " trips)"
    )

    start_long = data[data["n_trips"] == data["n_trips"].max()]["longitude"].values[0]
    start_lat = data[data["n_trips"] == data["n_trips"].max()]["latitude"].values[0]

    fig = go.Figure(
        go.Scattermapbox(
            text=data["name_trips"],
            lat=data["latitude"],
            lon=data["longitude"],
            mode="markers",
            hoverinfo="text",
            marker=go.scattermapbox.Marker(
                colorscale="blues",
                size=data["size"],
                color=data["n_trips"],
                showscale=True,
            ),
        ),
        layout={"height": fig_height},
    )

    fig.update_layout(
        title=f"Top stations in {city}",
        font={"size": 16},
        mapbox=dict(
            accesstoken=mapboxtoken,
            style="dark",
            center=go.layout.mapbox.Center(lat=float(start_lat), lon=float(start_long)),
            zoom=11,
        ),
    )
    return fig
