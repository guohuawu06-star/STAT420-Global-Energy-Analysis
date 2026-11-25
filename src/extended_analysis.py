"""Geographic and historical extensions of the fixed OWID analysis."""

import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import META, RENEWABLE, TOTAL

MAP_START, MAP_END = 1965, 2024
OUTSIDE, MISSING, REPORTED = "Outside source grid", "Missing", "Reported"
STATUS_ORDER = [OUTSIDE, MISSING, REPORTED]
STATUS_COLORS = ["#eeeae3", "#8092a5", "#087f71"]
MAP_FIELDS = {
    TOTAL: "Total supply (TWh)", RENEWABLE: "Renewable share (%)",
    "coal_energy_share_pct": "Coal (%)", "oil_energy_share_pct": "Oil (%)",
    "gas_energy_share_pct": "Natural gas (%)", "fossil_fuels_energy_share_pct": "Fossil fuels (%)",
    "nuclear_energy_share_pct": "Nuclear (%)",
}
HISTORICAL_SOURCES = {
    "Coal": "coal_energy_twh", "Oil": "oil_energy_twh", "Natural gas": "gas_energy_twh",
    "Nuclear": "nuclear_energy_twh", "Hydropower": "hydro_energy_twh", "Wind": "wind_energy_twh",
    "Solar": "solar_energy_twh", "Biofuels": "biofuels_energy_twh",
    "Other renewables": "other_renewables_including_bioenergy_energy_twh",
}
HISTORICAL_COLORS = ["#46505a", "#a25231", "#b79050", "#835687", "#236d9b",
                     "#17766f", "#e0ad2f", "#829c43", "#a76b95"]
RENEWABLE_TOLERANCE_TWH = 0.001


def geographic_panel(geography, observations, first_year, last_year):
    """Use source rows to define whether a location-year can be assessed."""
    iso = geography.loc[geography.geography_type.eq("iso_coded"), ["geo_id", "name", "iso_code"]]
    facts = observations.loc[
        observations.geo_id.isin(iso.geo_id) & observations.year.between(first_year, last_year)
    ]
    profiles = facts.pivot(index=["geo_id", "year"], columns="indicator_id", values="value")
    universe = pd.MultiIndex.from_product(
        [iso.geo_id, range(first_year, last_year + 1)], names=["geo_id", "year"]
    )
    panel = profiles.reindex(index=universe, columns=list(MAP_FIELDS))
    panel["source_row"] = universe.isin(profiles.index)
    panel["status"] = np.select(
        [panel[TOTAL].notna(), panel.source_row], [REPORTED, MISSING], default=OUTSIDE
    )
    return panel.reset_index().merge(iso, on="geo_id", validate="many_to_one")


def geographic_coverage(panel):
    return panel.assign(
        total_reported=panel[TOTAL].notna(), renewable_reported=panel[RENEWABLE].notna(),
        total_missing=panel.status.eq(MISSING), outside_source_grid=panel.status.eq(OUTSIDE),
    ).groupby("year", as_index=False)[
        ["source_row", "total_reported", "renewable_reported", "total_missing", "outside_source_grid"]
    ].sum()


def map_codes():
    metadata = json.loads((META / "plotly_world_50m.json").read_text(encoding="utf-8"))
    return set(metadata["iso_codes"])


def geographic_figures(panel, coverage):
    visible = panel.loc[panel.iso_code.isin(map_codes()) & panel.year.between(MAP_START, MAP_END)]
    visible = visible.sort_values(["year", "iso_code"]).rename(columns=MAP_FIELDS)
    visible = visible.assign(frame=visible.year.astype(str))
    shares = visible.dropna(subset=[MAP_FIELDS[RENEWABLE]])
    base = dict(locations="iso_code", locationmode="ISO-3", hover_name="name",
                projection="natural earth", template="plotly_white")
    years = [str(year) for year in range(MAP_START, MAP_END + 1)]
    hover = {label: ":,.2f" for label in MAP_FIELDS.values()}
    hover.update(iso_code=False, frame=False, year=True)
    latest = px.choropleth(shares.loc[shares.year.eq(MAP_END)], **base, hover_data=hover,
                           color=MAP_FIELDS[RENEWABLE], range_color=(0, 100),
                           color_continuous_scale="Viridis",
                           title=f"Reported renewable share by ISO-coded location, {MAP_END}")
    animated = px.choropleth(shares, **base, hover_data=hover, color=MAP_FIELDS[RENEWABLE],
                             range_color=(0, 100), color_continuous_scale="Viridis",
                             animation_frame="frame", category_orders={"frame": years},
                             title=f"Reported renewable share, {MAP_START}–{MAP_END}")

    visible["status_code"] = visible.status.map({label: i for i, label in enumerate(STATUS_ORDER)})
    availability = px.choropleth(
        visible, **base, color="status_code", range_color=(-0.5, 2.5),
        color_continuous_scale=[(end / 3, STATUS_COLORS[i]) for i in range(3) for end in (i, i + 1)],
        hover_data={"iso_code": False, "frame": False, "year": True, "status_code": False,
                    "status": True, MAP_FIELDS[TOTAL]: ":,.1f"},
        animation_frame="frame", category_orders={"frame": years},
        title=f"Total energy supply coverage on current boundaries, {MAP_START}–{MAP_END}",
    )
    availability.update_coloraxes(colorbar=dict(
        title="OWID source status", tickmode="array", tickvals=[0, 1, 2], ticktext=STATUS_ORDER, len=0.68
    ))
    for figure in (latest, animated, availability):
        figure.update_geos(resolution=50, showframe=False, showland=True, landcolor="#f6f6f6",
                           showcountries=True, countrycolor="#a9aeb6", showcoastlines=False)
        figure.update_layout(height=530, margin=dict(l=15, r=25, t=65, b=30))
    for figure in (animated, availability):
        figure.layout.sliders[0].currentvalue.prefix = "Year "

    counts = coverage.loc[coverage.year.between(MAP_START, MAP_END)].rename(columns={
        "total_reported": "Total energy supply", "renewable_reported": "Renewable share",
    })
    trend = px.line(counts, x="year", y=["Total energy supply", "Renewable share"], markers=True,
                    labels={"year": "Year", "value": "ISO-coded locations", "variable": "Reported indicator"},
                    title="Locations with reported values", template="plotly_white")
    trend.update_layout(hovermode="x unified")
    return latest, animated, availability, trend


def historical_values(raw):
    world = raw.loc[raw.country.eq("World")].set_index("year").sort_index()
    if not world.index.is_unique:
        raise ValueError("Expected one World observation row for each year.")
    sources = list(HISTORICAL_SOURCES.values())
    renewables = sources[4:]
    check = world[[TOTAL, "renewables_energy_twh", *sources]].copy()
    check["component_sum_twh"] = check[sources].sum(axis=1, min_count=len(sources))
    check["renewable_sum_twh"] = check[renewables].sum(axis=1, min_count=len(renewables))
    check["renewable_difference_twh"] = check["renewable_sum_twh"] - check["renewables_energy_twh"]
    check["total_difference_twh"] = check["component_sum_twh"] - check[TOTAL]
    return check


def historical_figures(history):
    observed = history.dropna(subset=["component_sum_twh", TOTAL])

    def traces(data):
        bars = [
            go.Bar(x=data.index.to_list(), y=data[column].to_list(), name=label, width=0.86, marker_color=color,
                   hovertemplate="%{y:,.1f} TWh")
            for (label, column), color in zip(HISTORICAL_SOURCES.items(), HISTORICAL_COLORS)
        ]
        return bars + [go.Scatter(x=data.index.to_list(), y=data[TOTAL].to_list(), mode="markers",
                                  marker=dict(size=5, color="#172331"), name="Published total",
                                  hovertemplate="%{y:,.1f} TWh")]

    layout = go.Layout(
        title="World energy supply by source in observed years", template="plotly_white",
        barmode="stack", hovermode="x unified", xaxis_title="Year", yaxis_title="Energy supply (TWh)",
        yaxis=dict(range=[0, max(observed[TOTAL].max(), observed.component_sum_twh.max()) * 1.05]),
        height=610, legend_title="OWID series",
    )
    full = go.Figure(data=traces(observed), layout=layout)
    full.update_xaxes(rangeslider_visible=True)
    frames = [go.Frame(name=str(year), data=traces(observed.loc[:year])) for year in observed.index]
    animated = go.Figure(data=traces(observed.iloc[:1]), layout=layout, frames=frames)
    animated.update_xaxes(range=[observed.index.min() - 2, observed.index.max() + 2])
    animated.update_layout(
        sliders=[dict(currentvalue={"prefix": "Observed year "}, pad={"t": 35}, steps=[
            dict(method="animate", label=frame.name,
                 args=[[frame.name], dict(mode="immediate", frame=dict(duration=0, redraw=True),
                                         transition=dict(duration=0))]) for frame in frames
        ])],
        updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.15, buttons=[
            dict(label="Play", method="animate",
                 args=[None, dict(fromcurrent=True, frame=dict(duration=220, redraw=True),
                                  transition=dict(duration=0))]),
            dict(label="Pause", method="animate",
                 args=[[None], dict(mode="immediate", frame=dict(duration=0, redraw=False))]),
        ])],
        margin=dict(b=125),
    )
    return full, animated
