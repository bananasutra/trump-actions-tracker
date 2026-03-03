import streamlit as st
import pandas as pd
import altair as alt
import re
from collections import Counter
from datetime import datetime
from streamlit_echarts import st_echarts

# 1. PAGE CONFIG
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. THEMES & GLOSSARY
THEME_GLOSSARY = [
    {"Theme": "Civil Rights", "Mapping": "Weakening Civil Rights", "Definition": "Dismantling Social Protections & Rights: Removing civil rights from marginalized groups like LGBTQ+ communities and immigrants."},
    {"Theme": "Corruption", "Mapping": "Corruption & Enrichment", "Definition": "Corruption and Enrichment: Actions that directly enrich the president, his family, or his cabinet."},
    {"Theme": "Democratic Norms", "Mapping": "Violating Democratic Norms, Undermining Rule of Law", "Definition": "Violating democratic norms, undermining rule of law: Actions that weaken checks and balances or restrict press freedom."},
    {"Theme": "Education & Culture", "Mapping": "Attacking Universities, Schools, Museums, Culture", "Definition": "Attacking universities, schools, museums, culture: Restricting K-12 education topics and targeting cultural institutions."},
    {"Theme": "Federal Institutions", "Mapping": "Hollowing State / Weakening Federal Institutions", "Definition": "Hollowing state: Dismantling federal institutions, mass firings, or politicizing government roles."},
    {"Theme": "Foreign Policy", "Mapping": "Aggressive Foreign Policy & Global Destabilisation", "Definition": "Aggressive Foreign Policy: Threatening allies and aligning with anti-democratic rivals."},
    {"Theme": "Immigration & Nationalism", "Mapping": "Anti-immigrant or Militarised Nationalism", "Definition": "Anti-immigrant/Nationalism: Using language that demonizes immigrants and expanding domestic surveillance."},
    {"Theme": "Info Control", "Mapping": "Controlling Information Including Spreading Misinformation and Propaganda", "Definition": "Controlling information: Manufacturing evidence to support state policy."},
    {"Theme": "Science & Health", "Mapping": "Control of Science & Health to Align with State Ideology", "Definition": "Control of science: Restricting research on climate change and attacking public health."},
    {"Theme": "Suppressing Dissent", "Mapping": "Suppressing Dissent / Weaponising State Against 'Enemies'", "Definition": "Suppressing dissent: Weaponizing executive power against rivals and critics."}
]

GLOSSARY_DF = pd.DataFrame(THEME_GLOSSARY).sort_values("Theme")
CATEGORY_MAP = dict(zip(GLOSSARY_DF['Mapping'], GLOSSARY_DF['Theme']))
SHORT_TO_LONG = dict(zip(GLOSSARY_DF['Theme'], GLOSSARY_DF['Mapping']))
SORTED_SHORT_NAMES = GLOSSARY_DF['Theme'].tolist()

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

# 4. WELCOME DIALOG
@st.dialog("Strategic Note on Facts")
def show_welcome():
    st.markdown("""
    **Opinions shall not trump the data.**
    In an era where the "certainty of fanatics” is all the rage (like Bertrand Russell almost said), this tracker is built for those who prioritize **verifiable doubt**.
    
    * **Velocity:** the rate at which institutional norms are rewritten.
    * **Complexity:** the ‘strategic’ overlap striking several democratic pillars at once.
    
    ---
    Now, if you’re curious 👀 click anywhere outside this box to begin your investigation.
    """)

if "first_visit" not in st.session_state:
    st.session_state.first_visit = True
    show_welcome()

# 5. SEARCH SYNC
if "search_term" not in st.session_state:
    st.session_state.search_term = ""

def sync_sidebar():
    st.session_state.search_term = st.session_state.sidebar_search

def sync_vault():
    st.session_state.search_term = st.session_state.vault_search

# 6. SIDEBAR
st.sidebar.title("🎛️ Data Controls")
st.sidebar.text_input("🔍 Global Search", key="sidebar_search", on_change=sync_sidebar, value=st.session_state.search_term)
st.sidebar.divider()
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", key="comparison_mode")
selected_short = st.sidebar.selectbox("Filter Area", ["All Actions"] + SORTED_SHORT_NAMES, key="filter_area")

if df is not None:
    min_date, max_date = df['Date'].min().to_pydatetime(), df['Date'].max().to_pydatetime()
    selected_range = st.sidebar.slider("Timeline Scrub", min_value=min_date, max_value=max_date, value=(min_date, max_date), key="date_range", format="MMM DD")
    
    mask = (df['Date'] >= selected_range[0]) & (df['Date'] <= selected_range[1])
    if st.session_state.search_term:
        mask = mask & (df['Title'].str.contains(st.session_state.search_term, case=False, na=False))
    filtered_df = df.loc[mask]

# 7. BRANDED HEADER
st.markdown("""
    <style>
        .brand-link { text-decoration: none !important; color: inherit !important; display: flex; align-items: center; gap: 20px; margin-bottom: 30px; }
        .brand-link h1 { color: inherit !important; margin: 0; font-weight: 700; font-size: calc(1.5rem + 1.5vw); }
        .brand-logo { font-size: 2.5rem; transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1); }
        .brand-link:hover .brand-logo { transform: scale(1.1); }
    </style>
    <a href="#top" class="brand-link">
        <div class="brand-logo">🍌</div>
        <h1>U.S. Democracy Gone Bananas</h1>
    </a>
""", unsafe_allow_html=True)

# 8. HERO STATS (THEME-PROOF)
if not filtered_df.empty:
    total_actions = len(filtered_df)
    days_active = max((selected_range[1] - selected_range[0]).days, 1)
    pace_per_month = (total_actions / days_active) * 30.44
    overlap = (len(filtered_df[filtered_df['Cat_Count'] > 1]) / total_actions * 100)

    st.markdown(f"""
    <div style="display: flex; justify-content: center; gap: 20px; width: 100%; padding: 20px 0; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 250px; background: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 10px; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">Actions in Window</p>
            <h2 style="margin: 0; font-size: 2.5rem;">{total_actions}</h2>
        </div>
        <div style="flex: 1; min-width: 250px; background: rgba(222, 1, 0, 0.05); border: 1px solid #DE0100; border-radius: 10px; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; color: #DE0100;">Velocity</p>
            <h2 style="margin: 0; font-size: 2.5rem; color: #DE0100;">{pace_per_month:.1f}<span style="font-size: 1rem;">/mo</span></h2>
        </div>
        <div style="flex: 1; min-width: 250px; background: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 10px; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">Strategic Overlap</p>
            <h2 style="margin: 0; font-size: 2.5rem;">{overlap:.1f}%</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 9. STICKY NAV
st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) { position: sticky; top: 2.875rem; z-index: 999; background: transparent; backdrop-filter: blur(8px); padding: 10px 0; }
        [id] { scroll-margin-top: 130px !important; }
        .quote-container { background: rgba(128, 128, 128, 0.05); border-left: 5px solid #DE0100; padding: 25px; border-radius: 5px; margin-bottom: 40px; }
    </style>
    <div class="nav-container" style="display: flex; justify-content: space-between; gap: 8px;">
        <a href="#timeline" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #DE0100; background: transparent; color: inherit; font-weight: bold; cursor: pointer;">Timeline</button></a>
        <a href="#themes" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #DE0100; background: transparent; color: inherit; font-weight: bold; cursor: pointer;">Themes</button></a>
        <a href="#insights" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #DE0100; background: transparent; color: inherit; font-weight: bold; cursor: pointer;">Insights</button></a>
        <a href="#words" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #DE0100; background: transparent; color: inherit; font-weight: bold; cursor: pointer;">Words</button></a>
        <a href="#search" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #DE0100; background: transparent; color: inherit; font-weight: bold; cursor: pointer;">Search</button></a>
    </div>
""", unsafe_allow_html=True)

# 10. TIMELINE
st.markdown("<div id='timeline'></div>", unsafe_allow_html=True)
if not filtered_df.empty:
    chart_df = filtered_df.copy().sort_values('Date')
    chart_df['Cumulative'] = range(1, len(chart_df) + 1)
    
    line = alt.Chart(chart_df).mark_line(interpolate='step-after', color='#DE0100', strokeWidth=3).encode(
        x=alt.X('Date:T', title='Timeline'),
        y=alt.Y('Cumulative:Q', title='Total Actions'),
        tooltip=['Date', 'Title', 'Themes_List']
    ).properties(height=400).interactive()
    st.altair_chart(line, use_container_width=True)

# 11. THEMES (THEMATIC DONUT)

st.markdown("<div id='themes'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🌹 Thematic Distribution (Donut)")
if not filtered_df.empty:
    donut_data = []
    for long, short in CATEGORY_MAP.items():
        count = (filtered_df[long].str.strip().str.lower() == 'yes').sum()
        if count > 0: donut_data.append({"value": int(count), "name": short})

    donut_options = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {"orient": "horizontal", "bottom": "0", "textStyle": {"color": "inherit"}},
        "series": [{
            "type": "pie", "radius": ["40%", "70%"], "avoidLabelOverlap": False,
            "itemStyle": {"borderRadius": 10, "borderColor": "transparent", "borderWidth": 2},
            "label": {"show": False}, "data": donut_data
        }]
    }
    st_echarts(donut_options, height="450px")

# 12. INSIGHTS (RESTORED FULL CONTENT)
st.markdown("<div id='insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: Strategic Diagnostic")
if not filtered_df.empty:
    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown("#### Strategic Velocity & Attrition")
        st.write(f"The administration is maintaining a velocity of **{pace_per_month:.1f} actions per month**. This volume induces 'procedural shock' designed to exhaust the bandwidth of judicial and civil oversight.")
        st.markdown("#### Norm-Collapse Loops")
        st.write(f"**Interconnectivity:** {overlap:.1f}% of events strike several democratic pillars at once, ensuring that legal resistance in one domain does not stall progress in another.")
    with col_ins2:
        st.markdown("#### The Resistance Heatmap")
        st.write("Opposition is currently concentrated in state-level hubs (CA, WA, NY, IL). Litigation remains the primary friction point against this administrative velocity.")
        st.warning(f"**Diagnostic Projection:** By Jan 2029, the tracker projects **8,220 actions**.")

    st.markdown(f"""<div class="quote-container"><p style="font-style: italic; margin-bottom: 5px;">"fools and fanatics are always so certain of themselves, and wiser people so full of doubts."</p><p style="text-align: right; font-weight: bold; margin: 0;">— Bertrand Russell</p></div>""", unsafe_allow_html=True)
    v_left, v_mid, v_right = st.columns([1, 8, 1])
    with v_mid: st.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")

# 13. WORD CLOUD
st.markdown("<div id='words'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("☁️ Thematic Word Cloud")
if not filtered_df.empty:
    stop_words = {'the', 'and', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'up', 'about', 'into', 'over', 'after', 'trump', 'administration', 'order', 'federal', 'u.s.', 'president', 'will', 'this', 'that'}
    all_titles = " ".join(filtered_df['Title'].values).lower()
    words = re.findall(r'\w+', all_titles)
    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
    word_counts = Counter(filtered_words).most_common(50)
    js_color = "function () { var colors = ['#00f2ff', '#ff00ea', '#00ffaa', '#fffb00', '#ff4d00', '#DE0100', '#55ff00']; return colors[Math.floor(Math.random() * colors.length)]; }"
    wc_options = {"backgroundColor": "transparent", "series": [{"type": "wordCloud", "gridSize": 15, "sizeRange": [16, 70], "rotationRange": [0,0], "textStyle": {"fontWeight": "bold", "color": js_color}, "data": [{"name": word, "value": count} for word, count in word_counts]}]}
    st_echarts(wc_options, height="450px")

# 14. VAULT
st.markdown("<div id='search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Search Data Vault")
st.text_input("Filter results...", key="vault_search", on_change=sync_vault, value=st.session_state.search_term)
if not filtered_df.empty:
    st.dataframe(filtered_df[['Date', 'Title', 'URL', 'Themes_List']].sort_values('Date', ascending=False), column_config={"URL": st.column_config.LinkColumn("Source"), "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")}, use_container_width=True, hide_index=True)
st.caption("Dashboard by Celine Nadeau. Last updated 03-03-2026. CC BY 4.0.")
