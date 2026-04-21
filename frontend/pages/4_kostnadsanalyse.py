import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import altair as alt
import pandas as pd
from backend.config import DB_PATH, default_date_range
from backend.database import init_db, get_observations
from backend.analysis import water_collected, Building, BUILDING_PRESETS
from backend.economics import (
    COST_ESTIMATES, CAPITAL_CATEGORIES, OPERATING_CATEGORIES,
    find_best_estimate, interpolate_cost, lifecycle_cost,
    cost_per_person, cost_per_liter, cost_breakdown,
)

st.set_page_config(page_title="Kostnadsanalyse", page_icon="💰")
st.title("Kostnadsanalyse")
st.markdown(
    "Hva koster et regnvannsoppsamlingssystem for beredskap? "
    "Denne siden gir indikative kostnadsestimater basert på systemtype og størrelse, "
    "med livsløpskostnader over 10, 20 og 30 år."
)


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

# --- Scenario ---
st.subheader("Ditt scenario")

col1, col2 = st.columns(2)
with col1:
    preset_keys = list(BUILDING_PRESETS.keys())
    preset_labels = [BUILDING_PRESETS[k]["label"] for k in preset_keys]
    selected_label = st.selectbox("Bygningstype", preset_labels)
    selected_key = preset_keys[preset_labels.index(selected_label)]
    preset = BUILDING_PRESETS[selected_key]
with col2:
    population = st.slider("Befolkning", 1, 2000, preset["default_people"])

roof_area = preset["roof_area_m2"]
total_rain = df["precipitation_mm"].sum()
annual_liters = water_collected(total_rain, roof_area)

# Find matching cost tier
est = find_best_estimate(population)
capital, annual_op = interpolate_cost(population, est)

# --- Key metrics ---
st.markdown("---")
st.subheader("Kostnadsestimat")
st.markdown(
    f"Basert på systemtype **{est.label}** for **{population} personer**. "
    f"Kostnadene er indikative og avhenger av lokale forhold, takets tilstand, "
    f"og valgt behandlingsnivå."
)

c1, c2, c3 = st.columns(3)
c1.metric(
    "Investeringskostnad",
    f"{capital:,.0f} kr",
    help=f"Estimert kapitalkostnad (spenn: {est.capital_low:,.0f} – {est.capital_high:,.0f} kr). "
         f"Inkluderer tank, behandling, rør, prosjektering og godkjenning.",
)
c2.metric(
    "Årlig drift",
    f"{annual_op:,.0f} kr/år",
    help=f"Estimert årlig driftskostnad (spenn: {est.annual_operating_low:,.0f} – {est.annual_operating_high:,.0f} kr). "
         f"Inkluderer filter, testing, rengjøring, vedlikehold og tilsyn.",
)
c3.metric(
    "Kostnad per person",
    f"{cost_per_person(capital, population):,.0f} kr",
    help="Investeringskostnad fordelt per person.",
)

# --- Cost range ---
st.markdown("---")
st.subheader("Kostnadsoversikt per systemtype")
st.markdown("Tabellen viser kostnadsintervallene for ulike systemtyper (alle beløp i NOK).")

range_data = {
    "Systemtype": [e.label for e in COST_ESTIMATES],
    "Investering (lav)": [f"{e.capital_low:,.0f}" for e in COST_ESTIMATES],
    "Investering (høy)": [f"{e.capital_high:,.0f}" for e in COST_ESTIMATES],
    "Årlig drift (lav)": [f"{e.annual_operating_low:,.0f}" for e in COST_ESTIMATES],
    "Årlig drift (høy)": [f"{e.annual_operating_high:,.0f}" for e in COST_ESTIMATES],
    "Kapasitet (personer)": [f"{e.capacity_low}–{e.capacity_high}" for e in COST_ESTIMATES],
}
st.dataframe(range_data, use_container_width=True, hide_index=True)

# --- Lifecycle cost chart ---
st.markdown("---")
st.subheader("Livsløpskostnad")
st.markdown(
    "Grafen viser total kostnad (investering + akkumulert drift) over tid. "
    "Godt designede systemer har en levetid på 20–40 år."
)

years_range = list(range(0, 31))
lifecycle_data = pd.DataFrame({
    "År": years_range,
    "Total kostnad (kr)": [lifecycle_cost(capital, annual_op, y) for y in years_range],
    "Driftskostnad (kr)": [annual_op * y for y in years_range],
})

line_chart = alt.Chart(lifecycle_data).mark_area(
    opacity=0.6, interpolate="monotone", color="#2E86AB",
).encode(
    x=alt.X("År:Q", title="År"),
    y=alt.Y("Total kostnad (kr):Q", title="Akkumulert kostnad (NOK)", axis=alt.Axis(format=",.0f")),
    tooltip=[
        alt.Tooltip("År:Q"),
        alt.Tooltip("Total kostnad (kr):Q", format=",.0f"),
    ],
)

st.altair_chart(line_chart, use_container_width=True)

# Lifecycle metrics
lc1, lc2, lc3 = st.columns(3)
lc1.metric("10 år", f"{lifecycle_cost(capital, annual_op, 10):,.0f} kr")
lc2.metric("20 år", f"{lifecycle_cost(capital, annual_op, 20):,.0f} kr")
lc3.metric("30 år", f"{lifecycle_cost(capital, annual_op, 30):,.0f} kr")

# Cost per liter
if annual_liters > 0:
    cpl_20 = cost_per_liter(lifecycle_cost(capital, annual_op, 20), annual_liters, 20)
    st.metric(
        "Kostnad per liter (20 år)",
        f"{cpl_20:.2f} kr/L",
        help="Total livsløpskostnad over 20 år delt på totalt oppsamlet vann i samme periode.",
    )

# --- Cost breakdown ---
st.markdown("---")
st.subheader("Kostnadsfordeling")

col_cap, col_op = st.columns(2)

with col_cap:
    st.markdown("##### Investering")
    cap_breakdown = cost_breakdown(capital, CAPITAL_CATEGORIES)
    cap_df = pd.DataFrame(cap_breakdown, columns=["Kategori", "Beløp (kr)"])
    st.dataframe(cap_df, use_container_width=True, hide_index=True)

with col_op:
    st.markdown("##### Årlig drift")
    op_breakdown = cost_breakdown(annual_op, OPERATING_CATEGORIES)
    op_df = pd.DataFrame(op_breakdown, columns=["Kategori", "Beløp (kr)"])
    st.dataframe(op_df, use_container_width=True, hide_index=True)

# --- Government pitch ---
st.markdown("---")
st.subheader("Nyttevurdering for offentlig investering")
st.markdown(
    "For offentlige beslutningstakere er følgende nytteverdier relevante:"
)

benefits = [
    ("Unngåtte krisekostnader", "Kostnadene ved nød-vannforsyning med flaskevann, tankbiler og sivilforsvarsmobilisering er svært høye. Selv ett unngått større hendelse kan forsvare investeringen."),
    ("Folkehelsebeskyttelse", "Opprettholdelse av drikkevannstilgang under kriser forebygger vannbårne sykdommer og reduserer belastningen på helsevesenet."),
    ("Forsikringsverdi", "Lavere sannsynlighet for katastrofal forsyningssvikt reduserer kommunalt ansvar og forsikringsrisiko."),
    ("Dobbeltbruksdividende", "Systemer designet for normalbruk (toalettspyling, vanning) kompenserer driftskostnader gjennom redusert kommunalt vannforbruk."),
    ("Klimatilpasning", "Investeringen teller mot Bergens klimatilpasningsforpliktelser under Klimaplan for Bergen 2030."),
    ("Lang levetid", "Godt designede systemer har 20–40 års operasjonell levetid."),
]

for title, desc in benefits:
    st.markdown(f"- **{title}** — {desc}")

# --- Footer ---
st.markdown("---")
st.caption(
    "Kostnadsestimatene er indikative og basert på rammeverket i "
    "\"Emergency Rainwater Supply Potential in Bergen\" (seksjon 14). "
    "Alle beløp i NOK. Faktiske kostnader avhenger av lokale forhold."
)
