from dash import Dash, dash_table, Input, Output, dcc, html, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import dash
import plotly.express as px
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dashboard_functions import get_dataframe_redshift


database_url = os.getenv("database_url_bbb")
mapboxtoken = os.getenv("mapboxtoken")

dash.register_page(
    __name__,
    title="Visualizations",
    path="/Visualizations",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)


def serve_layout_visualizations():
    return dbc.Container(
        [
            html.H1("Bike Share Visualizations"),
            html.Hr(),
            dbc.Row(
                [dbc.Col(dcc.Graph(id="n-trips-graph", figure=fig_n_trips), width=10)]
            ),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            id="n-trips-graph-subscribers", figure=fig_n_trips_subs
                        ),
                        width=10,
                    )
                ]
            ),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(id="start-hour", figure=fig_hours),
                        width=10,
                    ),
                    dbc.Row(
                        [
                            dbc.Col(dcc.Graph(id="days", figure=fig_days), width=10),
                        ]
                    ),
                ]
            ),
        ],
        fluid=True,
    )


layout = serve_layout_visualizations


query_get_n_trips = f"""
            SELECT  * from city_rides order by  2, 1
            """
dff_n_trips = get_dataframe_redshift(query_get_n_trips)
dff_n_trips.columns = ['Month', 'City', 'Number of Trips']
fig_n_trips = px.line(dff_n_trips, x="Month", y="Number of Trips", facet_col="City")
fig_n_trips.update_layout(
    title={"text": "Number of Trips by City and Month", "font": {"size": 30}}
)


query_subscriber_trips = f"""
        SELECT  * from city_subscriber_trips_cleaned
        order by 2,3, 1 desc
        """
dff_n_trips_subs = get_dataframe_redshift(query_subscriber_trips)
dff_n_trips_subs.columns = ['Date', 'Membership Status', 'City', 'Number of Trips', "Percent of Trips"]
dff_n_trips_subs
fig_n_trips_subs = px.line(
    dff_n_trips_subs,
    x="Date",
    y="Percent of Trips",
    facet_col="City",
    color="Membership Status",
)
fig_n_trips_subs.update_yaxes(matches=None)
fig_n_trips_subs.update_layout(
    title={
        "text": "Percent of Trips by City and Member Status",
        "font": {"size": 30},
    }
)


query_hours = f"""
        SELECT * FROM city_start_hours ORDER BY 2, 1
        """
dff_hours = get_dataframe_redshift(query_hours)
dff_hours.columns = ['Start Hour', 'City', 'Number of Trips']
fig_hours = px.line(dff_hours, x="Start Hour", y="Number of Trips", facet_col="City")
fig_hours.update_yaxes(matches=None)
fig_hours.update_layout(
    title={"text": "Number of Trips Started by Hour", "font": {"size": 30}}
)


query_dow = f"""
SELECT * FROM city_day_of_week
ORDER BY 2, 1
        """
dff_dow = get_dataframe_redshift(query_dow)
dff_dow.columns = ['Day of Week', 'City', 'Number of Trips']
fig_days = px.bar(dff_dow, x="Day of Week", y="Number of Trips", facet_col="City")
fig_days.update_yaxes(matches=None)
fig_days.update_layout(
    title={"text": "Number of Trips Started by Day", "font": {"size": 30}},
)
