import streamlit as st
import pandas as pd
import altair as alt
from urllib.parse import urlparse

# 1. PAGE CONFIG & SEO
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Open Graph Meta Workaround
st.markdown("""
    <head>
    <meta property="og:title" content="U.S. Democracy Gone Bananas" />
    <meta property="og:description" content="A strategic diagnostic of systemic democratic erosion in the U.S. since Jan 2025." />
    </head>
    """, unsafe_allow_html=True)

# 2. CATEGORY MAPPING
CATEGORY_MAP = {
    "Violating Democratic Norms, Undermining Rule of Law": "Democratic Norms",
    "Hollowing State / Weakening Federal Institutions": "Federal Institutions",
    "Suppressing Dissent / Weaponising State Against 'Enemies'": "Suppressing Dissent",
    "Controlling Information Including Spreading Misinformation and Propaganda": "Info Control",
    "Control of Science & Health to Align with State Ideology": "Science & Health",
    "Attacking Universities, Schools, Museums, Culture": "Education & Culture",
    "Weakening Civil Rights": "Civil Rights",
    "Corruption & Enrichment": "Corruption",
    "Aggressive Foreign Policy & Global Destabilisation": "Foreign Policy",
    "Anti-immigrant or Militarised Nationalism": "Immigration & Nationalism"
}
SORTED_SHORT_NAMES = sorted(list(CATEGORY_MAP.values()))
SHORT_TO_LONG = {v: k for k, v in CATEGORY_MAP.items()}

# 3. LOAD DATA
@st.cache_data
def load_data():
    files_to_try = ['trump-actions-3-1-26.csv', 'trump-actions.csv']
    df = None
    for file in files_to_try:
        try:
            df = pd.read_csv(file, skiprows=2)
            break
        except:
            continue
    if df is None: return None, None

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=True) 
    cat_cols = list(CATEGORY_MAP.keys())
    
    df['Themes_List'] = df.apply(lambda r: ", ".join([CATEGORY_MAP.get(c, c) for c in cat_cols if str(r[c]).strip().lower() == 'yes']), axis=1)
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df, cat_cols

df, cat_cols = load_data()

# 4. DEEP LINK LOGIC
query_params = st.query_params
default_area = query_params.get("area", "All Actions")

# 5. HEADER & VELOCITY METRIC
st.title("🙊 U.S. Democracy Gone Bananas")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0")

if not df.empty:
    total_actions = len(df)
    days_active = (df['Date'].max() - df['Date'].min()).days
    pace_per_month = (total_actions / max(days_active, 1)) * 30.44
    last_update = df['Date'].max().strftime('%b %d, %Y')
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Actions Logged", f"{total_actions}", f"Updated {last_update}", delta_color="off")
    m2.metric("Current Velocity", f"{pace_per_month:.1f} / mo", delta="⚠️ Critical Pace", delta_color="inverse")
    m3.metric("Strategic Overlap", f"{(len(df[df['Cat_Count'] > 1]) / total_actions * 100):.1f}%", help="Percentage of actions impacting multiple democratic norms simultaneously.")

st.info("**Context:** A strategic diagnostic of systemic democratic erosion in the U.S. since Jan 2025.")

# 6. STICKY WHITE-ON-WHITE NAVIGATION
st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) {
            position: sticky; top: 2.875rem; z-index: 999; background-color: #0e1117; padding: 10px 0;
        }
    </style>
    <div class="nav-container" style="display: flex; justify-content: space-between; gap: 8px; margin-bottom: 25px;">
        <a href="#timeline" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Timeline</button></a>
        <a href="#themes" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Themes</button></a>
        <a href="#latest" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Latest</button></a>
        <a href="#insights" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Insights</button></a>
        <a href="#search" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Search</button></a>
    </div>
""", unsafe_allow_html=True)

# 7. SIDEBAR & URL SYNC
st.sidebar.title("Filters")
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", value=False)
if comparison_mode:
    selected_compare = st.sidebar.multiselect("Categories", SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
    selected_short = "Comparison View"
else:
    if default_area in (["All Actions"] + SORTED_SHORT_NAMES):
        start_index = (["All Actions"] + SORTED_SHORT_NAMES).index(default_area)
    else:
        start_index = 0
    selected_short = st.sidebar.selectbox("Filter Area", ["All Actions"] + SORTED_SHORT_NAMES, index=start_index)
    st.query_params["area"] = selected_short

# 8. DATA BRANCHING
if comparison_mode:
    long_cats = [SHORT_TO_LONG[s] for s in selected_compare]
    df_comp = df.melt(id_vars=['Date', 'Index', 'Title', 'Themes_List', 'URL', 'Cat_Count'], value_vars=long_cats, var_name='Category_Long', value_name='Is_Active')
    df_comp = df_comp[df_comp['Is_Active'].fillna('No').astype(str).str.strip().str.lower() == 'yes']
    df_comp['Category_Short'] = df_comp['Category_Long'].map(CATEGORY_MAP)
    df_comp = df_comp.sort_values(['Category_Short', 'Date'])
    df_comp['Cumulative'] = df_comp.groupby('Category_Short').cumcount() + 1
    display_df = df_comp
