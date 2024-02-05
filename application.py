import dash
from dash import html, Dash
import dash_bootstrap_components as dbc

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

sidebar = dbc.Nav(
    [
        dbc.NavLink(
            [
                html.Div(page["name"], className="ms-2"),
            ],
            href=page["path"],
            active="exact",
        )
        for page in dash.page_registry.values()
    ],
    vertical=False,
    pills=True,
    className="bg-light",
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div("Bike Share Dashboard"),
                    style={"fontSize": 50, "textAlign": "center"},
                )
            ]
        ),
        dbc.Row([dbc.Col(sidebar, width=4)]),
        html.Hr(),
        dbc.Row([dbc.Col([dash.page_container], width=12)]),
    ],
    fluid=True,
)

if __name__ == "__main__":
    server.run(debug=True)
