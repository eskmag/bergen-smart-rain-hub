import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import altair as alt
from backend.database import init_db, get_observations
from backend.analysis import (
    water_collected, monthly_summary,
    emergency_supply_days, WATER_NEEDS,
)

st.set_page_config(page_title="Bergen Smart Rain Hub", page_icon="🌧️", layout="wide")
st.title("Bergen Smart Rain Hub")

st.markdown(
    "**Bergen Smart Rain Hub** analyserer nedbørsdata fra Bergen for å kartlegge potensialet "
    "for regnvannsoppsamling som **beredskapsressurs**. Ved vannkrise, forurensning eller "
    "infrastruktursvikt kan oppsamlet regnvann sikre vannforsyning for enkeltpersoner, "
    "lokalsamfunn og kommunale beredskapsplaner."
)

st.info(
    "**Hvordan fungerer dette?** Regn som faller på et tak kan samles opp via takrenner "
    "og lagres i tanker. Vi bruker ekte nedbørsdata fra Meteorologisk Institutt sin "
    "målestasjon på Florida i Bergen til å beregne hvor mye vann som kan samles opp, "
    "og hvor lenge det kan forsyne mennesker i en krisesituasjon."
)

# Load data
conn = init_db()
df = get_observations(conn, "2025-04-13", "2026-04-12")
conn.close()

if df.empty:
    st.warning("Ingen data funnet. Kjør `python -m backend.pipeline` for å hente data.")
    st.stop()

# --- Today's snapshot ---
st.subheader("Dagens oversikt")
st.markdown(
    "Tallene under viser nedbør for siste registrerte dag, og hva det betyr "
    "for vannoppsamling fra et vanlig norsk hustak (150 m²). "
    "Vi regner med 85 % oppsamlingseffektivitet — resten går tapt til avrenning og fordamping."
)

latest = df.iloc[-1]
rain_today = latest["precipitation_mm"]
roof_area = 150  # typical Norwegian house
liters_today = water_collected(rain_today, roof_area)
days_one_person = emergency_supply_days(liters_today, 1, "survival_total")

col1, col2, col3 = st.columns(3)
col1.metric(
    "Nedbør i dag",
    f"{rain_today:.1f} mm",
    help="Millimeter nedbør målt ved Bergen Florida målestasjon. 1 mm nedbør = 1 liter vann per kvadratmeter.",
)
col2.metric(
    "Oppsamlet vann (150 m² tak)",
    f"{liters_today:,.0f} L",
    help="Antall liter vann som kan samles opp fra et tak på 150 m² med 85 % effektivitet.",
)
col3.metric(
    "Beredskapsforsyning (1 person)",
    f"{days_one_person:.1f} dager",
    help=f"Antall dager vannet rekker for én person med WHO sitt beredskapsnivå ({WATER_NEEDS['survival_total']} liter/dag for drikke, matlaging, hygiene og medisinsk bruk).",
)

st.caption(
    f"Beredskapsminimum etter WHO-standard: {WATER_NEEDS['survival_total']} liter per person per dag — "
    f"dette dekker drikkevann ({WATER_NEEDS['drinking']} L), matlaging ({WATER_NEEDS['cooking']} L), "
    f"hygiene ({WATER_NEEDS['sanitation']} L) og medisinsk bruk ({WATER_NEEDS['medical']} L)."
)

# --- Daily rainfall chart (last 30 days) ---
st.subheader("Daglig nedbør — siste 30 dager")
st.markdown(
    "Diagrammet viser hvor mye regn som har falt hver dag den siste måneden. "
    "Høye søyler betyr mye nedbør og god påfylling av vannlagre. "
    "Perioder uten søyler er tørkeperioder der man er avhengig av lagret vann."
)

recent = df.tail(30).copy()
recent["date"] = recent["date"].astype(str)

chart = alt.Chart(recent).mark_bar(color="#2E86AB").encode(
    x=alt.X("date:N", title="Dato", sort=None, axis=alt.Axis(labelAngle=-45)),
    y=alt.Y("precipitation_mm:Q", title="Nedbør (mm)"),
    tooltip=["date", "precipitation_mm"],
).properties(height=350)

st.altair_chart(chart, use_container_width=True)

# --- Annual collection potential ---
st.subheader("Årlig oppsamlingspotensial")
st.markdown(
    "Hvor mye vann kan samles opp fra ett hustak i løpet av et helt år? "
    "Og hvor lenge rekker det i en beredsskapssituasjon? "
    "Tallene er basert på faktisk nedbør det siste året."
)

total_rain = df["precipitation_mm"].sum()
total_liters = water_collected(total_rain, roof_area)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Total nedbør",
    f"{total_rain:,.0f} mm",
    help="Sum av all nedbør det siste året ved målestasjonen.",
)
c2.metric(
    "Vann samlet (år)",
    f"{total_liters:,.0f} L",
    help="Totalt antall liter oppsamlet fra et 150 m² tak med 85 % effektivitet.",
)
c3.metric(
    "Beredskap 1 person",
    f"{emergency_supply_days(total_liters, 1, 'survival_total'):,.0f} dager",
    help="Antall dager hele årets oppsamling dekker for én person på beredskapsnivå.",
)
c4.metric(
    "Beredskap 4 pers. familie",
    f"{emergency_supply_days(total_liters, 4, 'survival_total'):,.0f} dager",
    help="Antall dager hele årets oppsamling dekker for en familie på fire.",
)

# --- Monthly summary ---
st.subheader("Månedlig nedbør")
st.markdown(
    "Tabellen viser nedbørsstatistikk for hver måned. "
    "**Total** er summen av all nedbør, **Snitt** er gjennomsnittet per dag, "
    "**Maks** er den mest nedbørsrike enkeltdagen, og **Regndager** er antall dager "
    "med mer enn 0,1 mm nedbør."
)
ms = monthly_summary(df)
ms.columns = ["Måned", "Total (mm)", "Snitt (mm)", "Maks (mm)", "Regndager"]
st.dataframe(ms, use_container_width=True, hide_index=True)
