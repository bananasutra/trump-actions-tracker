import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# 1. PAGE CONFIG & SEO
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# [SEO Block and Themes/Glossary remain unchanged]

# 3. LOAD DATA
@st.cache_data
def load_data():
    files_to_try = ['trump-actions-3-1-26.csv', 'trump-actions.csv']
    df = None
    for file in files_to_try:
        try:
            df = pd.read_csv(file, skiprows=2)
            break
        except: continue
    if df is None: return None
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=True) 
    cat_cols = list(CATEGORY_MAP.keys())
    df['Themes_List'] = df.apply(lambda r: ", ".join([CATEGORY_MAP.get(c, c) for c in cat_cols if str(r[c]).strip().lower() == 'yes']), axis=1)
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df

df = load_data()

# 4. SIDEBAR (THE "SLICE & DICE" ENGINE)
st.sidebar.title("🎛️ Data Controls")

# A. Global Keyword Search (New UX Priority)
st.sidebar.subheader("🔍 Global Search")
global_search = st.sidebar.text_input("Search any keyword...", placeholder="e.g. Musk, Border, DOJ", help="Filters all charts and tables on the page.")

# B. Category Filter
st.sidebar.divider()
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", value=False)
query_params = st.query_params
default_area = query_params.get("area", "All Actions")

if comparison_mode:
    selected_compare = st.sidebar.multiselect("Categories", SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
    selected_short = "Comparison View"
else:
    options = ["All Actions"] + SORTED_SHORT_NAMES
    start_index = options.index(default_area) if default_area in options else 0
    selected_short = st.sidebar.selectbox("Filter Area", options, index=start_index)
    st.query_params["area"] = selected_short

# C. Date Slider
if df is not None:
    st.sidebar.divider()
    st.sidebar.subheader("📅 Timeline Scrub")
    min_date = df['Date'].min().to_pydatetime()
    max_date = df['Date'].max().to_pydatetime()
    selected_range = st.sidebar.slider("Select Window", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="MMM DD")
    
    # APPLYING ALL FILTERS (Global Search + Date + Category)
    mask = (df['Date'] >= selected_range[0]) & (df['Date'] <= selected_range[1])
    if global_search:
        mask = mask & (df['Title'].str.contains(global_search, case=False, na=False))
    
    filtered_df = df.loc[mask]
else:
    filtered_df = df

# ... [Header, Hero Stats, and Nav remain the same, but they now reflect 'filtered_df' which includes the search keyword] ...

# 11. DEEP INSIGHTS (REFINED VIDEO WIDTH)
st.markdown("<div id='insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: Strategic Diagnostic")

if filtered_df is not None and not filtered_df.empty:
    total_raw = len(filtered_df)
    multi_ratio = (len(filtered_df[filtered_df['Cat_Count'] > 1]) / total_raw * 100)
    
    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown("#### Strategic Velocity & Attrition")
        st.write(f"The administration is maintaining a velocity of **{pace_per_month:.1f} actions per month**. This volume induces 'procedural shock' designed to exhaust the bandwidth of the legal system.")
        st.markdown("#### Norm-Collapse Loops")
        st.write(f"**Interconnectivity:** {multi_ratio:.1f}% of events are 'multi-tagged,' striking multiple institutional checks simultaneously.")

    with col_ins2:
        st.markdown("#### The Resistance Heatmap")
        st.write("Opposition centers in CA, WA, NY, IL. Litigation acts as the primary friction point against this velocity.")
        st.warning(f"**Diagnostic Projection:** By Jan 2029, the tracker projects **8,220 actions**. This signals a move toward a total administrative rewrite.")

    # REFINED VIDEO: The "80% Width" Padding Trick
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>Methodology Context & Expert Analysis</h4>", unsafe_allow_html=True)
    
    # Creating 3 columns with 10% - 80% - 10% width
    v_pad_left, v_main, v_pad_right = st.columns([1, 8, 1])
    with v_main:
        st.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")

# 12. SEARCH DATA VAULT (CLEANER)
st.markdown("<div id='search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Search Data Vault")
if global_search:
    st.write(f"Showing results for: **'{global_search}'** within selected dates.")

# display_df processing here...
st.dataframe(
    display_df[['Date', 'Title', 'URL', 'Themes_List']], 
    column_config={"URL": st.column_config.LinkColumn("Source"), "Themes_List": "Themes"},
    use_container_width=True, hide_index=True
)

st.caption("Dashboard by Celine Nadeau aka bananasutra. Last updated 03-02-2026. CC BY 4.0.")
