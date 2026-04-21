import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from backend.config import DB_PATH, default_date_range
from backend.database import init_db, get_observations
from backend.analysis import (
    Building, emergency_summary, WATER_NEEDS, BUILDING_PRESETS,
)
from backend.risk import (
    RISKS, CCPS, CATEGORY_LABELS, OVERALL_SEVERITY_ORDER,
    assess_scenario_risks,
)

st.set_page_config(page_title="Risikovurdering", page_icon="⚠️")
st.title("Risikovurdering")
st.markdown(
    "Regnvannsoppsamling for beredskap innebærer risiko som må vurderes og håndteres. "
    "Denne siden viser en systematisk risikovurdering basert på norske og internasjonale standarder, "
    "tilpasset ditt scenario."
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

# --- Scenario parameters ---
st.subheader("Ditt scenario")
st.markdown(
    "Juster parameterne under for å se hvilke risikoer som er mest relevante for ditt oppsett."
)

col1, col2, col3 = st.columns(3)
with col1:
    preset_keys = list(BUILDING_PRESETS.keys())
    preset_labels = [BUILDING_PRESETS[k]["label"] for k in preset_keys]
    selected_label = st.selectbox("Bygningstype", preset_labels)
    selected_key = preset_keys[preset_labels.index(selected_label)]
    preset = BUILDING_PRESETS[selected_key]
    roof_area = preset["roof_area_m2"]
with col2:
    population = st.slider("Befolkning", 1, 500, preset["default_people"])
with col3:
    tank_liters = st.slider("Tankkapasitet (liter)", 500, 100_000, 5000, step=500)

# Run simulation to get context
building = Building(preset["label"], roof_area_m2=roof_area, height_m=preset["height_m"])
summary = emergency_summary(df, [building], tank_liters, population)

# --- Contextual risk assessment ---
st.markdown("---")
st.subheader("Risikoer for ditt scenario")
st.markdown(
    "Risikoene under er rangert etter relevans for ditt valgte scenario. "
    "Risikoer med høyere poengsum er mer relevante for ditt oppsett."
)

assessed = assess_scenario_risks(
    tank_liters=tank_liters,
    population=population,
    roof_area_m2=roof_area,
    days_tank_empty=summary["days_tank_empty"],
    longest_dry_spell=summary["longest_dry_spell_days"],
)

SEVERITY_COLORS = {
    "Kritisk": "#C1292E",
    "Høy": "#E8963E",
    "Middels": "#2E86AB",
}

for risk, score, reason in assessed:
    color = SEVERITY_COLORS.get(risk.overall, "#666")
    badge_html = (
        f'<span style="background-color: {color}; color: white; '
        f'padding: 2px 8px; border-radius: 4px; font-size: 0.85rem;">'
        f'{risk.overall}</span>'
    )

    with st.expander(f"{risk.name}  —  {risk.overall}"):
        st.markdown(
            f"**Alvorlighetsgrad:** {badge_html}&emsp;"
            f"**Sannsynlighet:** {risk.likelihood}&emsp;"
            f"**Konsekvens:** {risk.impact}&emsp;"
            f"**Kategori:** {CATEGORY_LABELS.get(risk.category, risk.category)}",
            unsafe_allow_html=True,
        )
        if reason:
            st.info(f"Relevant for ditt scenario: {reason}")
        st.markdown(f"**Tiltak:** {risk.mitigation}")


# --- Full risk matrix ---
st.markdown("---")
st.subheader("Komplett risikomatrise")
st.markdown(
    "Tabellen under viser alle identifiserte risikoer med sannsynlighet, "
    "konsekvens og samlet vurdering. Basert på rammeverket i "
    "*Emergency Rainwater Supply Potential in Bergen* (se dokumentasjon)."
)

matrix_data = {
    "Risiko": [r.name for r in RISKS],
    "Kategori": [CATEGORY_LABELS.get(r.category, r.category) for r in RISKS],
    "Sannsynlighet": [r.likelihood for r in RISKS],
    "Konsekvens": [r.impact for r in RISKS],
    "Samlet": [r.overall for r in RISKS],
    "Tiltak": [r.mitigation for r in RISKS],
}

st.dataframe(matrix_data, use_container_width=True, hide_index=True)


# --- HACCP Critical Control Points ---
st.markdown("---")
st.subheader("Kritiske kontrollpunkter (HACCP)")
st.markdown(
    "For systemer beregnet på offentlig bruk kreves en formell HACCP-tilnærming "
    "(Hazard Analysis and Critical Control Points), i henhold til norsk *Vannforskrift*. "
    "De seks kontrollpunktene under dekker hele kjeden fra tak til tappepunkt."
)

for ccp in CCPS:
    with st.expander(f"{ccp.id}: {ccp.name}"):
        st.markdown(f"**Beskrivelse:** {ccp.description}")
        st.markdown(f"**Kontrollmål:** {ccp.control_measure}")


# --- Bergen-specific risks ---
st.markdown("---")
st.subheader("Bergen-spesifikke risikoer")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("##### Eldre bygningsstock")
    st.markdown(
        "Bergen har en betydelig andel pre-1970 trehus med:\n"
        "- Blybeslag og blylodde renner\n"
        "- Gamle malte overflater med blybasert maling\n"
        "- Asbestsement-taktekning (liten, men reell andel)\n\n"
        "En bygningsvis kartlegging anbefales før implementering av nabolags- "
        "eller større systemer."
    )

with col_b:
    st.markdown("##### Kyst- og bymiljø")
    st.markdown(
        "Nærhet til sjøen introduserer:\n"
        "- **Marin aerosol** — saltavsetning på tak; påvirker smak\n"
        "- **Måseforurensning** — Campylobacter- og Salmonella-risiko\n"
        "- **Havn og industri** — Laksevåg, Dokken og Nøstet har historisk "
        "industriell virksomhet; tungmetaller og hydrokarboner i luftnedfall"
    )


# --- Footer ---
st.markdown("---")
st.caption(
    "Risikovurderingen er basert på rammeverket i "
    "\"Emergency Rainwater Supply Potential in Bergen\" (seksjon 8). "
    "HACCP-tilnærmingen følger kravene i Vannforskriften."
)
