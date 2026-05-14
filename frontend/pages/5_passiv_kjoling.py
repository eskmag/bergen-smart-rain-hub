import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import altair as alt
import pandas as pd
from backend.config import DB_PATH, default_date_range
from backend.database import init_db, get_observations
from backend.analysis import (
    Building, COOLING_CONFIG, EMERGENCY_RESERVE_DAYS, EMERGENCY_RESERVE_PCT,
    annual_cooling_simulation, emergency_reserve_liters,
)
from backend.scales import SCALES

st.set_page_config(page_title="Passiv kjøling", page_icon="❄️")
st.title("Passiv kjøling")

# --- Scale gate -------------------------------------------------------------
scale_key = st.session_state.get("scale", "household")
if scale_key == "household":
    st.info(
        "**Denne modulen gjelder ikke for husholdningsskala.**\n\n"
        "Passiv kjøling utnytter et felles vannbårent gulvvarmesystem og krever "
        "et større bygg med eksisterende infrastruktur — typisk borettslag, skole, "
        "sykehjem eller næringsbygg.\n\n"
        "Bytt skala til **Nabolag** eller **Kritisk infrastruktur** på hovedsiden "
        "for å se hvordan en regnvannstank kan brukes til kjøling om sommeren."
    )
    st.stop()

st.markdown(
    "Regnvann i en nedgravd tank holder seg på 7–11 °C året rundt. "
    "Om sommeren kan dette sirkuleres gjennom et eksisterende gulvvarmesystem "
    "i reversert modus — uten kompressor — for å gi gratis kjøling. "
    "Beredskapsvolumet i tanken er **alltid beskyttet** og kan ikke tappes til kjøleformål."
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
st.subheader("Konfigurasjon")

default_roof = int(st.session_state.get("roof_area_m2", 2000))
default_pop = int(st.session_state.get("population", 200))
default_tank = int(st.session_state.get("tank_liters", 50_000))

col1, col2 = st.columns(2)
with col1:
    roof_area = st.number_input(
        "Samlet takareal (m²)", min_value=200, max_value=50_000,
        value=min(50_000, max(200, default_roof)), step=100,
        help="Aggregert takareal som mater tanken.",
    )
    floor_area = st.number_input(
        "Gulvareal med vannbåren varme (m²)", min_value=100, max_value=20_000,
        value=int(roof_area * COOLING_CONFIG["floor_area_per_roof_m2"]), step=50,
        help="Areal med eksisterende vannbårne gulvvarmeslynger som kan reverseres "
             "for kjøling. Standard antar 80 % av takarealet.",
    )
with col2:
    tank_liters = st.number_input(
        "Tankkapasitet (liter)", min_value=5_000, max_value=500_000,
        value=min(500_000, max(5_000, default_tank)), step=1_000,
        help="Total vannkapasitet i den nedgravde tanken.",
    )
    population = st.number_input(
        "Antall personer (beredskap)", min_value=1, max_value=5_000,
        value=min(5_000, max(1, default_pop)), step=10,
        help="Antall personer det skal være beredskapsvann for.",
    )

room_temp = st.slider(
    "Mål-romtemperatur (°C)", 21.0, 26.0,
    float(COOLING_CONFIG["default_room_temp_c"]), step=0.5,
    help="Innendørs temperatur som skal opprettholdes ved kjøling.",
)

st.markdown("##### Låst beredskapsreserve")
rcol1, rcol2 = st.columns(2)
with rcol1:
    reserve_days = st.slider(
        "Reservedager", 3, 14, EMERGENCY_RESERVE_DAYS,
        help="Antall dager med vann som alltid skal være låst i tanken (13 L/person/dag).",
    )
with rcol2:
    reserve_pct = st.slider(
        "Reserveandel (%)", 10, 50, int(EMERGENCY_RESERVE_PCT * 100),
        help="Andel av tankkapasiteten som alltid skal være låst.",
    ) / 100

reserve_liters = emergency_reserve_liters(tank_liters, population, reserve_days, reserve_pct)
st.caption(
    f"Låst beredskap: **{reserve_liters:,.0f} L** "
    f"(maks av {reserve_days} dager × {population} personer × 13 L/dag og "
    f"{reserve_pct*100:.0f} % × {tank_liters:,} L)"
)

# --- Run simulation --------------------------------------------------------
buildings = [Building("aggregert", roof_area_m2=roof_area)]
sim = annual_cooling_simulation(
    df, buildings, tank_liters, population,
    tank_type="nedgravd", room_temp_c=room_temp,
    floor_area_m2=floor_area,
    reserve_days=reserve_days, reserve_pct=reserve_pct,
)

annual_cooling_kwh = sim["cooling_kwh"].sum()
active_days = int(sim["cooling_active"].sum())
electricity_saved_kwh = annual_cooling_kwh  # 1:1 — passive replaces electric AC
nok_saved = annual_cooling_kwh * COOLING_CONFIG["passive_cooling_cop_factor"] * 0.0  # placeholder, NOK calc on lønnsomhet page
co2_saved_kg_eu = annual_cooling_kwh * 250 / 1000  # EU avg grid

# --- Headline metrics ------------------------------------------------------
st.markdown("---")
st.subheader("Årlig kjølepotensial")

m1, m2, m3 = st.columns(3)
m1.metric(
    "Total kjøleenergi",
    f"{annual_cooling_kwh:,.0f} kWh",
    help="Total kjøleenergi tilgjengelig fra tanken gjennom året, "
         "begrenset av disponibelt volum og effektiv sirkulasjonsmasse.",
)
m2.metric(
    "Aktive kjøledager",
    f"{active_days}",
    help="Antall dager der utetemperatur > 14 °C og tanken er kjølig nok til å levere kjøling.",
)
m3.metric(
    "CO₂-besparelse (EU-grid)",
    f"{co2_saved_kg_eu:,.0f} kg",
    help="Hvis kjølingen erstatter aktiv aircondition med strøm fra et "
         "gjennomsnittlig EU-nett (250 g CO₂/kWh).",
)

# --- Tank vs air temperature chart -----------------------------------------
st.markdown("---")
st.subheader("Tank- og lufttemperatur gjennom året")
st.markdown(
    "Den blå linjen er estimert tanktemperatur (nedgravd, lagger 2 mnd etter luft). "
    "Den oransje linjen er utetemperatur fra Frost API (faller tilbake til "
    "Bergen-normaler hvis ikke tilgjengelig). "
    "Gråsonen markerer perioden hvor passiv kjøling er aktuell — "
    f"når tanken er kaldere enn {COOLING_CONFIG['critical_tank_temp_c']:.0f} °C "
    f"og lufta er over {COOLING_CONFIG['cooling_season_air_temp_c']:.0f} °C."
)

temp_long = pd.melt(
    sim, id_vars=["date"],
    value_vars=["tank_temp_c", "air_temp_c"],
    var_name="type", value_name="temp_c",
)
temp_long["type"] = temp_long["type"].map({
    "tank_temp_c": "Tanktemperatur",
    "air_temp_c": "Lufttemperatur",
})

temp_chart = alt.Chart(temp_long).mark_line(interpolate="monotone").encode(
    x=alt.X("date:T", title="Dato"),
    y=alt.Y("temp_c:Q", title="Temperatur (°C)"),
    color=alt.Color("type:N", title="",
                    scale=alt.Scale(domain=["Tanktemperatur", "Lufttemperatur"],
                                    range=["#2E86AB", "#E85D04"])),
).properties(height=300)

cooling_threshold = alt.Chart(pd.DataFrame({"y": [COOLING_CONFIG["critical_tank_temp_c"]]})).mark_rule(
    color="#888", strokeDash=[4, 4],
).encode(y="y:Q")

st.altair_chart(temp_chart + cooling_threshold, use_container_width=True)

# --- Daily cooling potential -----------------------------------------------
st.markdown("---")
st.subheader("Daglig kjølepotensial")
st.markdown(
    "Stolpene viser hvor mange kWh kjøleenergi som er tilgjengelig hver dag. "
    "Begrensningene er disponibelt volum (etter låst beredskap) og effektiv "
    "sirkulasjonsmasse i gulvkretsen."
)

active_only = sim[sim["cooling_active"]]
if active_only.empty:
    st.info("Ingen aktive kjøledager funnet i denne perioden.")
else:
    cooling_chart = alt.Chart(active_only).mark_bar(color="#2E86AB").encode(
        x=alt.X("date:T", title="Dato"),
        y=alt.Y("cooling_kwh:Q", title="Kjøleenergi (kWh)"),
        tooltip=[
            alt.Tooltip("date:T", title="Dato"),
            alt.Tooltip("cooling_kwh:Q", title="kWh", format=".2f"),
            alt.Tooltip("tank_temp_c:Q", title="Tank (°C)", format=".1f"),
            alt.Tooltip("air_temp_c:Q", title="Luft (°C)", format=".1f"),
        ],
    ).properties(height=300)
    st.altair_chart(cooling_chart, use_container_width=True)

# --- Reserve indicator -----------------------------------------------------
st.markdown("---")
st.subheader("Beredskapsvolum")
st.markdown(
    "Beredskapsvolumet er **alltid beskyttet** — kjølesystemet får kun "
    "tappe det grå feltet (disponibelt volum). Lås du opp mer beredskap "
    "(høyere reservedager eller -andel) reduseres kjølepotensialet."
)

avg_available = sim["available_liters"].mean()
avg_locked = reserve_liters
avg_total_used = avg_locked + avg_available

reserve_data = pd.DataFrame({
    "kategori": ["Låst beredskap", "Disponibelt (gj.snitt)"],
    "liter": [avg_locked, avg_available],
})
reserve_chart = alt.Chart(reserve_data).mark_bar().encode(
    x=alt.X("liter:Q", title="Liter", stack="zero"),
    y=alt.Y("kategori:N", title=""),
    color=alt.Color("kategori:N",
                    scale=alt.Scale(domain=["Låst beredskap", "Disponibelt (gj.snitt)"],
                                    range=["#C1292E", "#2E86AB"])),
    tooltip=["kategori:N", alt.Tooltip("liter:Q", format=",.0f")],
).properties(height=120)
st.altair_chart(reserve_chart, use_container_width=True)

# --- Footer ----------------------------------------------------------------
st.markdown("---")
st.caption(
    "Beregningen bruker en forenklet termodynamisk modell: "
    f"effektiv vannmasse er begrenset til {COOLING_CONFIG['floor_area_per_roof_m2']*100:.0f} % "
    "av takarealet × 2 kg/m² (typisk gulvkrets). "
    "Den økonomiske verdien av kjølingen vises på siden **7 Lønnsomhet**."
)
