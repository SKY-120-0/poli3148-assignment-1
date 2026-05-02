from __future__ import annotations

import base64
import json
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots


project_dir = Path(__file__).resolve().parents[1]
processed_path = project_dir / "Data_Processed" / "ACLED_Kyrgyzstan_Tajikistan_2018-2025_processed.csv"
output_dir = project_dir / "Output"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "Interactive_Data_Driven_Analysis_Report_Revised.html"
_upload_candidates = (
    project_dir / "Assets" / "davies_reference.png",
    Path(__file__).resolve().parent / "davies_reference.png",
    Path(
        r"C:\Users\user\.cursor\projects\g-My-Drive-POLI-3148-Assignment-1\assets\c__Users_user_AppData_Roaming_Cursor_User_workspaceStorage_6a84a9e22910e787b90e57e97bbe80a5_images_640-a0376a77-120e-4869-b834-58144a37482a.png"
    ),
)
uploaded_image_path = next((p for p in _upload_candidates if p.exists()), _upload_candidates[0])

acled = pd.read_csv(processed_path)
acled["event_date"] = pd.to_datetime(acled["event_date"], errors="coerce")
acled = acled.dropna(subset=["event_date"]).copy()
acled = acled[(acled["event_date"] >= "2018-01-01") & (acled["event_date"] <= "2025-12-31")].copy()
acled["fatalities"] = pd.to_numeric(acled.get("fatalities", 0), errors="coerce").fillna(0)
acled["year"] = acled["event_date"].dt.year.astype(int)
acled["event_month"] = acled["event_date"].dt.to_period("M").dt.to_timestamp()

month_index = pd.date_range("2018-01-01", "2025-12-01", freq="MS")
monthly = (
    acled.groupby("event_month")
    .agg(events=("event_id_cnty", "count"), fatalities=("fatalities", "sum"))
    .reindex(month_index, fill_value=0)
    .rename_axis("event_month")
    .reset_index()
)
monthly["year"] = monthly["event_month"].dt.year


def fig_html(fig: go.Figure, include_plotlyjs: bool | str = False, config: dict | None = None) -> str:
    base_config = {"displaylogo": False, "responsive": True}
    if config:
        base_config.update(config)
    return plot(fig, include_plotlyjs=include_plotlyjs, output_type="div", config=base_config)


def table_html(df: pd.DataFrame) -> str:
    return df.to_html(index=False, classes="data-table", border=0, float_format=lambda x: f"{x:.2f}")


event_type_order = [
    "Battles",
    "Explosions/Remote violence",
    "Violence against civilians",
    "Riots",
    "Protests",
    "Strategic developments",
]
event_type_colors = {
    "Battles": "#d62728",
    "Explosions/Remote violence": "#ff7f0e",
    "Violence against civilians": "#9467bd",
    "Riots": "#1f77b4",
    "Protests": "#2ca02c",
    "Strategic developments": "#f1c40f",
}
# Short pie labels reduce overlap between segment text and percentages (percentages removed on-slice anyway).
pie_label_short = {
    "Battles": "Battles",
    "Explosions/Remote violence": "Explos./remote",
    "Violence against civilians": "Violence v. civilians",
    "Riots": "Riots",
    "Protests": "Protests",
    "Strategic developments": "Strategic dev.",
}


_border_geo_three_cached: dict | None = None
_border_geo_three_fetched = False


def border_geo_three_countries() -> dict | None:
    """Natural Earth 50m polygons for Kyrgyzstan, Tajikistan, Uzbekistan only (smooth vs 110m)."""
    global _border_geo_three_cached, _border_geo_three_fetched
    if _border_geo_three_fetched:
        return _border_geo_three_cached
    _border_geo_three_fetched = True
    url = "https://d2ad6b4ur7yvq5.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson"
    req = Request(url, headers={"User-Agent": "POLI3148-report/1"})
    wanted = {"KGZ", "TJK", "UZB"}
    try:
        with urlopen(req, timeout=60) as resp:
            world = json.load(resp)
        feats = []
        for f in world.get("features", []):
            props = f.get("properties") or {}
            iso = props.get("ISO_A3") or props.get("ADM0_A3") or ""
            if iso == "-99":
                iso = props.get("ADM0_A3") or ""
            if iso in wanted:
                feats.append(f)
        _border_geo_three_cached = {"type": "FeatureCollection", "features": feats} if len(feats) >= 2 else None
    except (OSError, ValueError, json.JSONDecodeError):
        _border_geo_three_cached = None
    return _border_geo_three_cached


def kg_tj_geo_subset(full_geo: dict) -> dict | None:
    feats = []
    for f in full_geo.get("features", []):
        p = f.get("properties") or {}
        iso = p.get("ISO_A3") or p.get("ADM0_A3") or ""
        if iso == "-99":
            iso = p.get("ADM0_A3") or ""
        if iso in {"KGZ", "TJK"}:
            feats.append(f)
    if len(feats) < 2:
        return None
    return {"type": "FeatureCollection", "features": feats}


def add_kg_tj_choropleth(fig: go.Figure, full_geo: dict) -> bool:
    """Fill only Kyrgyzstan and Tajikistan to show the two parties (no Uzbekistan hotspot box)."""
    sub = kg_tj_geo_subset(full_geo)
    if sub is None:
        return False
    fig.add_trace(
        go.Choroplethmapbox(
            geojson=sub,
            locations=["KGZ", "TJK"],
            z=[1.0, 2.0],
            featureidkey="properties.ISO_A3",
            colorscale=[
                [0.0, "#6BA868"],
                [0.498, "#6BA868"],
                [0.5, "#D98A62"],
                [1.0, "#D98A62"],
            ],
            marker_line_width=1.05,
            marker_line_color="rgba(54,67,94,0.42)",
            showscale=False,
            hovertext=["Kyrgyzstan", "Tajikistan"],
            hovertemplate="%{hovertext}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            lat=[41.28, 38.76],
            lon=[74.4, 70.92],
            mode="text",
            text=["Kyrgyzstan", "Tajikistan"],
            textfont=dict(size=12, color="#1a2744"),
            textposition=["top center", "bottom center"],
            showlegend=False,
            hoverinfo="skip",
        )
    )
    return True


pre_post = acled.assign(period=np.where(acled["year"] < 2023, "Pre-2023", "Post-2023"))
period_summary = (
    pre_post.groupby("period")
    .agg(events=("event_id_cnty", "count"), fatalities=("fatalities", "sum"), event_types=("event_type", "nunique"))
    .reset_index()
)
period_years = {"Pre-2023": 5, "Post-2023": 3}
period_summary["events_per_year"] = period_summary.apply(lambda r: r["events"] / period_years[r["period"]], axis=1)
period_summary["fatalities_per_year"] = period_summary.apply(lambda r: r["fatalities"] / period_years[r["period"]], axis=1)
period_summary_display = period_summary.copy()
period_summary_display["events_per_year"] = period_summary_display["events_per_year"].round(2)
period_summary_display["fatalities_per_year"] = period_summary_display["fatalities_per_year"].round(2)
period_summary_display.columns = ["Period", "Events", "Fatalities", "Event types", "Events/year", "Fatalities/year"]

# 3.1 Monthly event-type trends. Lines always drawn; markers only when events > 0.
monthly_type = acled.groupby(["event_month", "event_type"]).size().rename("events").reset_index()
all_month_type = pd.MultiIndex.from_product([month_index, event_type_order], names=["event_month", "event_type"]).to_frame(index=False)
monthly_type = all_month_type.merge(monthly_type, on=["event_month", "event_type"], how="left").fillna({"events": 0})
fig_monthly_types = go.Figure()
for et in event_type_order:
    sub = monthly_type[monthly_type["event_type"] == et]
    marker_opacity = [1.0 if float(v) > 0 else 0.0 for v in sub["events"].tolist()]
    fig_monthly_types.add_trace(
        go.Scatter(
            x=sub["event_month"],
            y=sub["events"],
            mode="lines+markers",
            name=et,
            line=dict(color=event_type_colors[et], width=2),
            marker=dict(color=event_type_colors[et], size=7, opacity=marker_opacity, line=dict(width=0)),
            hovertemplate="Year: %{x|%Y-%m}<br>Events: %{y}<br>Event type: "
            + et.replace("&", "&amp;")
            + "<extra></extra>",
        )
    )
fig_monthly_types.add_vline(x=pd.Timestamp("2023-01-01"), line_dash="dash", line_color="#555")
fig_monthly_types.add_annotation(
    x=pd.Timestamp("2023-01-01"),
    y=1.05,
    yref="paper",
    text="2023 structural break",
    showarrow=False,
    font=dict(size=10),
)
fig_monthly_types.update_layout(
    title=dict(text="Monthly event trends by event type (2018-2025)", x=0.02, xref="paper", xanchor="left"),
    template="plotly_white",
    height=570,
    hovermode="x unified",
    legend=dict(orientation="h", y=-0.32, x=0.5, xanchor="center"),
    margin=dict(l=50, r=35, t=70, b=135),
)
fig_monthly_types.update_xaxes(title_text="Year", tickformat="%Y", dtick="M12")

# 3.1 Bubble-size view: one year at a time, with bubble size showing monthly event counts.
bubble_plot_df = monthly_type.copy()
bubble_plot_df["year"] = bubble_plot_df["event_month"].dt.year
bubble_plot_df["month_label"] = bubble_plot_df["event_month"].dt.strftime("%Y-%m")
bubble_plot_df["bubble_size"] = ((bubble_plot_df["events"] ** 0.7) * 12).clip(7, 50)

monthly_hover_meta = (
    acled.assign(event_month=acled["event_date"].dt.to_period("M").dt.to_timestamp())
    .sort_values(["event_month", "event_type", "fatalities"], ascending=[True, True, False])
    .drop_duplicates(["event_month", "event_type"])
    [["event_month", "event_type", "sub_event_type", "actor1", "actor2", "fatalities"]]
)
bubble_plot_df = bubble_plot_df.merge(monthly_hover_meta, on=["event_month", "event_type"], how="left")
bubble_plot_df[["sub_event_type", "actor1", "actor2"]] = bubble_plot_df[["sub_event_type", "actor1", "actor2"]].fillna("N/A")
bubble_plot_df["fatalities"] = bubble_plot_df["fatalities"].fillna(0).astype(int)

fig_monthly_bubbles = go.Figure()
bubble_years = sorted(bubble_plot_df["year"].unique())
trace_ranges: dict[int, tuple[int, int]] = {}
for year in bubble_years:
    start = len(fig_monthly_bubbles.data)
    year_df = bubble_plot_df[(bubble_plot_df["year"] == year) & (bubble_plot_df["events"] > 0)].copy()
    for et in event_type_order:
        d = year_df[year_df["event_type"] == et].sort_values("event_month")
        if d.empty:
            continue
        fig_monthly_bubbles.add_trace(
            go.Scatter(
                x=d["event_month"],
                y=d["event_type"],
                mode="markers",
                name=et,
                showlegend=False,
                visible=(year == bubble_years[0]),
                marker=dict(
                    size=d["bubble_size"],
                    color=event_type_colors[et],
                    opacity=0.68,
                    line=dict(width=1, color="white"),
                ),
                customdata=d[["events", "month_label", "sub_event_type", "actor1", "actor2", "fatalities"]].to_numpy(),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Month: %{customdata[1]}<br>"
                    "Events: %{customdata[0]:.0f}<br>"
                    "Conflict type: %{customdata[2]}<br>"
                    "Actor 1: %{customdata[3]}<br>"
                    "Actor 2: %{customdata[4]}<br>"
                    "Fatalities: %{customdata[5]}<extra></extra>"
                ),
            )
        )
    trace_ranges[year] = (start, len(fig_monthly_bubbles.data))

legend_trace_start = len(fig_monthly_bubbles.data)
for et in event_type_order:
    fig_monthly_bubbles.add_trace(
        go.Scatter(
            x=[None],
            y=[et],
            mode="markers",
            name=et,
            marker=dict(size=12, color=event_type_colors[et], opacity=0.85, line=dict(width=1, color="white")),
            hoverinfo="skip",
            showlegend=True,
            visible=True,
        )
    )

slider_steps = []
for year in bubble_years:
    lo, hi = trace_ranges[year]
    slider_steps.append(
        dict(
            method="update",
            label=str(year),
            args=[
                {
                    "visible": [
                        (lo <= idx < hi) if idx < legend_trace_start else True
                        for idx in range(len(fig_monthly_bubbles.data))
                    ]
                }
            ],
        )
    )

fig_monthly_bubbles.update_layout(
    title=dict(text="Monthly event trends bubble map by year", x=0.02, xref="paper", xanchor="left"),
    xaxis_title="Month",
    yaxis_title="Event type",
    xaxis=dict(tickformat="%b", dtick="M1"),
    template="plotly_white",
    height=780,
    hovermode="closest",
    legend=dict(orientation="h", y=-0.62, x=0.5, xanchor="center", yanchor="top", font=dict(size=10)),
    margin=dict(l=160, r=35, t=70, b=360),
    sliders=[
        dict(
            active=0,
            currentvalue=dict(prefix="Year: "),
            pad=dict(t=40),
            steps=slider_steps,
        )
    ],
    annotations=[
        dict(
            text="<i>Bubble size represents the number of events</i>",
            xref="paper",
            yref="paper",
            x=0,
            y=-0.44,
            showarrow=False,
            font=dict(size=11, color="gray"),
            xanchor="left",
        )
    ],
)

# 3.2 Yearly event-type distribution. Slice labels abbreviated; no percentages on wedges; lighter subplot titles.
fig_event_types = make_subplots(
    rows=3,
    cols=3,
    specs=[[{"type": "domain"}, {"type": "domain"}, {"type": "domain"}], [{"type": "domain"}, {"type": "domain"}, {"type": "domain"}], [{"type": "domain"}, {"type": "domain"}, {"type": "domain"}]],
    subplot_titles=[str(y) for y in range(2018, 2026)] + [""],
    horizontal_spacing=0.04,
    vertical_spacing=0.08,
)
for i, year in enumerate(range(2018, 2026), start=1):
    row = ((i - 1) // 3) + 1
    col = ((i - 1) % 3) + 1
    frame = acled[acled["year"] == year]["event_type"].value_counts().reindex(event_type_order, fill_value=0)
    frame = frame[frame > 0]
    short_labels = [pie_label_short.get(str(x), str(x)) for x in frame.index]
    fig_event_types.add_trace(
        go.Pie(
            labels=short_labels,
            values=frame.values,
            name=str(year),
            marker=dict(colors=[event_type_colors.get(v, "#7f7f7f") for v in frame.index], line=dict(width=0)),
            textinfo="none",
            customdata=list(frame.index),
            hovertemplate="Year: "
            + str(year)
            + "<br>Event type: %{customdata}<br>Events: %{value}<br>Share: %{percent}<extra></extra>",
            showlegend=False,
            textfont=dict(size=11),
            insidetextorientation="horizontal",
        ),
        row=row,
        col=col,
    )
for event_type in event_type_order:
    fig_event_types.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color=event_type_colors[event_type]),
            name=pie_label_short.get(event_type, event_type),
            showlegend=True,
        )
    )
fig_event_types.update_layout(
    title=dict(text="Event-type distribution by year (2018-2025)", x=0.02, xref="paper", xanchor="left"),
    template="plotly_white",
    height=850,
    legend=dict(orientation="h", y=-0.06, x=0.5, xanchor="center", font=dict(size=10)),
    margin=dict(t=90, l=25, r=25, b=90),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
fig_event_types.update_annotations(
    bgcolor="rgba(0,0,0,0)",
    borderwidth=0,
    borderpad=4,
    font=dict(size=11, color="#455066"),
)
fig_event_types.update_layout(
    xaxis=dict(visible=False, showgrid=False, showline=False, zeroline=False),
    yaxis=dict(visible=False, showgrid=False, showline=False, zeroline=False),
)

# 3.3 Interactive map, modeled on the selected notebook map: 2021/2022 incidents, hotspot outlines, and jittered points.
map_data = acled[acled["year"].isin([2021, 2022])].dropna(subset=["latitude", "longitude"]).copy()
map_data["period"] = np.where(map_data["year"] == 2021, "2021 Dispute", "2022 Dispute")
map_data["fatalities_for_visualization"] = map_data["fatalities"] + 1
map_data["bubble_size"] = np.clip(np.log(map_data["fatalities_for_visualization"]) * 13 + 7, 7, 25)
dup_rank = map_data.groupby(["latitude", "longitude"]).cumcount()
dup_total = map_data.groupby(["latitude", "longitude"])["latitude"].transform("count")
angles = (dup_rank * 2.39996323) % (2 * np.pi)
radius = np.where(dup_total > 1, 0.015 + np.sqrt(dup_rank) * 0.012, 0.0)
map_data["lat_plot"] = map_data["latitude"] + radius * np.sin(angles)
map_data["lon_plot"] = map_data["longitude"] + radius * np.cos(angles) / np.cos(np.deg2rad(map_data["latitude"].clip(-70, 70)))
map_data["hover_text"] = map_data.apply(
    lambda r: "<br>".join(
        [
            f"<b>{r['period']}</b>",
            f"Location: {r.get('location', 'Unknown')}",
            f"Event date: {r['event_date'].strftime('%Y-%m-%d')}",
            f"Event type: {r.get('event_type', 'Unknown')}",
            f"Actor 1: {r.get('actor1', 'Unknown')}",
            f"Actor 2: {r.get('actor2', 'Unknown')}",
            f"Fatalities: {int(r['fatalities'])}",
        ]
    ),
    axis=1,
)

fig_map = go.Figure()
_border_geo_main = border_geo_three_countries()
_geo_main_ok = bool(_border_geo_main and add_kg_tj_choropleth(fig_map, _border_geo_main))
if not _geo_main_ok:
    fig_map.add_trace(
        go.Scattermapbox(
            lat=[41.05, 38.92],
            lon=[73.85, 70.92],
            mode="markers+text",
            marker=dict(size=28, color=["#6BA868", "#D98A62"], opacity=0.72),
            text=["Kyrgyzstan", "Tajikistan"],
            textposition="top center",
            showlegend=False,
            hovertemplate="%{text}<extra></extra>",
        )
    )

def make_circle(center_lat: float, center_lon: float, radius_km: float, n: int = 220) -> tuple[np.ndarray, np.ndarray]:
    theta = np.linspace(0, 2 * np.pi, n)
    lat = center_lat + (radius_km / 111.32) * np.sin(theta)
    lon = center_lon + (radius_km / (111.32 * np.cos(np.deg2rad(center_lat)))) * np.cos(theta)
    return lat, lon

hotspot_zones = [
    ("Hotspot 1: Core border clashes (highest concentration)", 39.95, 70.55, 18, "#0EA5E9", 3.2),
    ("Hotspot 2: Western villages corridor (repeated incidents)", 40.13, 69.76, 16, "#F97316", 2.9),
    ("Hotspot 3: Adjacent border cluster (near core hotspot)", 40.08, 70.76, 14, "#A855F7", 2.8),
]
for i, (name, lat, lon, radius_km, color, width) in enumerate(hotspot_zones):
    z_lat, z_lon = make_circle(lat, lon, radius_km)
    fig_map.add_trace(
        go.Scattermapbox(
            lon=z_lon,
            lat=z_lat,
            mode="lines",
            line=dict(color=color, width=width),
            name=name,
            legendgroup="zone",
            legendgrouptitle_text="Conflict hotspot zones" if i == 0 else None,
            hovertemplate=f"{name}<extra></extra>",
        )
    )
period_colors = {"2021 Dispute": "#4C78A8", "2022 Dispute": "#E11D48"}
for period in ["2021 Dispute", "2022 Dispute"]:
    subset = map_data[map_data["period"] == period]
    fig_map.add_trace(
        go.Scattermapbox(
            lon=subset["lon_plot"],
            lat=subset["lat_plot"],
            mode="markers",
            marker=dict(size=subset["bubble_size"], color=period_colors[period], opacity=0.62),
            name=period,
            legendgroup="period",
            legendgrouptitle_text="Conflict period" if period == "2021 Dispute" else None,
            hovertemplate="%{customdata}<extra></extra>",
            customdata=subset["hover_text"],
        )
    )
fig_map.update_layout(
    title=dict(text="Conflict hotspot map: 2021 and 2022 escalation geography", x=0.02, xref="paper", xanchor="left"),
    mapbox=dict(style="carto-positron", center=dict(lat=39.88, lon=70.58), zoom=7.92),
    height=720,
    margin=dict(t=70, r=20, b=20, l=20),
    legend=dict(font=dict(size=10), bgcolor="rgba(255,255,255,0.70)"),
)

_static_map_cfg = {"staticPlot": True, "displaylogo": False, "responsive": True}
fig_border_overview: go.Figure | None = None
if _border_geo_main is not None:
    fo = go.Figure()
    if add_kg_tj_choropleth(fo, _border_geo_main):
        fo.update_layout(
            title=dict(
                text="Static overview: Kyrgyzstan and Tajikistan (parties along the disputed border)",
                x=0.02,
                xref="paper",
                xanchor="left",
            ),
            mapbox=dict(style="carto-positron", center=dict(lat=40.06, lon=70.92), zoom=6.92),
            height=552,
            margin=dict(t=64, r=14, b=14, l=14),
            legend=dict(font=dict(size=10), bgcolor="rgba(255,255,255,0.65)"),
        )
        fig_border_overview = fo

overview_static_html = ""
if fig_border_overview is not None:
    overview_static_html = f"""
      <div class="map-static-pane">
        {fig_html(fig_border_overview, include_plotlyjs=False, config=_static_map_cfg)}
      </div>
    """

image_html = ""
if uploaded_image_path.exists():
    image_b64 = base64.b64encode(uploaded_image_path.read_bytes()).decode("ascii")
    image_html = f"""
      <p class="caption conflict-zone-caption">Primary Conflict Zone (Batken–Sughd Border)</p>
      <figure class="map-photo">
        <img src="data:image/png;base64,{image_b64}" alt="Reference map: Kyrgyzstan and Tajikistan (Davies, 2022)" />
        <figcaption>(Davies, 2022)</figcaption>
      </figure>
    """

# 4.1 Directly copy the cluster logic from the updated copy 4 notebook.
def classify_actor_type(actor_name: str) -> str:
    if pd.isna(actor_name):
        return "Unknown"
    actor = str(actor_name).lower()
    if any(k in actor for k in ["military forces", "armed forces", "state forces", "border guards", "police forces", "ministry of interior", "government"]):
        return "State forces"
    if any(k in actor for k in ["civilian", "residents", "villagers", "locals"]):
        return "Civilians"
    if any(k in actor for k in ["riot", "protest"]):
        return "Rioters/protesters"
    if any(k in actor for k in ["militia", "armed group"]):
        return "Armed groups"
    return "Other / mixed"

actor_cols = [c for c in ["actor1", "actor2"] if c in acled.columns]
if actor_cols:
    actor_long = acled[["event_month"] + actor_cols].melt(id_vars=["event_month"], value_vars=actor_cols, value_name="actor_name").dropna(subset=["actor_name"])
    actor_long["actor_type"] = actor_long["actor_name"].map(classify_actor_type)
    actor_counts = actor_long.groupby(["event_month", "actor_type"]).size().rename("n").reset_index().sort_values(["event_month", "n", "actor_type"], ascending=[True, False, True])
    top_actor_types = actor_counts.groupby("event_month").apply(lambda d: ", ".join(d["actor_type"].head(2)), include_groups=False).rename("main_actor_types").reindex(month_index).fillna("No actors recorded")
else:
    top_actor_types = pd.Series("No actors recorded", index=month_index, name="main_actor_types")

event_type_rank = acled.groupby(["event_month", "event_type"]).size().rename("n").reset_index()
dominant_event_type = (
    event_type_rank.sort_values(["event_month", "n", "event_type"], ascending=[True, False, True])
    .drop_duplicates("event_month")
    .set_index("event_month")["event_type"]
    .reindex(month_index)
    .fillna("No recorded event")
    .rename("dominant_event_type")
)
plot_df = pd.concat(
    [
        monthly.set_index("event_month")["events"],
        monthly.set_index("event_month")["fatalities"],
        dominant_event_type,
        top_actor_types,
    ],
    axis=1,
).reset_index().rename(columns={"index": "event_month"})

cluster_meta = {
    1: {
        "name": "Cluster 1: Communal (2018–20)",
        "description": "Low-intensity/high-frequency civilian disputes;<br>minimal fatalities; enclave-localized.",
        "color": "#2ca02c",
        "fullname": "Cluster 1: Communal Resource Conflict (2018-2020)",
    },
    2: {
        "name": "Cluster 2: Escalation (2021–22)",
        "description": "State-to-state clashes with heavy weapons/UAVs;<br>highest fatalities; geographically dispersed strikes.",
        "color": "#d62728",
        "fullname": "Cluster 2: Militarized Interstate Escalation (2021-2022)",
    },
    3: {
        "name": "Cluster 3: Cold peace (2023–25)",
        "description": "Sharp decline in violence/fatalities;<br>strategic developments and border securitization dominate.",
        "color": "#1f77b4",
        "fullname": "Cluster 3: Securitized Cold Peace (2023-2025)",
    },
}
plot_df["cluster_id"] = plot_df["event_month"].map(lambda m: 1 if m < pd.Timestamp("2021-01-01") else 2 if m < pd.Timestamp("2023-01-01") else 3)
plot_df["cluster_name"] = plot_df["cluster_id"].map(lambda c: cluster_meta[c]["fullname"])
plot_df["cluster_description"] = plot_df["cluster_id"].map(lambda c: cluster_meta[c]["description"])
fig_phase = go.Figure()
for cluster_id in [1, 2, 3]:
    chunk = plot_df[plot_df["cluster_id"] == cluster_id].copy()
    meta = cluster_meta[cluster_id]
    customdata = np.column_stack([chunk["cluster_name"], chunk["cluster_description"], chunk["dominant_event_type"], chunk["fatalities"], chunk["main_actor_types"]])
    fig_phase.add_trace(
        go.Scatter(
            x=chunk["event_month"],
            y=chunk["events"],
            mode="lines+markers",
            name=meta["name"],
            line=dict(color=meta["color"], width=2.5),
            marker=dict(size=5, color=meta["color"]),
            customdata=customdata,
            hovertemplate=(
                "Month: %{x|%Y-%m}<br>Events: %{y}<br><b>Cluster:</b> %{customdata[0]}<br>"
                "<b>Brief:</b> %{customdata[1]}<br><b>Event type:</b> %{customdata[2]}<br>"
                "<b>Fatalities:</b> %{customdata[3]}<br><b>Main actors:</b> %{customdata[4]}<extra></extra>"
            ),
            legendrank=cluster_id,
        )
    )
for x, text, color, x_text in [
    ("2021-01-01", "Jan 2021: Militarization pivot", "#ff7f0e", "2020-03-01"),
    ("2023-01-01", "Jan 2023: Demarcation / de-escalation pivot", "#9467bd", "2024-04-10"),
]:
    fig_phase.add_shape(type="line", x0=pd.Timestamp(x), x1=pd.Timestamp(x), y0=0, y1=1, xref="x", yref="paper", line=dict(color=color, width=2, dash="dash"))
    fig_phase.add_annotation(x=pd.Timestamp(x_text), y=0.9, xref="x", yref="paper", text=text, showarrow=False, font=dict(color=color, size=10), bgcolor="rgba(255,255,255,0.88)", bordercolor=color, borderwidth=1)
fig_phase.update_layout(
    title="",
    xaxis_title="Time (month)",
    yaxis_title="Number of events",
    xaxis=dict(
        range=[pd.Timestamp("2018-01-01"), pd.Timestamp("2025-12-31")],
        rangeselector=dict(
            y=1.055,
            yanchor="bottom",
            x=0.258,
            xanchor="left",
            buttons=[
                dict(count=12, label="1y", step="month", stepmode="backward"),
                dict(count=24, label="2y", step="month", stepmode="backward"),
                dict(step="all", label="All"),
            ],
        ),
        rangeslider=dict(visible=True, thickness=0.09),
    ),
    legend_title="Conflict clusters",
    legend=dict(font=dict(size=9), title_font=dict(size=10), bgcolor="rgba(255,255,255,0.55)", orientation="v", x=0, xanchor="left", y=-0.58, yanchor="top"),
    hovermode="closest",
    template="plotly_white",
    margin=dict(t=226, r=40, b=330, l=60),
    hoverlabel=dict(align="left", font=dict(size=10)),
    dragmode="pan",
    height=900,
)
fig_phase.add_annotation(
    xref="paper",
    yref="paper",
    x=-0.02,
    y=1.35,
    xanchor="left",
    yanchor="top",
    text="Kyrgyzstan-Tajikistan Border Conflict Dynamics (2018–2025)",
    showarrow=False,
    font=dict(size=17, color="#2a3f5f", family="Arial, Helvetica, sans-serif"),
)
fig_phase.add_annotation(
    xref="paper",
    yref="paper",
    x=-0.02,
    y=1.048,
    xanchor="left",
    yanchor="bottom",
    text="<b>Zoom window:</b>",
    showarrow=False,
    font=dict(size=11),
)

# 4.3 Dual-axis chart from copy 4, with range slider and no dashed event lines.
notes_col = next((col for col in acled.columns if "note" in col.lower()), None)
def top_note(series: pd.Series) -> str:
    if notes_col is None:
        return ""
    values = series.dropna()
    return values.value_counts().idxmax() if not values.empty else ""

timeline_monthly = (
    acled.assign(month=acled["event_date"].dt.to_period("M").dt.to_timestamp("M"))
    .groupby("month")
    .agg(events=("event_date", "size"), fatalities=("fatalities", "sum"), top_event=(notes_col, top_note) if notes_col else ("event_date", lambda s: ""))
    .reset_index()
)
timeline_monthly["fatalities"] = timeline_monthly["fatalities"].fillna(0)
timeline_monthly["top_event"] = timeline_monthly["top_event"].fillna("")
fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
fig_dual.add_trace(
    go.Scatter(x=timeline_monthly["month"], y=timeline_monthly["events"], mode="lines+markers", name="Monthly events", customdata=timeline_monthly[["top_event"]].to_numpy(), hovertemplate="Month: %{x|%Y-%m}<br>Events: %{y}<br>Top Event: %{customdata[0]}<extra></extra>"),
    secondary_y=False,
)
fig_dual.add_trace(
    go.Bar(x=timeline_monthly["month"], y=timeline_monthly["fatalities"], name="Monthly fatalities", opacity=0.6, customdata=timeline_monthly[["top_event"]].to_numpy(), hovertemplate="Month: %{x|%Y-%m}<br>Fatalities: %{y}<extra></extra>"),
    secondary_y=True,
)
fig_dual.update_layout(
    title=dict(text="Dual-axis timeline: Events and Fatalities (2018-2025)", x=0.02, xref="paper", xanchor="left"),
    xaxis=dict(title="Year", rangeslider=dict(visible=True), range=["2018-01-01", "2025-12-31"]),
    yaxis=dict(title="Events"),
    yaxis2=dict(title="Fatalities"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=60, b=40),
    template="plotly_white",
    height=540,
)

# 5 Forecast from copy 4, including x-axis, range slider, and shaded windows.
series = acled.assign(month=acled["event_date"].dt.to_period("M").dt.to_timestamp("M")).groupby("month").size().rename("events").reset_index().sort_values("month")
post_2023 = series[(series["month"] >= "2023-01-01") & (series["month"] <= "2025-12-31")].copy()
if post_2023.empty:
    post_2023 = series.tail(36).copy()
window = 6
post_2023["roll_mean"] = post_2023["events"].rolling(window=window, min_periods=1).mean()
future_months = pd.date_range(pd.Timestamp("2026-01-31"), periods=60, freq="ME")
last_values = post_2023["events"].tail(window).to_list()
forecast_events = []
for _ in range(len(future_months)):
    mean_val = float(np.mean(last_values)) if last_values else 0.0
    forecast_events.append(mean_val)
    last_values = (last_values + [mean_val])[-window:]
forecast_df = pd.DataFrame({"month": future_months, "events": np.round(forecast_events, 2), "type": "Projection"})
observed_df = series.copy()
observed_df["type"] = "Observed"
fig_forecast = go.Figure()
fig_forecast.add_trace(go.Scatter(x=observed_df["month"], y=observed_df["events"], mode="lines", name="Observed", line=dict(color="#0B3C8C", width=3), fill="tozeroy", fillcolor="rgba(11, 60, 140, 0.24)", hovertemplate="Month: %{x|%Y-%m}<br>Events: %{y}<extra></extra>"))
fig_forecast.add_trace(go.Scatter(x=forecast_df["month"], y=forecast_df["events"], mode="lines", name="Projection", line=dict(color="#B0122B", width=3, dash="dash"), fill="tozeroy", fillcolor="rgba(176, 18, 43, 0.20)", hovertemplate="Month: %{x|%Y-%m}<br>Events: %{y}<extra></extra>"))
for name, color in [("Pre-2023 shaded window", "rgba(235, 140, 52, 0.45)"), ("Post-2023 shaded window", "rgba(39, 174, 146, 0.45)"), ("Projection window shaded", "rgba(123, 97, 255, 0.45)")]:
    fig_forecast.add_trace(go.Scatter(x=[observed_df["month"].min()], y=[0], mode="markers", marker=dict(size=12, color=color), name=name, hoverinfo="skip"))
fig_forecast.add_vrect(x0="2018-01-01", x1="2022-12-31", fillcolor="rgba(235, 140, 52, 0.12)", line_width=0)
fig_forecast.add_vrect(x0="2023-01-01", x1="2030-12-31", fillcolor="rgba(39, 174, 146, 0.12)", line_width=0)
fig_forecast.add_vrect(x0="2026-01-01", x1="2030-12-31", fillcolor="rgba(123, 97, 255, 0.11)", line_width=0)
fig_forecast.add_vline(x="2023-01-01", line_dash="dot", line_color="rgba(0,0,0,0.4)")
fig_forecast.add_vline(x="2026-01-01", line_dash="dot", line_color="rgba(0,0,0,0.4)")
fig_forecast.update_layout(
    title=dict(text="Observed Trends and Rolling-Mean Projections of Conflict (2018-2030)", x=0.02, xref="paper", xanchor="left", y=0.98),
    xaxis_title="Year",
    yaxis_title="Events",
    xaxis=dict(rangeslider=dict(visible=True), range=["2018-01-01", "2030-12-31"], tickformat="%Y", dtick="M12"),
    template="plotly_white",
    height=680,
    legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5, font=dict(size=10)),
    margin=dict(l=60, r=40, t=145, b=80),
)

references = [
    "Arynova, A., & Schmeier, S. (2022). Conflicts over water and water infrastructure at the Tajik-Kyrgyz border: A looming threat for Central Asia? Water, Peace and Security. https://waterpeacesecurity.org/files/68",
    "Davies, I. (2022). Contextual source cited in the report draft for geospatial interpretation of border hotspot concentration.",
    "Eurasian Research Institute. (2025). Historic Agreement on Kyrgyz-Tajik Borders. https://www.eurasian-research.org/publication/historic-agreement-on-kyrgyz-tajik-borders/",
    "European Union. (2023). Kyrgyzstan-Tajikistan: helping civilians recover after devastating border clashes. https://civil-protection-humanitarian-aid.ec.europa.eu/news-stories/stories/kyrgyzstan-tajikistan-helping-civilians-recover-after-devastating-border-clashes_en",
    "Gabdulhakov, R., Antonov, O., & Kyzy, E. (2023). The Tajikistan-Kyrgyzstan Border Conflict: Social Media Discourses and Lived Experiences. The Oxus Society for Central Asian Affairs.",
    "Karacalti, A. (2021, February 9). Everlasting or Ever-Changing? Violence Along the Kyrgyzstan-Tajikistan Border. ACLED. https://acleddata.com/report/everlasting-or-ever-changing-violence-along-kyrgyzstan-tajikistan-border",
    "Kyrgyzstan, J. (2018). Kyrgyzstan and Tajikistan: Next in Line. https://www.silkroadstudies.org/resources/pdf/publications/9-1409GrandStrategy-Engvall.pdf",
    "Putz, C. (2023, October 4). Mysterious Border Protocol Signed Between Kyrgyz and Tajik Security Chiefs. The Diplomat. https://thediplomat.com/2023/10/mysterious-border-protocol-signed-between-kyrgyz-and-tajik-security-chiefs/",
    "Saud, A., & Gul, A. (2024). Kyrgyzstan-Tajikistan Border Skirmishes (2022) and Waning Russian Influence in Central Asia. Central Asia, 92(Summer), 17-34. https://doi.org/10.54418/ca-92.198",
    "Sullivan, C. J. (2021). Battle at the Border: An Analysis of the 2021 Kyrgyzstan-Tajikistan Conflict. Asian Affairs, 52(3), 529-535. https://doi.org/10.1080/03068374.2021.1940587",
]
references_html = "\n".join(f"<li>{escape(ref)}</li>" for ref in references)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Interactive Data-Driven Analysis Report</title>
  <style>
    :root {{ --bg: #f7f8fb; --ink: #172033; --muted: #5f6b7a; --line: #d9dee8; --panel: #ffffff; --accent: #244c8f; --accent-soft: #e8eef8; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: var(--bg); color: var(--ink); line-height: 1.62; }}
    .page {{ max-width: 1240px; margin: 0 auto; padding: 28px 22px 56px; }}
    .hero, .section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 18px; }}
    .hero {{ padding: 30px; }}
    .section {{ padding: 24px 28px; margin-top: 18px; }}
    .eyebrow {{ color: var(--accent); font-weight: 700; letter-spacing: .03em; text-transform: uppercase; font-size: .86rem; }}
    h1 {{ font-size: 2.05rem; line-height: 1.2; margin: 10px 0 12px; }}
    h2 {{ font-size: 1.35rem; margin: 34px 0 12px; border-top: 1px solid var(--line); padding-top: 24px; }}
    h3 {{ font-size: 1.08rem; margin: 22px 0 8px; }}
    .section > h2:first-child {{ border-top: 0; padding-top: 0; margin-top: 0; }}
    p {{ margin: 0 0 14px; }}
    .meta, .caption, figcaption {{ color: var(--muted); }}
    .toc {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 20px; }}
    .toc a {{ text-decoration: none; color: var(--accent); border: 1px solid #c9d5eb; background: #fff; border-radius: 999px; padding: 6px 11px; font-size: .9rem; }}
    .analysis-list {{ margin-top: 10px; }}
    .analysis-list li {{ margin-bottom: 8px; }}
    .chart {{ margin: 18px 0 22px; padding: 10px; border: 1px solid var(--line); border-radius: 14px; background: #fff; }}
    .chart--pies {{ margin: 12px 0 20px; padding: 0; border: none; border-radius: 0; background: transparent; box-shadow: none; }}
    .map-hotspot-stack {{ margin: 16px 0 22px; padding: 12px 12px 16px; border: 1px solid var(--line); border-radius: 14px; background: #fff; }}
    .map-static-pane {{ margin: 12px 0 18px; }}
    .map-hotspot-stack .map-photo {{ margin: 14px 0 0 0; }}
    .conflict-zone-caption {{ margin: 14px 0 8px; color: var(--ink); font-size: 1.08rem; font-weight: 700; }}
    .map-photo {{ margin: 12px 0 18px; }}
    .map-photo img {{ width: 100%; max-height: 520px; object-fit: contain; border: 1px solid var(--line); border-radius: 14px; background: #fff; }}
    .context-card {{ border: 1px solid var(--line); border-radius: 14px; padding: 18px; background: #fbfcff; margin: 12px 0 18px; }}
    .data-table {{ width: 100%; border-collapse: collapse; margin: 14px 0; font-size: .92rem; }}
    .data-table th, .data-table td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    .data-table th {{ background: #eef2f8; }}
    .note {{ background: #fff8e6; border: 1px solid #ead59a; border-radius: 12px; padding: 12px 14px; color: #5f4b16; }}
    ol.references {{ padding-left: 22px; }}
    ol.references li {{ margin-bottom: 10px; }}
    #findings > h2, #findings > h3 {{ font-size: 1.48rem; line-height: 1.3; }}
    #findings > h2 {{ margin-bottom: 12px; }}
    #findings > h3 {{ margin-top: 28px; padding-top: 22px; border-top: 1px solid var(--line); }}
    #findings > h2 + h3 {{ margin-top: 8px; padding-top: 8px; border-top: none; }}
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <div class="eyebrow">Interactive Data-Driven Analysis Report</div>
      <h1>Title: Chronic Tension to Managed Stability? Conflict Dynamics along the Kyrgyzstan-Tajikistan Border (2018-2025)</h1>
      <p class="meta"><strong>30 April 2026</strong></p>
      <p class="meta"><strong>Name:</strong> YAO KI SAN &nbsp; | &nbsp; <strong>Student UID:</strong> 3036067030 &nbsp; | &nbsp; <strong>Course Code:</strong> POLI3148</p>
      <nav class="toc">
        <a href="#introduction">Introduction</a><a href="#methodology">Methodology</a><a href="#conflict-setting">Conflict Setting</a><a href="#findings">Findings</a><a href="#forecast">Forecast</a><a href="#limitations">Limitations</a><a href="#references">References</a>
      </nav>
    </header>

    <section class="section" id="introduction">
      <h2>1. Introduction</h2>
      <p>The Kyrgyzstan-Tajikistan border remains one of Central Asia's most conflict-prone frontiers, particularly in the Batken (Kyrgyzstan) and Sughd (Tajikistan) regions. Overlapping settlements, enclaves, and shared infrastructure have historically generated disputes over land, water, and mobility (Arynova &amp; Schmeier, 2022).</p>
      <p>While violence historically took the form of low-intensity communal clashes, the period between 2021 and 2022 marked a critical shift toward militarised interstate conflict. The April 2021 “Water War” and the September 2022 escalation involved heavy weaponry, state forces, and significant casualties. In contrast, the period after 2023 suggests a structural break (Gabdulhakov &amp; Kyzy, 2023). This decline coincides with intensified diplomatic engagement and the eventual March 2025 border demarcation agreement, which formally delineated the entire Kyrgyz-Tajik boundary (Eurasian Research Institute, 2025).</p>
    </section>

    <section class="section" id="methodology">
      <h2>2. Methodology</h2>
      <p>Using ACLED data for 2018-2025, the analysis focuses on the Batken region of Kyrgyzstan and the Sughd region of Tajikistan, where majority of cross-border incidents occur. Three core analytical applications are:</p>
      <ol class="analysis-list" type="i">
        <li><strong>Quantitative Mapping:</strong> Tracking event frequency and fatalities to identify structural breaks.</li>
        <li><strong>Categorical Analysis:</strong> Comparing event types, such as Riots and Battles, to measure militarization.</li>
        <li><strong>Qualitative Synthesis:</strong> Interpreting data trends against the 2023-2025 diplomatic breakthroughs.</li>
      </ol>
      {table_html(period_summary_display)}
    </section>

    <section class="section" id="conflict-setting">
      <h2>3. Conflict Setting</h2>
      <p>Following independence in 1991, previously administrative Soviet borders became poorly defined international boundaries. As local livelihoods depend heavily on agriculture, water distribution, and cross-border mobility, disputes mostly concerned with irrigation systems, roads, pasture access, and enclave connectivity (Gabdulhakov &amp; Kyzy, 2023).</p>
      <p>Three drivers underpin this instability. First, resource scarcity, particularly competition over shared water infrastructure such as the Golovnoy facility. Second, Soviet-era demarcation has produced fragmented and interdependent territorial arrangements, including enclaves such as Vorukh, which complicate governance and generate overlapping claims. Third, domestic political fragility contributes to instability, as state elites may leverage border tensions to reinforce authority or mobilise nationalist sentiment (Arynova &amp; Schmeier, 2022; Gabdulhakov &amp; Kyzy, 2023).</p>
      <p>As a whole, these factors have created a pattern of persistent low-intensity conflict punctuated by periodic escalation. While tensions were already chronic before 2021, the escalation in 2021 and 2022 marked a turning point, as the conflict intensified in scale, lethality, and level of militarisation.</p>

      <h2>3.1 Patterns of Conflict</h2>
      <div class="chart">{fig_html(fig_monthly_types, include_plotlyjs='cdn')}</div>
      <div class="chart">{fig_html(fig_monthly_bubbles)}</div>
      <p>The data shows consistently high event frequency between 2018 and 2023 with persistent low-level tensions in general. April 2021 and September 2022 stand out as major outliers, with sharp spikes in both event frequency and fatalities. These peaks represent escalation episodes in which localized disputes expanded into large-scale violence involving state military forces.</p>
      <p>After 2023, both frequency and intensity decline sharply, suggesting a structural break in conflict dynamics. However, this decline should be interpreted as a reduction in overt violence alongside the persistence of underlying tensions. In effect, the post-2023 period marks a transition from interactive, community-driven conflict to controlled separation enforced through state authority (Sullivan, 2021; Karacalti, 2021).</p>

      <h2>3.2 Event-Type Transformation</h2>
      <div class="chart chart--pies">{fig_html(fig_event_types)}</div>
      <p>Between 2018 and 2020, conflict was dominated by riots and protests, reflecting community-based disputes over resources and infrastructure. Violence against civilians occurred but remained limited (Karacalti, 2021).</p>
      <p>In 2021 and 2022, there was a surge in battles signalling the growing involvement of state military actors and the escalation toward militarised confrontation. In the post-2023 period, strategic developments become the dominant event type. These include border patrols, infrastructure construction, and administrative control measures, reflecting a transition toward state-led management of the frontier.</p>
      <p>Overall, the data shows a progression from communal conflict to militarisation, followed by institutionalised de-escalation.</p>

      <h2>3.3 Spatial Concentration of Conflict</h2>
      <div class="map-hotspot-stack">
        {overview_static_html}
        {fig_html(fig_map, include_plotlyjs=False)}
        {image_html}
      </div>
      <div class="context-card">
        <h3>Border Hotspot Context</h3>
        <p>Conflict events are highly concentrated in the Batken region, confirming its role as the primary hotspot of violence. This concentration reflects the region’s geographical and strategic significance, where dense populations, shared infrastructure, and contested enclaves intersect. The region includes key water systems, transit routes, and enclaves, making it strategically and economically critical. As a result, Batken is particularly vulnerable to escalation. Even minor disputes can disrupt vital infrastructure or transportation routes, amplifying their impact (Davies, 2022; Eurasian Research Institute, 2025).</p>
      </div>

      <h2>3.4 Escalation Context: The 2021 and 2022 Conflicts</h2>
      <p>The 2021 clashes from April 29 to May 1, triggered by a dispute over the Golovnoy water distribution facility, marked a critical turning point. Initial confrontations involved civilians using stones and small arms, consistent with earlier patterns. However, the situation rapidly escalated as border guards and military forces intervened, leading to the use of firearms and mortars. Within days, dozens were killed, hundreds injured, and thousands displaced. This episode represents a clear shift from community-level dispute to state-led confrontation (Sullivan, 2021).</p>
      <p>The September 2022 escalation represents a further intensification. Unlike earlier conflicts confined to border villages, violence extended beyond disputed zones, involving the use of drones, artillery, and heavy weapons. The scale and organisation of the conflict indicate a transition toward high-intensity interstate warfare, with strikes targeting infrastructure and areas deeper within national territory (Saud &amp; Gul, 2023).</p>
    </section>

    <section class="section" id="findings">
      <h2>4. Key Findings</h2>
      <h3>4.1 Three Phases of Conflict</h3>
      <div class="chart">{fig_html(fig_phase, config={'scrollZoom': False, 'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'toggleSpikelines']})}</div>
      <p>The dataset reveals a clear three-phase trajectory in conflict dynamics along the Kyrgyzstan-Tajikistan border. The first phase (2018-2020) is characterised by frequent but low-intensity communal conflict, dominated by civilians and local actors. Most events consist of riots and protests related to disputes over water, roads, and pastureland, with relatively low fatality levels. Violence during this period functioned primarily as a localised bargaining mechanism, rather than organised warfare.</p>
      <p>The second phase (2021-2022) marks a period of rapid escalation and militarisation. Beginning with the April 2021 “Water War” and culminating in the September 2022 clashes, conflict shifted from community-based disputes to state-led military confrontation. Both the frequency of battle events and the severity of fatalities increased sharply, while interaction patterns shifted toward state-versus-state engagements, highlighting the transformation into interstate conflict.</p>
      <p>The third phase (2023-2025) shows a sharp decline in violent events, indicating a transition toward institutionalised conflict management. While overt violence decreases significantly, this phase reflects a transformation rather than the disappearance of conflict.</p>

      <h3>4.2 Transformation of Conflict Dynamics</h3>
      <p>Although event frequency follows a V-shaped trend, rising sharply before declining after 2023, militarisation follows a more linear trajectory, increasing during escalation and remaining embedded thereafter. This indicates that while violence has reduced, the infrastructure of militarisation persists.</p>
      <p>A comparison between the two periods illustrates this shift:</p>
      <table class="data-table"><thead><tr><th>Feature</th><th>Pre-2023 Dynamics</th><th>Post-2023 Dynamics</th></tr></thead><tbody><tr><td>Primary Actor</td><td>Local Civilians / Border Guards</td><td>Regular Army / State Officials</td></tr><tr><td>Event Type</td><td>Riots &amp; Property Destruction</td><td>Strategic Developments &amp; Patrols</td></tr><tr><td>Interaction</td><td>Communal (17, 77)</td><td>State-to-State (11)</td></tr><tr><td>Resolution</td><td>Temporary Ceasefires</td><td>Formal Demarcation Mapping</td></tr></tbody></table>
      <p>This shift indicates a transition from bottom-up conflict driven by local disputes to top-down conflict management dominated by state actors.</p>

      <h3>4.3 The “Silence” After 2023</h3>
      <p>The relative absence of direct violence after 2023 does not imply peace but reflects what can be described as a “cold peace”: a condition in which overt conflict is suppressed through state control rather than resolved. The dataset reveals an ongoing presence of strategic developments, indicating continued military activity and administrative consolidation along the border. This suggests that conflict has instead been transformed and institutionalised through processes of securitisation as indicated by the consistently high number of recorded strategic developments in post 2023.</p>
      <div class="chart">{fig_html(fig_dual)}</div>
      <p>As shown in the dual-axis chart, fatalities peak sharply during the escalation periods of 2021 and 2022, reflecting the use of heavy weaponry such as artillery, drones, and rocket systems. These spikes contrast strongly with the post-2023 period, where fatalities remain consistently low despite ongoing activity. Earlier incidents, such as in 2018, also produced temporary spikes, though at much lower intensity.</p>
      <p>The surge in fatalities during 2021-2022 highlights the shift toward high-intensity militarised conflict, while the subsequent decline reflects the effectiveness of measures aimed at preventing further large-scale escalation. However, this decline does not indicate conflict resolution. Rather, it suggests reduced opportunities for direct confrontation due to tighter border controls and increased military presence. In this sense, securitisation functions as a containment strategy, limiting violence without addressing underlying causes.</p>
      <p>Several factors explain this trend. First, intensified diplomacy after 2022 leading to agreements such as Protocol 44 (2023) and the March 2025 border settlement (Putz, 2023). These reduced territorial ambiguity and formalised boundary control. Second, war fatigue and reconstruction needs incentivised both governments to stabilise the region following widespread destruction and displacement. Third, domestic political considerations encouraged settlement, as leaders sought legitimacy and stability. Finally, broader regional geopolitical dynamics played an indirect but important role. Russia’s reduced engagement in regional mediation opened space for alternative actors, while Uzbekistan emerged as a more active diplomatic facilitator. Concurrently, China’s economic investments in Central Asia created additional incentives for maintaining regional stability (European Union, 2023).</p>
    </section>

    <section class="section" id="forecast">
      <h2>5. Future Implications and Forecast</h2>
      <div class="chart">{fig_html(fig_forecast)}</div>
      <p class="note"><strong>Reminder:</strong> Projection is a simple rolling-mean continuation from recent post-2023 patterns, so it should be read as a scenario rather than a predictive model.</p>
      <p>Based on post-2023 trends, the most likely trajectory is one of managed stability. Conflict events are expected to remain low, with near-zero battle events and minimal fatalities. However, low-intensity activities such as strategic developments, protests, and minor unrest are likely to persist.</p>
      <p>Diplomatic negotiations and the 2025 border agreement have played a critical role in reducing overt conflict. These efforts were driven by both domestic political incentives and broader regional considerations, including economic integration and stability concerns. However, underlying structural drivers, particularly resource competition and territorial ambiguity, remain unresolved (Eurasian Research Institute, 2025).</p>
      <p>Looking forward, the border is likely to remain stable over the next 3-5 years, which could best characterized as managed stability. The decline in violence supports a continued downward trajectory in intensity, but the persistence of low-intensity events implies a stabilization process still underway rather than a fully consolidated peace.</p>
    </section>

    <section class="section" id="limitations">
      <h2>6. Limitations</h2>
      <p>This report is subject to several important limitations related to data, scope, and analytical focus. To begin with, the report does not fully examine the actors factors like the role of local-level agency and community dynamics. While the analysis does not fully explore how involved actors mediate or exacerbate tensions among the recorded events. Moreover, the study is bound to the 2018-2025 data range, which excludes recent diplomatic developments or shifts occurring in early 2026. Furthermore, by maintaining a rigorous focus on the immediate border, the report may not fully account for broader regional shifts, such as the evolving security roles of external powers or changing trade alliances that indirectly dictate border stability.</p>
    </section>

    <section class="section" id="conclusion">
      <h2>7. Conclusion</h2>
      <p>The Kyrgyzstan-Tajikistan border conflict has shifted from recurring communal conflict to state-centric control. The 2021-2022 escalations catalysed demarcation and stabilisation, culminating in the March 2025 agreement. The Kyrgyz-Tajik border agreement is a historic milestone in resolving one of Central Asia’s most intractable territorial disputes. However, whether this peace holds will depend not only on agreements or treaties, but on how governments engage their citizens in building a shared future across once-divisive lines.</p>
    </section>

    <section class="section" id="references">
      <h2>8. References</h2>
      <ol class="references">{references_html}</ol>
      <p class="note"><strong>Data source:</strong> Armed Conflict Location &amp; Event Data Project (ACLED), filtered to Kyrgyzstan-Tajikistan border-related records for 2018-2025 using the processed project dataset.</p>
    </section>
  </main>
</body>
</html>"""

output_path.write_text(html, encoding="utf-8")
print(f"Revised interactive report written to: {output_path}")
