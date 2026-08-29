import streamlit as st
#default page config
st.set_page_config(
    layout="wide",
    page_title="Evogen primer search",
    page_icon="♿"
)
#main browser look
st.title("Evogen primer search")
st.write("Write down coordinates as in example: ChrX:12345-12346")
st.markdown("zip zap")
col1, col2, col3 = st.columns([1.5, 4, 1])
with col1:
    category = st.selectbox(
        "Grch38/Grch37",
        options=["Grch38", "Grch37"],
        label_visibility="collapsed",
        key="category_main"
    )
with col2:
    coordinates = st.text_input(
        "Coordinates",
        placeholder="ChrX:12345-12346",
        label_visibility="collapsed",
        key="coordinates_main"
    )
with col3:
    if st.button("🔍", use_container_width=True, key="search_btn"):
        st.session_state.search_triggered = True