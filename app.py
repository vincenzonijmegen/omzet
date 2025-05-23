from sqlalchemy import create_engine
import os

import sqlite3
import pandas as pd
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px

# Database uitlezen
def load_data():
    url = "postgresql://postgres:houhetveilig66%B@db.zpuxihfmvijsuqnhvomu.supabase.co:5432/postgres?sslmode=require"
    engine = create_engine(url)
    df = pd.read_sql("SELECT * FROM sales", engine)
    df["datum"] = pd.to_datetime(df["datum"], dayfirst=True)
    df["tijdstip"] = pd.to_datetime(df["tijdstip"], errors="coerce").dt.time
    df["maand"] = df["datum"].dt.month
    df["maandnaam"] = df["datum"].dt.strftime("%b")
    df["product"] = df["product"].str.strip()
    return df


df = load_data()
df["jaar"] = df["datum"].dt.year

# Categorie mapping
def map_categorie(product):
    mapping = {
        "1 bol": "hoorntje", "2 bollen": "hoorntje", "3 bollen": "hoorntje",
        "Beker 2 smaken": "beker", "Beker 3 smaken": "beker", "Beker 4 smaken": "beker", "Bol in beker": "beker",
        "Extra hoorntje": "hoorntje", "Gluten-/Lactosevrij hoorntje": "overig", "IJsbonbon": "overig",
        "IJswafel": "overig", "ISO-bak": "overig", "ISO-bak medewerker": "overig", "Mega Hoorn": "overig",
        "Proeverij Box": "overig", "Slagroomwafel": "overig",
        "Cadeaubon € 10,": "cadeaubon", "Cadeaubon € 10,=": "cadeaubon", "Cadeaubon € 15,": "cadeaubon",
        "Cadeaubon € 15,=": "cadeaubon", "Cadeaubon € 20,": "cadeaubon", "Cadeaubon € 20,=": "cadeaubon",
        "Cadeaubon € 25,": "cadeaubon", "Cadeaubon € 25,=": "cadeaubon", "Cadeaucard € 5,": "cadeaubon",
        "Cadeaucard € 5,=": "cadeaubon", "Cappuccino": "koffie", "Dubbele Ristretto / Espresso": "koffie",
        "Espresso": "koffie", "Extra bol": "koffie", "Flat White": "koffie", "Frisdrank": "frisdrank",
        "Koffie": "koffie", "Latte Macchiato": "koffie", "Latte Macchiato / Flat White": "koffie",
        "Ristretto": "koffie", "Ristretto / Espresso": "koffie", "Slagroom": "slagroom",
        "Suikervrij 1 smaak": "suikervrij", "Thee": "koffie"
    }
    for key, value in mapping.items():
        if key.lower() in product.lower():
            return value.capitalize()
    return "Overig"

df["type"] = df["product"].apply(map_categorie)

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Omzet Dashboard"

# Omzet per maand per jaar (lijnweergave)
omzet_per_maand = df.copy()
omzet_per_maand["maandnaam"] = omzet_per_maand["datum"].dt.strftime("%b")
omzet_maand_groep = omzet_per_maand.groupby(["jaar", "maandnaam"], observed=True).agg({"verkoopprijs": "sum"}).reset_index()
omzet_maand_groep["maandnaam"] = pd.Categorical(omzet_maand_groep["maandnaam"],
                                                 categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                                                 ordered=True)
omzet_maand_groep.sort_values(["jaar", "maandnaam"], inplace=True)
fig_omzet = px.line(omzet_maand_groep, x="maandnaam", y="verkoopprijs", color="jaar",
                   title="Omzet per maand per jaar", markers=True)

# Tabs-layout
app.layout = html.Div([
    dcc.Tabs(id="tabs", value="tab-overzicht", children=[
        dcc.Tab(label="🎯 Feestdag Zwaartepunt", value="tab-feestdag-zwaartepunt"),
        dcc.Tab(label="📈 Top/Bottom 20", value="tab-topbottom"),
        dcc.Tab(label="⏰ Tijd", value="tab-tijd"),
        dcc.Tab(label="📊 Overzicht", value="tab-overzicht"),
        dcc.Tab(label="🍦 Bollen", value="tab-bollen"),
        dcc.Tab(label="🍧 Bekers vs Hoorntjes", value="tab-bh"),
        dcc.Tab(label="📅 Maandomzet", value="tab-maandomzet"),
        dcc.Tab(label="🏷️ Categorieën", value="tab-categorie"),
        dcc.Tab(label="📤 Upload", value="tab-upload"),
        dcc.Tab(label="🎉 Feestdagen", value="tab-feestdagen")
    ]),
    html.Div(id="tabs-content")
])

# Callback voor tabinhoud
@app.callback(Output("tabs-content", "children"), Input("tabs", "value"))
def render_content(tab):
    if tab == "tab-overzicht":
        overzicht = df.copy()
        overzicht["maandnaam"] = overzicht["datum"].dt.strftime("%B")
        overzicht["maandnaam"] = pd.Categorical(overzicht["maandnaam"],
                                                 categories=["March", "April", "May", "June", "July", "August", "September", "October"],
                                                 ordered=True)
        overzicht_groep = overzicht.groupby(["maandnaam", "jaar"], observed=True)["verkoopprijs"].sum().reset_index()
        overzicht_groep.sort_values(["jaar", "maandnaam"], inplace=True)

        tabel = overzicht_groep.pivot(index="maandnaam", columns="jaar", values="verkoopprijs").fillna(0).astype(int)
        tabel = tabel.loc[~tabel.index.isnull()]
        kleurenschaal = px.colors.sequential.YlGn
        max_waarden = tabel.max(axis=1)
        min_waarden = tabel.min(axis=1)

        def get_bg_color(value, vmin, vmax):
            if vmax == vmin:
                return kleurenschaal[-1]
            index = int((value - vmin) / (vmax - vmin) * (len(kleurenschaal) - 1))
            return kleurenschaal[index]

        def get_text_color(value, vmin, vmax):
            if vmax == vmin:
                return "black"
            index = int((value - vmin) / (vmax - vmin) * (len(kleurenschaal) - 1))
            return "white" if index > len(kleurenschaal) * 0.6 else "black"

        tabel_html = html.Table([
            html.Thead(html.Tr([html.Th("Maand", style={"border": "1px solid black", "padding": "4px"})] + [html.Th(str(col), style={"border": "1px solid black", "padding": "4px"}) for col in tabel.columns])),
            html.Tbody([
                html.Tr([html.Td(maand, style={"border": "1px solid black", "padding": "4px"})] + [html.Td(f"€ {value:,}".replace(",", "."), style={"border": "1px solid black", "padding": "4px", "backgroundColor": get_bg_color(value, min_waarden[maand], max_waarden[maand]), "color": get_text_color(value, min_waarden[maand], max_waarden[maand])}) for value in row])
                for maand, row in tabel.iterrows()
            ])
        ])

        # Bereken kleur per jaar (voor totaaltabel)
        kleurenschaal_totaal = px.colors.sequential.YlGn
        totalen = df.groupby("jaar")["verkoopprijs"].sum()
        vmin, vmax = totalen.min(), totalen.max()

        totaal_tabel = html.Table([
            html.Thead(html.Tr([
                html.Th("Jaar", style={"border": "1px solid black", "padding": "4px"}),
                html.Th("Totaalomzet (€)", style={"border": "1px solid black", "padding": "4px"}),
                html.Th("Gemiddelde dagomzet (€)", style={"border": "1px solid black", "padding": "4px"})
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(str(jaar), style={"border": "1px solid black", "padding": "4px"}),
                    html.Td(f"{int(totaal):,}".replace(",", "."), style={"border": "1px solid black", "padding": "4px", "backgroundColor": get_bg_color(totaal, vmin, vmax), "color": get_text_color(totaal, vmin, vmax)}),
                    html.Td(f"{int(totaal/len(df[df['jaar']==jaar]['datum'].dt.date.unique())):,}".replace(",", "."), style={"border": "1px solid black", "padding": "4px", "backgroundColor": get_bg_color(totaal, vmin, vmax), "color": get_text_color(totaal, vmin, vmax)})
                ]) for jaar, totaal in totalen.items()
            ])
        ])

        # Bereken kleur per jaar (voor totaaltabel)
        kleurenschaal_totaal = px.colors.sequential.YlGn
        totalen = df.groupby("jaar")["verkoopprijs"].sum()
        vmin, vmax = totalen.min(), totalen.max()

        return html.Div([
            dcc.Graph(figure=fig_omzet),
        html.Hr(),
        tabel_html,
        html.Hr(),
        html.H4("Totaalomzet en gemiddelde dagomzet per jaar"),
        totaal_tabel
        ])
    elif tab == "tab-bollen":
            bollen_df = df.copy()
            def extract_bollen(product):
                product = product.lower()
                match = re.search(r"\b(1|2|3)\s*-?\s*(bol|bolletje|bollen|bolletjes)\b", product)
                return match.group(1) if match else "Onbekend"
            bollen_df["bollen"] = bollen_df["product"].apply(extract_bollen)
            df_bollen = bollen_df[bollen_df["bollen"].isin(["1", "2", "3"])]
            bollen_per_jaar = df_bollen.groupby(["jaar", "bollen"], observed=True)["aantal"].sum().reset_index()
            total_per_jaar = df_bollen.groupby("jaar")["aantal"].sum().reset_index().rename(columns={"aantal": "totaal"})
            bollen_per_jaar = bollen_per_jaar.merge(total_per_jaar, on="jaar")
            bollen_per_jaar["percentage"] = (bollen_per_jaar["aantal"] / bollen_per_jaar["totaal"] * 100).round(2)
            fig_bollen = px.bar(bollen_per_jaar, x="jaar", y="percentage", color="bollen", barmode="group",
                        title="% verdeling 1 / 2 / 3 bollen binnen elk jaar",
                        labels={"percentage": "% binnen jaar"}, text="percentage")
            fig_bollen.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            return html.Div([dcc.Graph(figure=fig_bollen)])
    elif tab == "tab-bh":
        bh_df = df[df["type"].isin(["Beker", "Hoorntje"])]
        groep = bh_df.groupby(["jaar", "type"], observed=True)["aantal"].sum().reset_index()
        totaal = bh_df.groupby("jaar")["aantal"].sum().reset_index().rename(columns={"aantal": "totaal"})
        groep = groep.merge(totaal, on="jaar")
        groep["percentage"] = (groep["aantal"] / groep["totaal"] * 100).round(2)
        fig_bh = px.bar(groep, x="jaar", y="percentage", color="type", barmode="group",
                        title="% verhouding Beker vs Hoorntje per jaar", labels={"percentage": "% binnen jaar"},
                        text="percentage")
        fig_bh.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        return html.Div([dcc.Graph(figure=fig_bh)])
    elif tab == "tab-maandomzet":
        maand_omzet = df.groupby(["jaar", "maandnaam"])["verkoopprijs"].sum().reset_index()
        total_jaar_omzet = df.groupby("jaar")["verkoopprijs"].sum().reset_index().rename(columns={"verkoopprijs": "totaal"})
        maand_omzet = maand_omzet.merge(total_jaar_omzet, on="jaar")
        maand_omzet["percentage"] = (maand_omzet["verkoopprijs"] / maand_omzet["totaal"] * 100).round(2)
        maand_omzet["maandnaam"] = pd.Categorical(maand_omzet["maandnaam"],
                                                   categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                                                   ordered=True)
        maand_omzet.sort_values(["jaar", "maandnaam"], inplace=True)

        return html.Div([
            html.Label("Toon maandomzet als:"),
            dcc.Dropdown(
                id="maandweergave-keuze",
                options=[
                    {"label": "% binnen jaar", "value": "percentage"},
                    {"label": "Bedrag in euro", "value": "verkoopprijs"}
                ],
                value="percentage"
            ),
            dcc.Graph(id="maandomzet-weergave")
        ])
    elif tab == "tab-categorie":
        return html.Div([
            html.Label("Selecteer een categorie:"),
            dcc.Dropdown(
                id="categorie-keuze",
                options=[{"label": cat, "value": cat} for cat in sorted(df["type"].unique())],
                value="Beker"
            ),
            dcc.Graph(id="categorie-aantallen-per-jaar")
        ])

    

    elif tab == "tab-tijd":
        return html.Div([
        html.H4("Gemiddeld aantal verkopen per uur per weekdag"),
            dcc.Dropdown(
                id="tijd-maand-dropdown",
                options=[{"label": maand, "value": maand} for maand in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]],
                value=sorted(df["maandnaam"].unique())[0],
                style={"width": "250px", "marginBottom": "10px"}
            ),
            dcc.Dropdown(
                id="tijd-type-dropdown",
                options=[
                    {"label": "Aantal verkopen", "value": "aantal"},
                    {"label": "Omzet (€)", "value": "verkoopprijs"}
                ],
                value="aantal",
                style={"width": "250px", "marginBottom": "10px"}
            ),
            dcc.Graph(id="tijd-uur-weekdag"),
        html.H4("Gemiddeld aantal verkopen per weekdag per uur"),
        dcc.Graph(id="tijd-uur-weekdag-omgekeerd")
        ])

    elif tab == "tab-feestdagen":
        geldige_jaren = sorted(df[df["datum"] <= pd.Timestamp.today()]["jaar"].unique())
        return html.Div([
            html.Label("Selecteer een jaar (of alle):"),
            dcc.Dropdown(
                id="feestdagen-jaar-dropdown",
                options=[
                {"label": "Alle jaren", "value": "alle"},
                
            ] + [{"label": str(j), "value": j} for j in geldige_jaren] + [{"label": str(j), "value": j} for j in geldige_jaren],
                value="alle",
                style={"width": "250px", "marginBottom": "10px"}
            ),
            html.H4("Omzet op feestdagen"),
            dcc.Graph(id="feestdagen-grafiek"),
            html.Hr(),
            html.H4("Gemiddelde omzet op feestdagen"),
            dcc.Graph(id="feestdagen-gemiddelde-grafiek"),
            
        ])

    elif tab == "tab-topbottom":
        dagtotalen = df.groupby("datum")["verkoopprijs"].sum().reset_index()
        top20 = dagtotalen.sort_values("verkoopprijs", ascending=False).head(20)
        bottom20 = dagtotalen.sort_values("verkoopprijs", ascending=True).head(20)

        top_tabel = html.Table([
            html.Thead(html.Tr([html.Th("Top 20 Dagomzet"), html.Th("Omzet (€)")])),
            html.Tbody([
                html.Tr([
                    html.Td(row["datum"].strftime("%Y-%m-%d")),
                    html.Td(f"€ {int(row['verkoopprijs']):,}".replace(",", "."))
                ]) for _, row in top20.iterrows()
            ])
        ])

        bottom_tabel = html.Table([
            html.Thead(html.Tr([html.Th("Bottom 20 Dagomzet"), html.Th("Omzet (€)")])),
            html.Tbody([
                html.Tr([
                    html.Td(row["datum"].strftime("%Y-%m-%d")),
                    html.Td(f"€ {int(row['verkoopprijs']):,}".replace(",", "."))
                ]) for _, row in bottom20.iterrows()
            ])
        ])

        return html.Div([
            top_tabel,
            html.Hr(),
            bottom_tabel
        ])

    elif tab == "tab-feestdag-zwaartepunt":
        feestdagen_excel = pd.read_excel("feestdagen 2021-2035.xlsx")
        feestdagen_excel["datum"] = pd.to_datetime(feestdagen_excel["datum"])

        return html.Div([
            html.Label("Selecteer een feestdag:"),
            dcc.Dropdown(
                id="feestdag-zwaartepunt-dropdown",
                options=[{"label": f"{row['feestdag']} ({row['datum'].strftime('%d-%m-%Y')})", "value": row['datum'].strftime("%Y-%m-%d")} for _, row in feestdagen_excel.iterrows()],
                value=None,
                style={"width": "400px", "marginBottom": "10px"}
            ),
            dcc.Graph(id="feestdag-zwaartepunt-grafiek")
        ])

    elif tab == "tab-upload":
        return html.Div([
            html.H3("Upload nieuwe omzet voor een jaar"),
            dcc.Upload(
                id="upload-bestand",
                children=html.Button("Bestand selecteren"),
                style={"marginBottom": "10px"}
            ),
            dcc.Input(id="jaar-input", type="number", placeholder="Jaar", debounce=True, style={"marginRight": "10px"}),
            html.Button("Upload en vervang", id="upload-button"),
            html.Div(id="upload-feedback")
        ])

@app.callback(Output("categorie-aantallen-per-jaar", "figure"), Input("categorie-keuze", "value"))
def update_categorie_grafiek(selected):
    filtered = df[df["type"] == selected]
    grouped = filtered.groupby("jaar")["aantal"].sum().reset_index()
    fig = px.bar(grouped, x="jaar", y="aantal", text="aantal",
                 title=f"Aantal verkopen per jaar voor categorie: {selected}",
                 labels={"aantal": "Aantal verkopen"})
    return fig






@app.callback(Output("maandomzet-weergave", "figure"), Input("maandweergave-keuze", "value"))
def update_maandgrafiek(weergave):
    maand_omzet = df.groupby(["jaar", "maandnaam"])["verkoopprijs"].sum().reset_index()
    total_jaar_omzet = df.groupby("jaar")["verkoopprijs"].sum().reset_index().rename(columns={"verkoopprijs": "totaal"})
    maand_omzet = maand_omzet.merge(total_jaar_omzet, on="jaar")
    maand_omzet["percentage"] = (maand_omzet["verkoopprijs"] / maand_omzet["totaal"] * 100).round(2)
    maand_omzet["maandnaam"] = pd.Categorical(maand_omzet["maandnaam"],
                                               categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                                               ordered=True)
    maand_omzet.sort_values(["jaar", "maandnaam"], inplace=True)
    y_as = weergave
    titel = "% maandomzet binnen jaaromzet" if y_as == "percentage" else "Maandomzet in euro's"
    tekstkolom = y_as
    texttemplate = '%{text:.0f}' if y_as == "verkoopprijs" else '%{text}'
    fig = px.bar(maand_omzet, x="jaar", y=y_as, color="maandnaam", barmode="group",
                 title=titel, labels={y_as: y_as}, text=tekstkolom)
    fig.update_traces(texttemplate=texttemplate, textposition="outside")
    return fig


@app.callback(
    Output("upload-feedback", "children"),
    Input("upload-button", "n_clicks"),
    State("upload-bestand", "contents"),
    State("upload-bestand", "filename"),
    State("jaar-input", "value")
)
def upload_en_vervang(n_clicks, contents, filename, jaar):
    if n_clicks is not None and contents and jaar:
        import io, base64
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df_new = pd.read_csv(io.StringIO(decoded.decode('utf-8-sig')), sep=";")
            verplichte_kolommen = {"datum", "tijdstip", "product", "aantal", "verkoopprijs"}
            if not verplichte_kolommen.issubset(set(df_new.columns.str.strip().str.lower())):
                return "❌ Bestand mist verplichte kolommen: datum, tijdstip, product, aantal, verkoopprijs."

            df_new = df_new.dropna(subset=["datum", "tijdstip", "product", "aantal", "verkoopprijs"])
            df_new = df_new[df_new["datum"].astype(str).str.strip() != "0"]
            df_new["verkoopprijs"] = df_new["verkoopprijs"].astype(str).str.replace(",", ".").astype(float)
            df_new["aantal"] = pd.to_numeric(df_new["aantal"], errors="coerce").fillna(0).astype(int)
            df_new["jaar"] = jaar

            conn = sqlite3.connect("sales_data.db")
            cur = conn.cursor()
            cur.execute("DELETE FROM sales WHERE jaar = ?", (jaar,))
            conn.commit()
            df_new.to_sql("sales", conn, if_exists="append", index=False)
            conn.close()
            return f"✅ Omzetdata voor {jaar} succesvol vervangen. ({len(df_new)} rijen toegevoegd)"
        except Exception as e:
            return f"❌ Fout bij verwerken bestand: {str(e)}"
    if not contents:
        return "⚠️ Geen bestand geselecteerd."
    if not jaar:
        return "⚠️ Geen jaartal opgegeven."
    return ""





@app.callback(
    Output("tijd-uur-weekdag", "figure"),
    Input("tijd-maand-dropdown", "value"),
    Input("tijd-type-dropdown", "value")
)
def update_tijd_uur_weekdag(maand, metric):
    df_tijd = df[df["maandnaam"] == maand].copy()
    df_tijd["tijdstip"] = pd.to_datetime(df_tijd["tijdstip"], errors="coerce", infer_datetime_format=True)
    df_tijd["uur"] = pd.Categorical(
        df_tijd["tijdstip"].dt.hour,
        categories=list(range(12, 22)),
        ordered=True
    )
    df_tijd["weekdag"] = pd.Categorical(df_tijd["datum"].dt.day_name(), categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], ordered=True)
    df_tijd = df_tijd[df_tijd["uur"].isin(list(range(12, 22)))]

    dagen_per_weekdag = df_tijd.groupby("weekdag", observed=True)["datum"].nunique().reset_index().rename(columns={"datum": "dagen"})
    totaal_per_blok = df_tijd.groupby(["weekdag", "uur"], observed=True)[metric].sum().reset_index()
    merged = totaal_per_blok.merge(dagen_per_weekdag, on="weekdag")
    merged["gemiddeld"] = (merged[metric] / merged["dagen"]).round(2)

    fig = px.bar(
        merged,
        x="uur",
        y="gemiddeld",
        color="weekdag",
        barmode="group",
        title=f"Gemiddelde {'verkopen' if metric == 'aantal' else 'omzet'} per uur per weekdag ({maand})",
        labels={"uur": "Uur", "gemiddeld": "Gem. aantal" if metric == 'aantal' else "Gem. omzet (€)", "weekdag": "Weekdag"},
        text_auto=".1f"
    )
    fig.update_traces(hovertemplate='%{y:.0f}' if metric == "verkoopprijs" else '%{y:.2f}')
    return fig


@app.callback(
    Output("tijd-uur-weekdag-omgekeerd", "figure"),
    Input("tijd-maand-dropdown", "value"),
    Input("tijd-type-dropdown", "value")
)
def update_tijd_weekdag_uur(maand, metric):
    df_tijd = df[df["maandnaam"] == maand].copy()
    df_tijd["tijdstip"] = pd.to_datetime(df_tijd["tijdstip"], errors="coerce", infer_datetime_format=True)
    df_tijd["uur"] = pd.Categorical(
        df_tijd["tijdstip"].dt.hour,
        categories=list(range(12, 22)),
        ordered=True
    )
    df_tijd["weekdag"] = pd.Categorical(
        df_tijd["datum"].dt.day_name(),
        categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        ordered=True
    )
    df_tijd = df_tijd[df_tijd["uur"].isin(list(range(12, 22)))]

    dagen_per_combi = df_tijd.groupby(["weekdag", "uur"], observed=True)["datum"].nunique().reset_index().rename(columns={"datum": "dagen"})
    totaal_per_combi = df_tijd.groupby(["weekdag", "uur"], observed=True)[metric].sum().reset_index()
    merged = totaal_per_combi.merge(dagen_per_combi, on=["weekdag", "uur"])
    merged["gemiddeld"] = (merged[metric] / merged["dagen"]).round(2)

    fig = px.bar(
        merged,
        x="weekdag",
        y="gemiddeld",
        color="uur",
        barmode="group",
        title=f"Gemiddelde {'verkopen' if metric == 'aantal' else 'omzet'} per weekdag per uur ({maand})",
        labels={"weekdag": "Weekdag", "gemiddeld": "Gem. aantal" if metric == 'aantal' else "Gem. omzet (€)", "uur": "Uur"},
        text_auto=".1f"
    )
    fig.update_traces(hovertemplate='%{y:.0f}' if metric == "verkoopprijs" else '%{y:.2f}')
    return fig

def eerste_feestdag(nl_feest, naam):
    dagen = list(nl_feest.get_named(naam))
    return dagen[0] if dagen else None

@app.callback(
    Output("feestdagen-grafiek", "figure"),
    Input("tabs", "value"),
    Input("feestdagen-jaar-dropdown", "value")
)
def update_feestdagen_grafiek(tab, geselecteerd_jaar):
    if tab != "tab-feestdagen":
        return dash.no_update

    import datetime
    today = datetime.date.today()
    huidig_jaar = today.year

    feestdagen_excel = pd.read_excel("feestdagen 2021-2035.xlsx")
    feestdagen_excel["datum"] = pd.to_datetime(feestdagen_excel["datum"])
    feestdagen_excel["jaar"] = feestdagen_excel["datum"].dt.year

    geldige_jaren = sorted(feestdagen_excel[feestdagen_excel["datum"] <= pd.Timestamp(today)]["jaar"].unique())

    feestdagen_resultaat = []
    for _, row in feestdagen_excel.iterrows():
        dag = row["datum"]
        naam = row["feestdag"]
        jaar = row["jaar"]
        if jaar in geldige_jaren and geselecteerd_jaar != "Gemiddelde" and (geselecteerd_jaar == 'alle' or jaar == geselecteerd_jaar):
            dag_omzet = df[df["datum"] == dag]["verkoopprijs"].sum()
            feestdagen_resultaat.append({"feestdag": naam, "jaar": jaar, "omzet": dag_omzet})

    feestdagen_df = pd.DataFrame(feestdagen_resultaat)
    
    
    feestdagen_df["feestdag"] = pd.Categorical(
        feestdagen_df["feestdag"],
        categories=[
            "Goede Vrijdag",
            "1e Paasdag",
            "2e Paasdag",
            "meivakantie dag 1",
            "meivakantie dag 2",
            "meivakantie dag 3",
            "meivakantie dag 4",
            "meivakantie dag 5",
            "meivakantie dag 6",
            "meivakantie dag 7",
            "meivakantie dag 8",
            "meivakantie dag 9",
            "Bevrijdingsdag",
            "Moederdag",
            "Hemelvaartsdag",
            "1e Pinksterdag",
            "2e Pinksterdag",
            "Vaderdag",
            "Zomerfeesten dag 1",
            "Zomerfeesten dag 2",
            "Zomerfeesten dag 3",
            "Zomerfeesten dag 4",
            "Zomerfeesten dag 5",
            "Zomerfeesten dag 6",
            "Zomerfeesten dag 7"
        ],
        ordered=True
    )
    feestdagen_df = feestdagen_df.sort_values("feestdag")
    feestdagen_df["jaar"] = pd.Categorical(
        feestdagen_df["jaar"],
        categories=sorted(feestdagen_df["jaar"].loc[feestdagen_df["omzet"] > 0].unique()),
        ordered=True
    )
    feestdagen_df = feestdagen_df.sort_values(by=["feestdag", "jaar"])
    fig = px.bar(feestdagen_df, x="feestdag", y="omzet", color="jaar", barmode="group", text_auto=".0f")
    return fig

@app.callback(
    Output("feestdagen-gemiddelde-grafiek", "figure"),
    Input("tabs", "value")
)
def update_feestdagen_gemiddelde_grafiek(tab):
    if tab != "tab-feestdagen":
        return dash.no_update

    feestdagen_excel = pd.read_excel("feestdagen 2021-2035.xlsx")
    feestdagen_excel["datum"] = pd.to_datetime(feestdagen_excel["datum"])
    feestdagen_excel["jaar"] = feestdagen_excel["datum"].dt.year

    feestdagen_resultaat = []
    for _, row in feestdagen_excel.iterrows():
        dag = row["datum"]
        naam = row["feestdag"]
        omzet = df[df["datum"] == dag]["verkoopprijs"].sum()
        feestdagen_resultaat.append({"feestdag": naam, "omzet": omzet})

    feestdagen_df = pd.DataFrame(feestdagen_resultaat)
    feestdagen_df = feestdagen_df[feestdagen_df["omzet"] > 0]
    gemiddelde_df = feestdagen_df.groupby("feestdag", observed=True)["omzet"].mean().reset_index()

    gemiddelde_df["feestdag"] = pd.Categorical(
        gemiddelde_df["feestdag"],
        categories=[
            "Goede Vrijdag",
            "1e Paasdag",
            "2e Paasdag",
            "meivakantie dag 1",
            "meivakantie dag 2",
            "meivakantie dag 3",
            "meivakantie dag 4",
            "meivakantie dag 5",
            "meivakantie dag 6",
            "meivakantie dag 7",
            "meivakantie dag 8",
            "meivakantie dag 9",
            "Bevrijdingsdag",
            "Moederdag",
            "Hemelvaartsdag",
            "1e Pinksterdag",
            "2e Pinksterdag",
            "Vaderdag",
            "Zomerfeesten dag 1",
            "Zomerfeesten dag 2",
            "Zomerfeesten dag 3",
            "Zomerfeesten dag 4",
            "Zomerfeesten dag 5",
            "Zomerfeesten dag 6",
            "Zomerfeesten dag 7"
        ],
        ordered=True
    )
    gemiddelde_df = gemiddelde_df.sort_values("feestdag")
    fig = px.bar(gemiddelde_df, x="feestdag", y="omzet", text_auto=".0f")
    return fig
@app.callback(
    Output("feestdag-zwaartepunt-grafiek", "figure"),
    Input("feestdag-zwaartepunt-dropdown", "value")
)
def update_feestdag_zwaartepunt(datum_str):
    import plotly.graph_objects as go

    if not datum_str:
        return go.Figure()

    datum = pd.to_datetime(datum_str)
    df_dag = df[df["datum"] == datum].copy()
    df_dag["tijdstip"] = pd.to_datetime(df_dag["tijdstip"], errors="coerce")
    df_dag["uur"] = df_dag["tijdstip"].dt.hour
    df_dag = df_dag[df_dag["uur"].between(12, 21)]

    omzet_per_uur = df_dag.groupby("uur")["verkoopprijs"].sum().reset_index()
    if omzet_per_uur.empty:
        return go.Figure()

    max_uur = omzet_per_uur.loc[omzet_per_uur["verkoopprijs"].idxmax(), "uur"]

    fig = px.bar(omzet_per_uur, x="uur", y="verkoopprijs", text_auto=".0f")
    fig.update_layout(title=f"Omzet per uur op {datum.strftime('%d-%m-%Y')} (hoogste omzet om {max_uur}:00)", xaxis_title="Uur", yaxis_title="Omzet (€)")
    fig.update_traces(marker_color=["orange" if uur == max_uur else "steelblue" for uur in omzet_per_uur["uur"]])

    return fig



import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)