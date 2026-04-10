import json
import pandas as pd
import streamlit as st

DATA_FILE = "laws_data.json"

st.set_page_config(
    page_title="Pustinyakovo Laws Database",
    page_icon="⚖️",
    layout="wide"
)

@st.cache_data
def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        laws = json.load(f)
    return laws

laws = load_data()

if "selected_law_id" not in st.session_state:
    st.session_state.selected_law_id = None
if "filters_applied" not in st.session_state:
    st.session_state.filters_applied = False
if "search_text" not in st.session_state:
    st.session_state.search_text = ""
if "selected_sectors" not in st.session_state:
    st.session_state.selected_sectors = []
if "year_range" not in st.session_state:
    st.session_state.year_range = None
if "law_id_search" not in st.session_state:
    st.session_state.law_id_search = ""
if "active_only" not in st.session_state:
    st.session_state.active_only = False

df = pd.DataFrame([
    {
        "sector": law.get("sector", ""),
        "title": law.get("title", ""),
        "year": law.get("year", None),
        "law_id": law.get("law_id", ""),
        "subject": law.get("subject", ""),
        "full_text": law.get("full_text", ""),
        "is_relevant": law.get("is_relevant", True)
    }
    for law in laws
])

st.title("⚖️ Закони на Република Пустиняково ")
st.markdown("Интерактивна база данни за търсене, филтриране и преглед на законите.")

st.sidebar.header("Филтри")

sectors = sorted([s for s in df["sector"].dropna().unique() if s])
years = sorted([int(y) for y in df["year"].dropna().unique()])

if years and st.session_state.year_range is None:
    st.session_state.year_range = (min(years), max(years))
elif st.session_state.year_range is None:
    st.session_state.year_range = (1900, 2100)

with st.sidebar.form("filters_form"):
    search_text = st.text_input("Търсене по ключова дума", value=st.session_state.search_text)

    selected_sectors = st.multiselect(
        "Сектор",
        options=sectors,
        default=st.session_state.selected_sectors
    )

    if years:
        year_range = st.slider(
            "Година на приемане",
            min_value=min(years),
            max_value=max(years),
            value=st.session_state.year_range
        )
    else:
        year_range = (1900, 2100)

    law_id_search = st.text_input(
        "Търсене по идентификационен номер",
        value=st.session_state.law_id_search
    )
    active_only = st.checkbox(
        "Само активни закони",
        value=st.session_state.active_only
    )
    apply_filters = st.form_submit_button("Търси")

if apply_filters:
    st.session_state.search_text = search_text
    st.session_state.selected_sectors = selected_sectors
    st.session_state.year_range = year_range
    st.session_state.law_id_search = law_id_search
    st.session_state.active_only = active_only
    st.session_state.filters_applied = True

search_text = st.session_state.search_text
selected_sectors = st.session_state.selected_sectors
year_range = st.session_state.year_range
law_id_search = st.session_state.law_id_search
active_only = st.session_state.active_only

filtered_df = df.copy()

if st.session_state.filters_applied:
    if search_text:
        search_lower = search_text.lower()
        filtered_df = filtered_df[
            filtered_df["title"].str.lower().str.contains(search_lower, na=False) |
            filtered_df["subject"].str.lower().str.contains(search_lower, na=False) |
            filtered_df["full_text"].str.lower().str.contains(search_lower, na=False)
        ]

    if selected_sectors:
        filtered_df = filtered_df[filtered_df["sector"].isin(selected_sectors)]

    filtered_df = filtered_df[
        filtered_df["year"].fillna(0).between(year_range[0], year_range[1])
    ]

    if law_id_search:
        law_id_lower = law_id_search.lower()
        filtered_df = filtered_df[
            filtered_df["law_id"].str.lower().str.contains(law_id_lower, na=False)
        ]

    if active_only:
        filtered_df = filtered_df[filtered_df["is_relevant"] == True]

st.subheader("Общ преглед")
col1, col2, col3 = st.columns(3)
col1.metric("Общ брой закони", len(df))
col2.metric("Показани резултати", len(filtered_df) if st.session_state.filters_applied else len(df))
col3.metric("Брой сектори", len(sectors))

st.subheader("Резултати")

results_df = filtered_df if st.session_state.filters_applied else df
results_df = results_df.sort_values(by=["year", "law_id", "title"], ascending=[True, True, True])

if results_df.empty:
    st.warning("Няма намерени резултати по зададените критерии.")
else:
    header_cols = st.columns([2, 1, 5, 2])
    header_cols[0].markdown("**ID**")
    header_cols[1].markdown("**Година**")
    header_cols[2].markdown("**Заглавие**")
    header_cols[3].markdown("**Преглед**")

    st.markdown("---")

    for _, row in results_df.iterrows():
        row_cols = st.columns([2, 1, 5, 2])

        row_cols[0].write(row["law_id"])
        row_cols[1].write(int(row["year"]) if pd.notna(row["year"]) else "")

        title_text = row["title"]
        if row["is_relevant"]:
            title_text += " ✅"
        else:
            title_text += " ❌"

        row_cols[2].write(title_text)

        if row_cols[3].button("Отвори", key=f'open_{row["law_id"]}'):
            st.session_state.selected_law_id = row["law_id"]

        if st.session_state.selected_law_id == row["law_id"]:
            matching_law = next(
                (law for law in laws if law.get("law_id") == row["law_id"]),
                None
            )

            if matching_law:
                detail_container = st.container()
                with detail_container:
                    st.markdown(f"### {matching_law.get('title', '')} — {matching_law.get('law_id', '')}")
                    st.markdown(f"**Сектор:** {matching_law.get('sector', '')}")
                    st.markdown(f"**Година:** {matching_law.get('year', '')}")
                    st.markdown(f"**Предмет на закона:** {matching_law.get('subject', '')}")

                    if matching_law.get("is_relevant", True):
                        st.markdown("<span style='color:green; font-weight:bold;'>Активен закон</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color:red; font-weight:bold;'>Законът не е актуален</span>", unsafe_allow_html=True)

                    if matching_law.get("articles"):
                        st.markdown("### Членове")
                        for article in matching_law["articles"]:
                            st.markdown(f'**{article.get("article_number", "")}** {article.get("text", "")}')
                    else:
                        st.info("Няма налични членове за този закон.")

                    if st.button("Затвори", key=f'close_{matching_law.get("law_id", "")}'):
                        st.session_state.selected_law_id = None
                        st.rerun()

                    st.markdown("---")