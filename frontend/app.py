import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import altair as alt
from backend.database import init_db, get_observations
from backend.analysis import (
    water_collected, emergency_supply_days,
    storage_simulation, recommend_tank_size,
    find_dry_spells, Building, BUILDING_PRESETS, WATER_NEEDS,
)

st.set_page_config(page_title="Bergen Smart Rain Hub", page_icon="🌧️", layout="wide")
st.title("Bergen Smart Rain Hub")
st.markdown(
    "Finn ut hvor mye regnvann **ditt bygg** kan samle opp, "
    "og hvor lenge det rekker i en krisesituasjon."
)

# Load data
conn = init_db()
df = get_observations(conn, "2025-04-13", "2026-04-12")
conn.close()

if df.empty:
    st.warning("Ingen data funnet. Kjør `python -m backend.pipeline` for å hente data.")
    st.stop()

# ============================================================
# Step 1: Building selector
# ============================================================
st.subheader("1. Velg bygningstype")

preset_keys = list(BUILDING_PRESETS.keys())
preset_labels = [BUILDING_PRESETS[k]["label"] for k in preset_keys]

selected_label = st.radio(
    "Hva slags bygg har du?",
    preset_labels,
    horizontal=True,
    label_visibility="collapsed",
)

selected_key = preset_keys[preset_labels.index(selected_label)]
preset = BUILDING_PRESETS[selected_key]

st.caption(preset["description"])

# ============================================================
# Step 2: People
# ============================================================
st.subheader("2. Hvor mange personer?")

people = st.slider(
    "Antall personer som skal forsynes med vann",
    min_value=1,
    max_value=1000,
    value=preset["default_people"],
    help="Velg antall personer bygget skal forsyne. "
         "For en husholdning er dette familien din. "
         "For en skole eller arbeidsplass er det elever/ansatte som oppholder seg der daglig.",
)

# ============================================================
# Hero answer
# ============================================================
total_rain = df["precipitation_mm"].sum()
roof_area = preset["roof_area_m2"]
annual_liters = water_collected(total_rain, roof_area)
supply_days = emergency_supply_days(annual_liters, people, "survival_total")

st.markdown("---")

# Big result
if supply_days >= 365:
    color = "#1B813E"
    verdict = "Svært god beredskap"
elif supply_days >= 90:
    color = "#2E86AB"
    verdict = "God beredskap"
elif supply_days >= 30:
    color = "#E8963E"
    verdict = "Moderat beredskap"
else:
    color = "#C1292E"
    verdict = "Lav beredskap"

st.markdown(
    f"""
    <div style="background-color: {color}15; border-left: 5px solid {color};
                padding: 1.5rem; border-radius: 0.5rem; margin: 1rem 0;">
        <h2 style="margin: 0; color: {color};">{verdict}</h2>
        <p style="font-size: 1.4rem; margin: 0.5rem 0 0 0;">
            Ditt <strong>{preset['label'].lower()}</strong> kan samle opp
            <strong>{annual_liters:,.0f} liter</strong> regnvann i året — nok til å forsyne
            <strong>{people} {'person' if people == 1 else 'personer'}</strong> i
            <strong>{supply_days:,.0f} dager</strong> ved en vannkrise.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Supporting metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Årlig oppsamling",
    f"{annual_liters:,.0f} L",
    help=f"Total vannoppsamling fra et {roof_area} m² tak med 85 % effektivitet, basert på {total_rain:,.0f} mm nedbør det siste året.",
)
c2.metric(
    "Per dag (snitt)",
    f"{annual_liters / 365:,.0f} L",
    help="Gjennomsnittlig daglig oppsamling gjennom året.",
)
c3.metric(
    "Daglig behov",
    f"{WATER_NEEDS['survival_total'] * people:,.0f} L",
    help=f"{WATER_NEEDS['survival_total']} liter per person per dag (WHO beredskapsstandard) × {people} personer.",
)
c4.metric(
    "Beredskap",
    f"{supply_days:,.0f} dager",
    help="Antall dager hele årets oppsamling kan dekke vannbehovet.",
)

# ============================================================
# Tank recommendation
# ============================================================
st.markdown("---")
st.subheader("3. Anbefalt tankstørrelse")
st.markdown(
    "For å faktisk kunne lagre regnvann trenger du en tank. "
    "Størrelsen avhenger av hvor mange dager uten regn du vil være forberedt på. "
    "Bergen kan ha tørkeperioder på opptil 3–4 uker."
)

tank_options = recommend_tank_size(annual_liters, people)

tank_cols = st.columns(3)
for i, opt in enumerate(tank_options):
    with tank_cols[i]:
        if opt["label"] == "Anbefalt":
            st.markdown(f"**{opt['label']}**")
        else:
            st.markdown(opt["label"])
        st.metric(
            "Tankkapasitet",
            f"{opt['liters']:,.0f} L",
            help=opt["description"],
        )
        st.caption(f"{opt['description']}")
        st.caption(f"= {opt['liters']/1000:,.1f} m³")

# ============================================================
# Simulation with recommended tank
# ============================================================
recommended_tank = tank_options[1]["liters"]  # "Anbefalt"
building = Building(preset["label"], roof_area_m2=roof_area, height_m=preset["height_m"])

sim = storage_simulation(df, [building], recommended_tank, people, "survival_total")

st.markdown("---")
st.subheader("4. Simulering gjennom året")
st.markdown(
    f"Grafen under viser hvordan tanknivået ville sett ut det siste året med "
    f"den anbefalte tanken ({recommended_tank:,.0f} L). "
    f"Regn fyller tanken, daglig forbruk tømmer den. "
    f"Den røde linjen markerer kritisk nivå (20 %)."
)

tank_chart = alt.Chart(sim).mark_area(
    opacity=0.6, interpolate="monotone", color="#2E86AB",
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

days_empty = int((sim["tank_level_liters"] == 0).sum())
if days_empty == 0:
    st.success("Med den anbefalte tanken gikk vannet aldri tomt det siste året.")
elif days_empty < 14:
    st.warning(
        f"Tanken var tom {days_empty} dager i løpet av året. "
        "Vurder en større tank eller å koble til flere tak."
    )
else:
    st.error(
        f"Tanken var tom {days_empty} dager. "
        "Du bør vurdere en betydelig større tank for denne befolkningen."
    )

# ============================================================
# Dry spells
# ============================================================
st.markdown("---")
st.subheader("5. Sårbare perioder")
st.markdown(
    "Tabellen viser perioder det siste året med tre eller flere dager nesten uten regn. "
    "Disse periodene er den største utfordringen for regnvannsbasert beredskap — "
    "tanken fylles ikke opp, men forbruket fortsetter."
)

dry_spells = find_dry_spells(df)
if dry_spells.empty:
    st.info("Ingen lengre tørkeperioder funnet det siste året.")
else:
    display = dry_spells.copy()
    display.columns = ["Start", "Slutt", "Antall dager", "Total nedbør (mm)"]
    display = display.sort_values("Antall dager", ascending=False).head(10)
    st.dataframe(display, use_container_width=True, hide_index=True)

# ============================================================
# Advanced: customize parameters
# ============================================================
with st.expander("Tilpass parametere (avansert)"):
    st.markdown(
        "Standardverdiene er basert på typiske norske bygg. "
        "Hvis du kjenner de nøyaktige tallene for ditt bygg kan du justere dem her."
    )
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        custom_roof = st.number_input(
            "Takareal (m²)", value=roof_area, min_value=10, max_value=10000,
            help="Det faktiske takarealet på bygget ditt.",
        )
    with col_b:
        custom_efficiency = st.slider(
            "Oppsamlingseffektivitet (%)", 50, 95, 85,
            help="85 % er realistisk for de fleste tak. Flate tak med membran kan gi opptil 90 %. "
                 "Tak med mye mose eller dårlige renner kan gi ned mot 60 %.",
        ) / 100
    with col_c:
        custom_tank = st.number_input(
            "Tankkapasitet (liter)", value=recommended_tank, min_value=100, max_value=500000, step=500,
            help="Størrelsen på vanntanken din.",
        )

    if custom_roof != roof_area or custom_efficiency != 0.85 or custom_tank != recommended_tank:
        custom_liters = water_collected(total_rain, custom_roof, custom_efficiency)
        custom_days = emergency_supply_days(custom_liters, people, "survival_total")

        st.markdown(f"""
        **Med dine tilpassede verdier:**
        - Årlig oppsamling: **{custom_liters:,.0f} liter**
        - Beredskapsforsyning: **{custom_days:,.0f} dager** for {people} personer
        """)

        custom_building = Building("Tilpasset", roof_area_m2=custom_roof, height_m=preset["height_m"])
        custom_sim = storage_simulation(df, [custom_building], custom_tank, people, "survival_total", custom_efficiency)
        custom_empty = int((custom_sim["tank_level_liters"] == 0).sum())

        if custom_empty == 0:
            st.success("Med disse parameterne gikk tanken aldri tom.")
        else:
            st.warning(f"Tanken var tom {custom_empty} dager med disse parameterne.")

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.caption(
    "Data fra Meteorologisk Institutt (Frost API), målestasjon Bergen Florida (SN50540). "
    f"Beredskapsberegninger basert på WHO-standard: {WATER_NEEDS['survival_total']} liter/person/dag "
    f"(drikkevann {WATER_NEEDS['drinking']} L, matlaging {WATER_NEEDS['cooking']} L, "
    f"hygiene {WATER_NEEDS['sanitation']} L, medisinsk {WATER_NEEDS['medical']} L)."
)
