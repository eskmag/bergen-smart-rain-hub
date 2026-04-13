import streamlit as st

st.set_page_config(page_title="Energibesparing")

st.title("Energibesparing")
st.write("Innhold for energibesparing kommer her")

# Placeholder for diagram eller data
col1, col2 = st.columns(2)
with col1:
    st.metric("Energispart", "45%")
with col2:
    st.metric("CO₂ Reduksjon", "12 tonn")
