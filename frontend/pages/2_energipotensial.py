import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from backend.config import DB_PATH, default_date_range
from backend.database import init_db, get_observations
from backend.analysis import (
    calculate_rain_energy, co2_offset,
    practical_equivalents, seasonal_summary,
)

st.set_page_config(page_title="Energipotensial", page_icon="⚡")
st.title("Energipotensial")
st.markdown(
    "I tillegg til vannberedskap har regnvann et teoretisk **energipotensial**. "
    "Når vann faller fra taket ned til bakken, har det energi på grunn av tyngdekraften. "
    "Denne energien kan i prinsippet fanges opp med mikroturbiner i nedløpsrør."
)

st.info(
    "**Viktig kontekst:** Energitallene her er beskjedne sammenlignet med solenergi eller vindkraft. "
    "Regnvannsoppsamling er først og fremst verdifullt som **vannressurs og beredskap** — "
    "energipotensialet er en bonus, ikke hovedargumentet."
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

# --- Configuration ---
st.subheader("Bygg-parametere")
st.markdown(
    "**Takareal** bestemmer hvor mye vann som samles opp. "
    "**Fallhøyde** er avstanden vannet faller — fra tak til bakkenivå eller tank. "
    "Høyere fall = mer energi (men vanligvis begrenset til byggets høyde)."
)

col1, col2 = st.columns(2)
with col1:
    roof_area = st.slider(
        "Takareal (m²)", 50, 2000, 200, step=50,
        help="Et vanlig hus: 100–150 m². Blokk: 300–800 m². Næringsbygg: 500–2000 m².",
    )
with col2:
    height = st.slider(
        "Fallhøyde (m)", 2, 30, 8, step=1,
        help="Høyden vannet faller fra taket. Et vanlig hus er ca. 5–8 m, en blokk 15–25 m.",
    )

# --- Annual energy ---
total_rain = df["precipitation_mm"].sum()
total_liters, total_energy_wh = calculate_rain_energy(total_rain, roof_area, height)
co2 = co2_offset(total_energy_wh)
eq = practical_equivalents(total_energy_wh)

st.subheader("Årlig energipotensial")
st.markdown(
    "Beregnet med formelen **E = mgh** (masse x tyngdekraft x høyde). "
    "Vannet som faller fra taket har en viss vekt (1 liter = 1 kg), "
    "og denne vekten ganget med fallhøyden gir energien i joule, "
    "som vi omregner til kilowattimer (kWh)."
)

c1, c2, c3 = st.columns(3)
c1.metric(
    "Teoretisk energi",
    f"{total_energy_wh/1000:,.2f} kWh",
    help="Total energi fra vannets fall det siste året. "
         "Til sammenligning bruker en norsk husholdning ca. 16 000 kWh i året.",
)
c2.metric(
    "CO₂-besparelse (EU-snitt)",
    f"{co2['EU']/1000:,.2f} kg",
    help="Hvor mye CO₂ som spares hvis denne energien erstatter strøm fra et gjennomsnittlig europeisk nett (250 g CO₂/kWh).",
)
c3.metric(
    "CO₂-besparelse (Norge)",
    f"{co2['NO']/1000:,.3f} kg",
    help="Norge har svært ren strømproduksjon (hovedsakelig vannkraft, 11 g CO₂/kWh), "
         "så besparelsen er mye lavere enn i land med mer fossil kraftproduksjon.",
)

# --- Equivalents ---
st.subheader("Hva tilsvarer energien?")
st.markdown("For å sette tallene i perspektiv — den årlige energien tilsvarer omtrent:")

e1, e2, e3, e4 = st.columns(4)
e1.metric("Mobilladinger", f"{eq['phone_charges']:,.0f}", help="Ca. 10 Wh per full lading av en moderne smarttelefon.")
e2.metric("LED-timer", f"{eq['led_bulb_hours']:,.0f}", help="Timer en 7W LED-pære kan lyse.")
e3.metric("Laptopladinger", f"{eq['laptop_charges']:,.0f}", help="Ca. 50 Wh per full lading av en bærbar PC.")
e4.metric("El-sykkel km", f"{eq['electric_bike_km']:,.0f}", help="Ca. 15 Wh per kilometer på en elektrisk sykkel.")

# --- Seasonal breakdown ---
st.subheader("Sesongfordeling nedbør")
st.markdown(
    "Bergen har tydelige sesongvariasjoner i nedbør. Høsten (september–november) "
    "er normalt den våteste perioden, mens våren ofte er tørrere. "
    "Tabellen viser hvordan nedbøren fordeler seg over årstidene."
)

ss = seasonal_summary(df)
ss.columns = ["Sesong", "Total (mm)", "Snitt per dag (mm)", "Antall dager"]
st.dataframe(ss, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(
    "Energiberegningen viser ren gravitasjonsenergi (E = mgh). "
    "I praksis kan mer avanserte systemer som trykkgjenvinning i rør, "
    "mikroturbiner, og regnvanns-varmepumper (regnvann på 5–10°C som varmekilde) "
    "utnytte energien mer effektivt enn det denne enkle beregningen viser."
)
