import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import altair as alt
import pandas as pd
from backend.config import DB_PATH, default_date_range
from backend.database import init_db, get_observations
from backend.analysis import (
    Building, HEAT_PUMP_CONFIG, annual_cooling_simulation,
    cop_estimate, heat_pump_supplement_simulation, water_collected,
)
from backend.lonnsomhet import INSTALLATION_UNIT_COSTS, investment_analysis
from backend.scales import SCALES

st.set_page_config(page_title="Lønnsomhet", page_icon="💰")
st.title("Lønnsomhet — investeringsanalyse")

# --- Scale gate -------------------------------------------------------------
scale_key = st.session_state.get("scale", "household")
if scale_key == "household":
    st.info(
        "**Denne modulen gjelder ikke for husholdningsskala.**\n\n"
        "Lønnsomhetskalkylen forutsetter et større anlegg med integrert "
        "passiv kjøling og bergvarmesupplering. Bytt skala til "
        "**Nabolag** eller **Kritisk infrastruktur** på hovedsiden."
    )
    st.stop()

st.markdown(
    "Hva er den totale verdien av integrasjonen — regnvann som beredskap, "
    "passiv kjøling og bergvarmesupplering? Denne siden samler alle tre "
    "verdistrømmene og sammenligner med investerings- og driftskostnader."
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

# --- Scenario inputs (read from session_state with defaults) ---------------
st.markdown("---")
st.subheader("Scenario")

default_roof = int(st.session_state.get("roof_area_m2", 2000))
default_pop = int(st.session_state.get("population", 200))
default_tank = int(st.session_state.get("tank_liters", 50_000))

col1, col2 = st.columns(2)
with col1:
    roof_area = st.number_input(
        "Takareal (m²)", min_value=200, max_value=50_000,
        value=min(50_000, max(200, default_roof)), step=100,
    )
    tank_liters = st.number_input(
        "Tankkapasitet (liter)", min_value=5_000, max_value=500_000,
        value=min(500_000, max(5_000, default_tank)), step=1_000,
    )
with col2:
    population = st.number_input(
        "Antall personer (beredskap)", min_value=1, max_value=5_000,
        value=min(5_000, max(1, default_pop)), step=10,
    )
    annual_demand = st.number_input(
        "Årlig varmebehov (kWh)", min_value=10_000, max_value=2_000_000,
        value=int(HEAT_PUMP_CONFIG["annual_demand_kwh_default"]), step=5_000,
    )

analysis_years = st.slider("Analyseperiode (år)", 10, 30, 20)

# --- Sensitivity sliders --------------------------------------------------
st.markdown("##### Prisparametere (juster for å se sensitivitet)")
scol1, scol2, scol3 = st.columns(3)
with scol1:
    elec_price = st.slider(
        "Strømpris (NOK/kWh)", 0.80, 2.50,
        INSTALLATION_UNIT_COSTS["electricity_price_kwh"], step=0.10,
    )
with scol2:
    water_price = st.slider(
        "Vannpris (NOK/L)", 0.010, 0.050,
        INSTALLATION_UNIT_COSTS["water_price_per_liter"], step=0.005,
        format="%.3f",
        help="Bergen kommune ligger typisk på 0.025–0.040 NOK/L "
             "(inkludert avløp).",
    )
with scol3:
    cooling_value = st.slider(
        "Kjøleverdi (NOK/kWh)", 0.20, 1.50,
        INSTALLATION_UNIT_COSTS["cooling_value_per_kwh"], step=0.10,
        help="Verdi per kWh kjøleenergi spart vs. aktiv AC. "
             "Konservativt estimat: 0.30–0.80.",
    )

# --- Run all upstream simulations silently --------------------------------
buildings = [Building("aggregert", roof_area_m2=roof_area)]

# Annual water collected
total_rain_mm = df["precipitation_mm"].sum()
annual_water = water_collected(total_rain_mm, roof_area)

# Cooling
cooling_sim = annual_cooling_simulation(
    df, buildings, tank_liters, population, tank_type="nedgravd",
)
annual_cooling_kwh = float(cooling_sim["cooling_kwh"].sum())

# Heat pump supplement (electricity saved vs berg-only baseline)
hp_sim = heat_pump_supplement_simulation(
    df, annual_demand_kwh=annual_demand,
)
cop_baseline = cop_estimate(HEAT_PUMP_CONFIG["berg_temp_c_default"])
elec_baseline = annual_demand / cop_baseline if cop_baseline > 0 else annual_demand
elec_with = float(hp_sim["kwh_electricity"].sum())
electricity_saved = max(0.0, elec_baseline - elec_with)

# --- Investment analysis --------------------------------------------------
result = investment_analysis(
    tank_capacity_liters=tank_liters,
    roof_area_m2=roof_area,
    annual_water_liters=annual_water,
    annual_cooling_kwh=annual_cooling_kwh,
    annual_electricity_saved_kwh=electricity_saved,
    years=analysis_years,
    electricity_price_kwh=elec_price,
    water_price_per_liter=water_price,
    cooling_value_per_kwh=cooling_value,
)

# --- Headline metrics -----------------------------------------------------
st.markdown("---")
st.subheader("Hovedtall")

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Investering",
    f"{result['capex']['total']:,.0f} kr",
    help="Total kapitalkostnad: tank, varmeveksler, pumpe, rør, installasjon.",
)
m2.metric(
    "Årlig besparelse",
    f"{result['annual_savings_total']:,.0f} kr",
    help="Brutto besparelse minus årlig vedlikehold (2 % av kapital).",
)
payback = result["payback_years"]
m3.metric(
    "Tilbakebetalingstid",
    f"{payback:.1f} år" if payback else "> {0} år".format(analysis_years),
    help="År før akkumulerte besparelser overstiger investeringen.",
)
m4.metric(
    f"Netto verdi etter {analysis_years} år",
    f"{result['npv']:,.0f} kr",
    help="Akkumulert kontantstrøm: besparelser − investering − vedlikehold. "
         "Udiskontert (no NPV discount applied).",
)

# --- Cumulative savings curve ---------------------------------------------
st.markdown("---")
st.subheader(f"Akkumulert besparelse over {analysis_years} år")
st.markdown(
    "Kurven starter i minus (investeringskostnaden) og stiger med årlig "
    "besparelse. Krysser kurven null-linjen er det tilbakebetalt."
)

cum_df = pd.DataFrame({
    "år": list(range(analysis_years + 1)),
    "kr": result["cumulative_savings"],
})
cum_chart = alt.Chart(cum_df).mark_area(
    opacity=0.6, color="#1B813E", interpolate="monotone",
).encode(
    x=alt.X("år:Q", title="År"),
    y=alt.Y("kr:Q", title="Akkumulert (NOK)"),
    tooltip=[
        alt.Tooltip("år:Q"),
        alt.Tooltip("kr:Q", format=",.0f", title="Akkumulert (NOK)"),
    ],
).properties(height=300)
zero_rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
    color="#888", strokeDash=[4, 4],
).encode(y="y:Q")
st.altair_chart(cum_chart + zero_rule, use_container_width=True)

# --- Investment breakdown -------------------------------------------------
st.markdown("---")
st.subheader("Investering — fordeling")

capex_items = result["capex"]
breakdown_df = pd.DataFrame([
    {"kategori": "Tank", "kr": capex_items["tank"]},
    {"kategori": "Varmeveksler", "kr": capex_items["heat_exchanger"]},
    {"kategori": "Pumpe og styring", "kr": capex_items["pump_and_controls"]},
    {"kategori": "Rør og takrenner", "kr": capex_items["piping"]},
    {"kategori": "Installasjonsarbeid", "kr": capex_items["labor"]},
])
capex_chart = alt.Chart(breakdown_df).mark_bar(color="#2E86AB").encode(
    x=alt.X("kr:Q", title="Kostnad (NOK)"),
    y=alt.Y("kategori:N", title="", sort="-x"),
    tooltip=["kategori:N", alt.Tooltip("kr:Q", format=",.0f")],
).properties(height=200)
st.altair_chart(capex_chart, use_container_width=True)

# --- Annual savings breakdown ---------------------------------------------
st.markdown("---")
st.subheader("Årlig besparelse — fordeling")

savings = result["savings"]
savings_df = pd.DataFrame([
    {"kategori": "Vann", "kr": savings["water"]},
    {"kategori": "Kjøling", "kr": savings["cooling"]},
    {"kategori": "Strøm (varmepumpe)", "kr": savings["electricity"]},
])
savings_chart = alt.Chart(savings_df).mark_bar(color="#1B813E").encode(
    x=alt.X("kr:Q", title="Årlig besparelse (NOK)"),
    y=alt.Y("kategori:N", title="", sort="-x"),
    tooltip=["kategori:N", alt.Tooltip("kr:Q", format=",.0f")],
).properties(height=150)
st.altair_chart(savings_chart, use_container_width=True)

st.caption(
    f"Brutto årlig besparelse: **{result['annual_savings_gross']:,.0f} kr**. "
    f"Årlig vedlikehold (2 % av investering): **{result['annual_maintenance']:,.0f} kr**. "
    f"Netto årlig: **{result['annual_savings_total']:,.0f} kr**."
)

# --- Underlying input summary ---------------------------------------------
with st.expander("Bakgrunnsdata for kalkylen"):
    st.markdown(f"""
    - **Årlig regnvann samlet:** {annual_water:,.0f} L
    - **Årlig kjøling (passiv):** {annual_cooling_kwh:,.0f} kWh
    - **Strøm spart (bergvarme + regnvann):** {electricity_saved:,.0f} kWh
    - **Tankkapasitet:** {tank_liters:,} L
    - **Takareal:** {roof_area:,} m²
    - **Befolkning (beredskap):** {population:,}
    """)

# --- Municipal relevance --------------------------------------------------
st.markdown("---")
st.subheader("Kommunal relevans og tilskudd")
st.markdown(
    "Direkte privatøkonomisk tilbakebetaling er ofte ikke det fullstendige bildet. "
    "Verdiene under er ikke kvantifisert her, men kan styrke prosjektøkonomien:\n\n"
    "- **Overvannshåndtering:** Bergen kommune har behov for å redusere "
    "spissavrenning. Lagring av regnvann reduserer belastningen på avløpsnettet og "
    "kan kvalifisere for kommunale tilskudd.\n"
    "- **Klimatilpasningstilskudd (Enova):** Anlegg som kombinerer beredskap, "
    "energieffektivisering og klimatilpasning kan kvalifisere for støtteordninger.\n"
    "- **Termisk regenerering:** Vist på siden **6 Varmesystem** — sparer bergbrønnen "
    "og forlenger anleggets levetid.\n"
    "- **Beredskapsverdi:** WHO-standard vannforsyning i krise er vanskelig å prise "
    "i NOK, men har samfunnsmessig verdi som ikke fanges av direkte besparelser."
)

# --- Footer ----------------------------------------------------------------
st.markdown("---")
st.caption(
    "Modellen er udiskontert (ingen NPV-diskontering). For mer presise beregninger "
    "bør en realrente på 3–5 % brukes. Prisestimatene er 2024-vintage og bør "
    "verifiseres mot lokale leverandører før reell beslutning. "
    "Tilbakebetaling avhenger særlig sterkt av vannpris (sensitivitetslider over)."
)
