import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import altair as alt
from backend.database import init_db, get_observations
from backend.analysis import (
    Building, emergency_summary, storage_simulation,
    find_dry_spells, WATER_NEEDS,
)

st.set_page_config(page_title="Vannberedskap", page_icon="🚨")
st.title("Vannberedskap")
st.markdown(
    "Denne siden simulerer hvordan regnvannsoppsamling fungerer som beredskapsressurs "
    "gjennom et helt år. Du kan justere parameterne for å se hvordan ulike scenarier "
    "påvirker vanntryggheten — for en enkelt husholdning, et borettslag, eller et helt nabolag."
)

# Load data
conn = init_db()
df = get_observations(conn, "2025-04-13", "2026-04-12")
conn.close()

if df.empty:
    st.warning("Ingen data funnet. Kjør `python -m backend.pipeline` for å hente data.")
    st.stop()

# --- Configuration ---
st.subheader("Juster scenarioet")
st.markdown(
    "Bruk glidebryterne under til å tilpasse simuleringen. "
    "Prøv å endre verdiene for å se hvordan de påvirker beredskapsvurderingen."
)

col1, col2, col3 = st.columns(3)
with col1:
    roof_area = st.slider(
        "Takareal per bygg (m²)", 50, 2000, 200, step=50,
        help="Størrelsen på taket som samler opp regnvann. "
             "Et vanlig norsk hus har ca. 100–150 m², en blokk 300–800 m², "
             "et næringsbygg kan ha over 1000 m².",
    )
    num_buildings = st.slider(
        "Antall bygg", 1, 50, 5,
        help="Hvor mange bygninger som bidrar med oppsamlet regnvann. "
             "Flere bygg = større takflate = mer vann.",
    )
with col2:
    population = st.slider(
        "Befolkning (personer)", 1, 500, 50,
        help="Antall mennesker som skal forsynes med vann. "
             "En gjennomsnittlig norsk husholdning har 2,1 personer.",
    )
    tank_liters = st.slider(
        "Tankkapasitet (liter)", 1000, 100_000, 10_000, step=1000,
        help="Hvor mye vann tanken(e) kan lagre totalt. "
             "En typisk hagetank er 1 000–5 000 L, en nedgravd tank for borettslag "
             "kan være 10 000–50 000 L. 1 000 liter = 1 kubikkmeter.",
    )
with col3:
    efficiency = st.slider(
        "Oppsamlingseffektivitet (%)", 50, 95, 85,
        help="Hvor stor andel av regnvannet som faktisk havner i tanken. "
             "85 % er et realistisk estimat — resten går tapt til sprut, "
             "fordamping, og den første skyllingen som rengjør taket (first flush).",
    ) / 100
    usage_level = st.selectbox(
        "Forbruksnivå",
        ["survival_total", "normal_usage"],
        format_func=lambda x: {
            "survival_total": f"Beredskap ({WATER_NEEDS['survival_total']} L/person/dag)",
            "normal_usage": f"Normal ({WATER_NEEDS['normal_usage']} L/person/dag)",
        }[x],
        help="**Beredskap** = WHO sitt minimumsforbruk for overlevelse (drikkevann, matlaging, hygiene). "
             "**Normal** = gjennomsnittlig norsk forbruk inkludert dusj, klesvask, oppvask osv.",
    )

buildings = [
    Building(f"Bygg {i+1}", roof_area_m2=roof_area)
    for i in range(num_buildings)
]

# --- Emergency assessment ---
summary = emergency_summary(df, buildings, tank_liters, population, efficiency)

st.subheader("Beredskapsvurdering")
st.markdown(
    "Disse nøkkeltallene oppsummerer hvor godt forberedt scenarioet ditt er. "
    "Simuleringen kjører gjennom det siste året med ekte nedbørsdata dag for dag: "
    "regn fyller tanken, forbruk tømmer den."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Årlig oppsamling",
    f"{summary['total_collected_m3']:,.1f} m³",
    help="Totalt antall kubikkmeter (1 m³ = 1 000 liter) regnvann samlet opp fra alle takene i løpet av året.",
)
c2.metric(
    "Beredskapsforsyning",
    f"{summary['days_of_survival_supply']:,.0f} dager",
    help="Hvis alt vannet som samles i løpet av året ble lagret: "
         f"antall dager det dekker for {population} personer på valgt forbruksnivå.",
)
c3.metric(
    "Dager tank tom",
    f"{summary['days_tank_empty']}",
    help="Antall dager i simuleringen der tanken gikk helt tom. "
         "Flere dager = høyere risiko. 0 dager = tanken holdt hele året.",
)
c4.metric(
    "Lengste tørkeperiode",
    f"{summary['longest_dry_spell_days']} dager",
    help="Den lengste sammenhengende perioden med under 1 mm nedbør per dag. "
         "Lange tørkeperioder er den største utfordringen for regnvannsbasert beredskap.",
)

# Risk assessment
if summary["days_tank_empty"] == 0:
    st.success("Tanken gikk aldri tom det siste året — god beredskap for dette scenarioet!")
elif summary["days_tank_empty"] < 14:
    st.warning(
        f"Tanken var tom {summary['days_tank_empty']} dager i løpet av året. "
        "Prøv å øke tankkapasiteten, legge til flere bygg, eller redusere befolkningen for å se hva som hjelper."
    )
else:
    st.error(
        f"Tanken var tom {summary['days_tank_empty']} dager — dette er utilstrekkelig. "
        "Juster parameterne: større tank, flere tak, eller færre personer."
    )

st.markdown("---")

# --- Tank level simulation chart ---
st.subheader("Tanknivå gjennom året")
st.markdown(
    "Grafen viser hvor full vanntanken er gjennom hele året. "
    "Når det regner fylles tanken opp (kurven stiger), og daglig forbruk tømmer den (kurven synker). "
    "Den røde stiplede linjen markerer et **kritisk nivå på 20 %** — "
    "under dette nivået bør man vurdere å rasjonere vann."
)

sim = storage_simulation(df, buildings, tank_liters, population, usage_level, efficiency)

tank_chart = alt.Chart(sim).mark_area(
    opacity=0.6,
    interpolate="monotone",
    color="#2E86AB",
).encode(
    x=alt.X("date:T", title="Dato"),
    y=alt.Y("tank_pct:Q", title="Tanknivå (%)", scale=alt.Scale(domain=[0, 100])),
    tooltip=[
        alt.Tooltip("date:T", title="Dato"),
        alt.Tooltip("tank_level_liters:Q", title="Liter i tank", format=",.0f"),
        alt.Tooltip("tank_pct:Q", title="Tanknivå (%)", format=".1f"),
        alt.Tooltip("days_remaining:Q", title="Dager igjen", format=".1f"),
    ],
)

threshold = alt.Chart(sim).mark_rule(color="red", strokeDash=[4, 4]).encode(
    y=alt.datum(20),
)

st.altair_chart(tank_chart + threshold, use_container_width=True)
st.caption("Hold musepekeren over grafen for å se eksakte verdier for hver dag.")

# --- Days remaining chart ---
st.subheader("Dager med vannforsyning igjen")
st.markdown(
    "Denne grafen viser hvor mange dager vannet i tanken rekker til enhver tid, "
    "basert på daglig forbruk. Når linjen er høy har man god margin. "
    "Når den nærmer seg null er situasjonen kritisk."
)

days_chart = alt.Chart(sim).mark_line(
    interpolate="monotone",
    color="#E85D04",
).encode(
    x=alt.X("date:T", title="Dato"),
    y=alt.Y("days_remaining:Q", title="Dager igjen"),
    tooltip=[
        alt.Tooltip("date:T", title="Dato"),
        alt.Tooltip("days_remaining:Q", title="Dager igjen", format=".1f"),
    ],
).properties(height=300)

st.altair_chart(days_chart, use_container_width=True)

# --- Dry spells ---
st.subheader("Tørkeperioder")
st.markdown(
    "Tabellen viser perioder med tre eller flere sammenhengende dager med nesten ingen nedbør (under 1 mm). "
    "Disse periodene er den største risikoen for regnvannsbasert vannforsyning — "
    "tanken fylles ikke opp, men forbruket fortsetter. "
    "Lange tørkeperioder krever større lagringskapasitet."
)

dry_spells = find_dry_spells(df)
if dry_spells.empty:
    st.info("Ingen lengre tørkeperioder funnet det siste året.")
else:
    display_spells = dry_spells.copy()
    display_spells.columns = ["Start", "Slutt", "Dager", "Total nedbør (mm)"]
    display_spells = display_spells.sort_values("Dager", ascending=False)
    st.dataframe(display_spells, use_container_width=True, hide_index=True)

# --- WHO needs breakdown ---
st.subheader("Vannbehov ved krise (WHO-standard)")
st.markdown(
    "Verdens helseorganisasjon (WHO) anbefaler et minimum på "
    f"**{WATER_NEEDS['survival_total']} liter per person per dag** i krisesituasjoner. "
    "Til sammenligning bruker en gjennomsnittlig nordmann ca. 150 liter per dag. "
    "Tabellen under viser hva beredskapsvannet dekker:"
)

needs_data = {
    "Kategori": ["Drikkevann", "Sanitær og hygiene", "Matlaging", "Medisinsk bruk"],
    "Liter/person/dag": [
        WATER_NEEDS["drinking"],
        WATER_NEEDS["sanitation"],
        WATER_NEEDS["cooking"],
        WATER_NEEDS["medical"],
    ],
    "Hva det dekker": [
        "Rent drikkevann for å unngå dehydrering",
        "Håndvask, tannpuss og grunnleggende hygiene",
        "Vann til koking av mat",
        "Sårrengjøring og medisinsk bruk",
    ],
}
st.dataframe(needs_data, use_container_width=True, hide_index=True)
st.caption(
    f"Totalt beredskapsbehov: {WATER_NEEDS['survival_total']} liter/person/dag. "
    "Merk: dette er et absolutt minimum. Mer vann gir bedre hygiene og lavere sykdomsrisiko."
)
