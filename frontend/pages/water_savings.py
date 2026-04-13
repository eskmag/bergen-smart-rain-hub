import streamlit as st

st.set_page_config(page_title="Vannbesparing")

st.title("Vannbesparing")
st.write("Innhold for vannbesparing kommer her")

# Placeholder for diagram eller data
col1, col2 = st.columns(2)
with col1:
    st.metric("Vannspart", "60%")
with col2:
    st.metric("Liter spart", "125,000 L")
