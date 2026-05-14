import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import altair as alt
from backend.config import DB_PATH, default_date_range
from backend.database import init_db, get_observations
from backend.analysis import (
    HEAT_PUMP_CONFIG, annual_cop_improvement,
    cop_estimate, heat_pump_supplement_simulation,
    tank_temperature_series,
)
from backend.scales import SCALES

st.set_page_config(page_title="Varmesystem", page_icon="🔥")
st.title("Varmesystem — bergvarme + regnvann")

# --- Scale gate -------------------------------------------------------------
scale_key = st.session_state.get("scale", "household")
if scale_key == "household":
    st.info(
        "**Denne modulen gjelder ikke for husholdningsskala.**\n\n"
        "Integrasjon med bergvarme krever et eksisterende vann/vann-varmepumpeanlegg. "
        "Dette er typisk infrastruktur for borettslag, skoler, sykehjem og næringsbygg.\n\n"
        "Bytt skala til **Nabolag** eller **Kritisk infrastruktur** på hovedsiden."
    )
    st.stop()

st.markdown(
    "En regnvannstank kan supplere et eksisterende **bergvarmeanlegg** (vann/vann-varmepumpe). "
    "Om sommeren og høsten er regnvannet ofte varmere enn berget — og en varmere kilde "
    "gir høyere COP (varmefaktor). Dette sparer strøm og lar bergbrønnen regenerere termisk."
)

st.caption(f"Aktiv skala: **{SCALES[scale_key].label}** (valgt på hovedsiden).")


@st.cache_data(ttl=3600)
def load_data():
    start, end = default_date_range()
    conn = init_db(DB_PATH)
    data = get_observations(conn, start, end)
    conn.close()
    return data


df = load_data()
if df.empty:
    st.warning("Ingen data funnet. Kjør `python -m backend.pipeline` for å hente data.")
    st.stop()

# --- Configuration ---------------------------------------------------------
st.markdown("---")
st.subheader("Systemkonfigurasjon")

col1, col2 = st.columns(2)
with col1:
    annual_demand = st.number_input(
        "Årlig varmebehov (kWh)", min_value=10_000, max_value=2_000_000,
        value=int(HEAT_PUMP_CONFIG["annual_demand_kwh_default"]), step=5_000,
        help="Bygningens totale årlige varmebehov. Et borettslag (60 leiligheter) "
             "ligger typisk på 200–400 MWh/år; et sykehjem 300–600 MWh; "
             "Haukeland-størrelse > 5 GWh.",
    )
    delivery_label = st.radio(
        "Leveringstemperatur",
        ["Gulvvarme (35 °C)", "Radiatorer (60 °C)"],
        horizontal=True,
        help="Lavtemperatur (gulvvarme) gir betydelig høyere COP enn høytemperatur (radiatorer).",
    )
    delivery_temp = 35.0 if "Gulvvarme" in delivery_label else 60.0

with col2:
    berg_temp = st.slider(
        "Bergtemperatur (°C)", 4.0, 12.0,
        float(HEAT_PUMP_CONFIG["berg_temp_c_default"]), step=0.5,
        help="Stabil temperatur i bergbrønnen. Typisk 6–8 °C i Bergen.",
    )
    st.caption(
        "Tanktype: **nedgravd** (forutsettes for v1). "
        "Tanken varierer fra ~7 °C (mars) til ~11 °C (september)."
    )

# --- Run simulation --------------------------------------------------------
sim = heat_pump_supplement_simulation(
    df, berg_temp_c=berg_temp,
    delivery_temp_c=delivery_temp,
    annual_demand_kwh=annual_demand,
)

# Compute baseline (berg-only) electricity for comparison
cop_berg_only = cop_estimate(berg_temp, delivery_temp)
elec_baseline = annual_demand / cop_berg_only if cop_berg_only > 0 else annual_demand
elec_with_rainwater = sim["kwh_electricity"].sum()
electricity_saved = max(0.0, elec_baseline - elec_with_rainwater)

ts = tank_temperature_series(df, "nedgravd")
cop_summary = annual_cop_improvement(ts, berg_temp, delivery_temp)

# --- Headline metrics ------------------------------------------------------
st.markdown("---")
st.subheader("Årlig effekt")

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "COP berg alene",
    f"{cop_summary['cop_baseline']:.2f}",
    help="Gjennomsnittlig varmefaktor med kun bergbrønnen som kilde.",
)
m2.metric(
    "COP med regnvann",
    f"{cop_summary['cop_with_rainwater']:.2f}",
    delta=f"+{cop_summary['cop_uplift']:.2f}",
    help="Gjennomsnittlig COP når regnvann brukes som kilde der det er varmere enn berget.",
)
m3.metric(
    "Strøm spart",
    f"{electricity_saved:,.0f} kWh",
    help=f"Reduksjon i årlig elektrisitetsforbruk vs. baseline (kun berg). "
         f"Ved {1.20:.2f} kr/kWh: {electricity_saved * 1.20:,.0f} kr/år.",
)
m4.metric(
    "CO₂ spart (EU-grid)",
    f"{electricity_saved * 250 / 1000:,.0f} kg",
    help="Hvis spart strøm hadde kommet fra et gjennomsnittlig EU-nett (250 g CO₂/kWh).",
)

# --- COP through year ------------------------------------------------------
st.markdown("---")
st.subheader("COP gjennom året")
st.markdown(
    "Grafen viser daglig COP når regnvann velges som kilde der det er varmere enn berget. "
    "Den stiplede linjen er COP for kun bergbrønnen — flat fordi bergtemperaturen er stabil."
)

cop_chart_df = sim[sim["kwh_demand"] > 0].copy()
cop_chart_df["cop_baseline"] = cop_summary["cop_baseline"]

cop_chart = alt.Chart(cop_chart_df).mark_line(
    color="#2E86AB", interpolate="monotone",
).encode(
    x=alt.X("date:T", title="Dato"),
    y=alt.Y("cop_used:Q", title="COP", scale=alt.Scale(zero=False)),
    tooltip=[
        alt.Tooltip("date:T", title="Dato"),
        alt.Tooltip("cop_used:Q", title="COP", format=".2f"),
        alt.Tooltip("source:N", title="Kilde"),
        alt.Tooltip("tank_temp_c:Q", title="Tank (°C)", format=".1f"),
    ],
).properties(height=300)

baseline_rule = alt.Chart(cop_chart_df).mark_line(
    strokeDash=[4, 4], color="#888",
).encode(
    x="date:T",
    y="cop_baseline:Q",
)

st.altair_chart(cop_chart + baseline_rule, use_container_width=True)

# --- Source prioritization ------------------------------------------------
st.markdown("---")
st.subheader("Kildeprioritering gjennom året")
st.markdown(
    "Hvilke dager har regnvann eller berg som varmekilde? "
    "Regnvann velges når tanken er varmere enn berget."
)

source_active = sim[sim["kwh_demand"] > 0].copy()
source_chart = alt.Chart(source_active).mark_bar().encode(
    x=alt.X("date:T", title="Dato"),
    y=alt.Y("kwh_demand:Q", title="Daglig varmebehov (kWh)"),
    color=alt.Color(
        "source:N", title="Kilde",
        scale=alt.Scale(domain=["rainwater", "berg"], range=["#2E86AB", "#8B5A2B"]),
    ),
    tooltip=[
        alt.Tooltip("date:T", title="Dato"),
        alt.Tooltip("source:N", title="Kilde"),
        alt.Tooltip("kwh_demand:Q", title="Behov (kWh)", format=".0f"),
        alt.Tooltip("kwh_electricity:Q", title="Strøm (kWh)", format=".0f"),
    ],
).properties(height=250)
st.altair_chart(source_chart, use_container_width=True)

st.caption(
    f"Dager der regnvann er valgt: **{cop_summary['rainwater_dominant_days']}** "
    f"(av 365). Disse er fordelt over sommer-, høst- og tidlig vinterdager når "
    f"tanken fortsatt holder restvarme fra sommerhalvåret."
)

# --- Cumulative savings ---------------------------------------------------
st.markdown("---")
st.subheader("Akkumulerte besparelser")

sim_sorted = sim.sort_values("date").copy()
sim_sorted["cumulative_savings"] = sim_sorted["kwh_savings_vs_berg"].cumsum()

cum_chart = alt.Chart(sim_sorted).mark_area(
    opacity=0.6, color="#1B813E", interpolate="monotone",
).encode(
    x=alt.X("date:T", title="Dato"),
    y=alt.Y("cumulative_savings:Q", title="Akkumulert strøm spart (kWh)"),
    tooltip=[
        alt.Tooltip("date:T", title="Dato"),
        alt.Tooltip("cumulative_savings:Q", title="kWh spart", format=",.0f"),
    ],
).properties(height=250)
st.altair_chart(cum_chart, use_container_width=True)

# --- Thermal regeneration --------------------------------------------------
st.markdown("---")
st.subheader("Termisk regenerering av bergbrønnen")
st.markdown(
    "Hver vinter trekkes varme ut av bergbrønnen, og temperaturen synker over tid "
    "hvis brønnen ikke får regenerere. Når regnvannstanken brukes som primærkilde "
    "om sommeren og høsten, lar bergbrønnen \"hvile\" — temperaturen i berget kan "
    "stige igjen før neste fyringssesong.\n\n"
    "Dette gir **økt levetid** for bergvarmesystemet og **høyere COP over tid** "
    "sammenlignet med systemer som bare henter fra berg hele året."
)

# --- Footer ----------------------------------------------------------------
st.markdown("---")
st.caption(
    "COP-modellen er Carnot × 0.45 (typisk praktisk virkningsgrad for moderne "
    "vann/vann-varmepumpe). Daglig varmefordeling bruker en enkel "
    f"gradedags-tilnærming basert på terskeltemperatur "
    f"{HEAT_PUMP_CONFIG['heating_season_air_temp_c']:.0f} °C. "
    "Den økonomiske verdien av strømbesparelsen vises på siden **7 Lønnsomhet**."
)
