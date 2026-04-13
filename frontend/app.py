import streamlit as st


st.set_page_config(page_title="Bergen Smart Rain Hub", page_icon="🌧️", layout="wide")
st.title("Bergen Smart Rain Hub",)

c = st.container()
c.markdown(
    "**Bergen Smart Rain Hub** er et prosjekt som samler inn og analyserer data fra regnsensorer i Bergen. " \
    "Vi benytter data fra **[Meterologisk Institutt](https://www.met.no/)** og privatsensorer for å gi innsikt i nedbørsmønstre og lokale avvik. " \
    "Vi analyserer også hvordan regn kan påvirke energiforbruket i urbane områder og hvordan det kan utnyttes "
    "for å redusere energiforbruket og vannforbruket i næringsbygg og boliger."
)

col1, col2, col3 = st.columns(3)
col1.metric("Nedbør i dag", "15 mm")
col2.metric("Energipotensial", "1500 Wh")
col3.metric("Vann samlet opp", "1500 L")

