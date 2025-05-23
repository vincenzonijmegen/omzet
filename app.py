import dash
from dash import html
import os

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Hallo vanaf Render!"),
    html.P("Dit is een voorbeeld van een Dash-dashboard.")
])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run_server(host="0.0.0.0", port=port)
