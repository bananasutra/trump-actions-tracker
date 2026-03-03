import streamlit as st
import pandas as pd
import altair as alt
import re
from collections import Counter
from datetime import datetime
from streamlit_echarts import st_echarts

# 1. PAGE CONFIG & SEO HACK
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- THE SEO HACK ---
# This injects metadata for social media crawlers
st.markdown(f"""
    <head>
    <title>U.S. Democracy Gone Bananas</title>
    <meta name="description" content="A strategic diagnostic of systemic democratic erosion and institutional dismantling in the U.S. since Jan 2025.">
    <meta property="og:title" content="U.S. Democracy Gone Bananas: Trump Actions Tracker">
    <meta property="og:description" content="Strategic diagnostic of administrative velocity and institutional rewrite in the U.S. (2025-2026).">
    <meta property="og:image" content="https://raw.githubusercontent.com/celinenadeau/repo/main/og-image.png">
    <meta property="og:url" content="https://trump-actions-tracker.streamlit.app/">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="U.S. Democracy Gone Bananas">
    <meta name="twitter:description" content="Diagnostic of systemic democratic erosion since Jan 2025.">
    </head>
    """, unsafe_allow_html=True)

# 2. THEMES & GLOSSARY
THEME_GLOSSARY = [
    {"Theme": "Civil Rights", "Mapping": "Weakening Civil Rights", "Definition": "Dismantling Social Protections & Rights."},
    {"Theme": "Corruption", "Mapping": "Corruption & Enrichment", "Definition": "Actions that directly enrich the president or his inner circle."},
    {"Theme": "Democratic Norms", "Mapping": "Violating Democratic Norms, Undermining Rule of Law", "Definition": "Weakening checks and balances or restricting press freedom."},
    {"Theme": "Education & Culture", "Mapping": "Attacking Universities, Schools, Museums, Culture", "Definition": "Restricting K-12 education and targeting cultural institutions."},
    {"Theme": "Federal Institutions", "Mapping": "Hollowing State / Weakening Federal Institutions", "Definition": "Dismantling federal institutions and politicizing government roles."},
    {"Theme": "Foreign Policy", "Mapping": "Aggressive Foreign Policy & Global Destabilisation", "Definition": "Threatening allies and aligning with anti-democratic rivals."},
    {"Theme": "Immigration & Nationalism", "Mapping": "Anti-immigrant or Militarised Nationalism", "Definition": "Demonizing immigrants and expanding domestic surveillance."},
    {"Theme": "Info Control", "Mapping": "Controlling Information Including Spreading Misinformation and Propaganda", "Definition": "Manufacturing evidence to support state policy."},
    {"Theme": "Science & Health", "Mapping": "Control of Science & Health to Align with State Ideology", "Definition": "Restricting research and attacking public health."},
    {"Theme": "Suppressing Dissent", "Mapping": "Suppressing Dissent / Weaponising State Against 'Enemies'", "Definition": "Weaponizing executive power against rivals and critics."}
]

GLOSSARY_DF = pd.DataFrame(THEME_GLOSSARY).sort_values("Theme")
CATEGORY_MAP = dict(zip(GLOSSARY_DF['Mapping'], GLOSSARY_DF['Theme']))
SHORT_TO_LONG = dict(zip(GLOSSARY_DF['Theme'], GLOSSARY_DF['Mapping']))
SORTED_SHORT_NAMES = GLOSSARY_DF['Theme'].tolist()

# 3. DATA LOADING
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

# 4. SEARCH SYNC & DIALOG
if "search_term" not in st.session_state: st.session_state.search_term = ""
def sync_sidebar(): st.session_state.search_term = st.session_state.sidebar_search
def sync_vault(): st.session_state.search_term = st.session_state.vault_search

@st.dialog("Strategic Note on Facts")
def show_welcome():
    st.markdown("""
    **Opinions shall not trump the data.**
    In an era of certainty, this tracker is built for **verifiable doubt**.
    * **Velocity:** institutional rewrite rate.
    * **Complexity:** interlocking strikes.
    ---
    Now, if you’re curious 👀 click anywhere outside this box to begin your investigation.
    """)

if "first_visit" not in st.session_state:
    st.session_state.first_visit = True
    show_welcome()

# 5. SIDEBAR
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

    def reset_filters():
        st.session_state.search_term = ""
        st.session_state.sidebar_search = ""
        st.session_state.vault_search = ""
        st.session_state.comparison_mode = False
        st.session_state.filter_area = "All Actions"
        st.session_state.date_range = (min_date, max_date)
    st.sidebar.button("🧹 Clear All Filters", on_click=reset_filters, use_container_width=True)

# 6. CSS OVERRIDES (THEME-PROOF NAV & MOBILE)
st.markdown("""
    <style>
        .nav-button {
            width: 100%; padding: 10px; border-radius: 5px; 
            border: 1px solid currentColor !important; 
            background: transparent !important; 
            color: inherit !important; 
            font-weight: bold; cursor: pointer;
            text-decoration: none !important;
            display: inline-block;
            text-align: center;
        }
        .nav-button:hover { opacity: 0.6; }
        [id] { scroll-margin-top: 150px !important; }
        
        .hero-card {
            flex: 1; min-width: 280px; 
            background: rgba(128, 128, 128, 0.1); 
            border: 1px solid rgba(128, 128, 128, 0.2); 
            border-radius: 12px; padding: 25px; 
            text-align: center; margin-bottom: 15px;
        }
        .hero-card h2 { margin: 10px 0; font-size: 2.2rem; }
        .hero-card p.label { margin: 0; font-size: 0.85rem; opacity: 0.7; text-transform: uppercase; }
        .hero-card p.context { margin-top: 10px; font-size: 0.75rem; opacity: 0.6; font-style: italic; }
        
        .quote-container { background: rgba(128, 128, 128, 0.05); border-left: 5px solid #DE0100; padding: 25px; border-radius: 5px; margin-bottom: 40px; }
    </style>
""", unsafe_allow_html=True)

# 7. BRANDED HEADER
st.markdown("""
    <a href="#top" style="text-decoration:none; color:inherit; display:flex; align-items:center; gap:20px; margin-bottom:30px;">
        <div style="font-size:2.5rem;">🍌</div>
        <h1 style="margin:0; font-weight:700;">U.S. Democracy Gone Bananas</h1>
    </a>
""", unsafe_allow_html=True)

# 8. HERO CARDS
if not filtered_df.empty:
    total_actions = len(filtered_df)
    days_active = max((selected_range[1] - selected_range[0]).days, 1)
    pace_per_month = (total_actions / days_active) * 30.44
    overlap = (len(filtered_df[filtered_df['Cat_Count'] > 1]) / total_actions * 100)

    st.markdown(f"""
    <div style="display: flex; justify-content: center; gap: 15px; width: 100%; flex-wrap: wrap;">
        <div class="hero-card">
            <p class="label">Total Actions</p>
            <h2>{total_actions}</h2>
            <p class="context">Total scale of administrative rewrite in the selected window.</p>
        </div>
        <div class="hero-card" style="border-color: #DE0100; background: rgba(222, 1, 0, 0.05);">
            <p class="label" style="color: #DE0100;">Velocity</p>
            <h2 style="color: #DE0100;">{pace_per_month:.1f}<span style="font-size: 1rem;">/mo</span></h2>
            <p class="context">Institutional rewrite rate; the pace of procedural change.</p>
        </div>
        <div class="hero-card">
            <p class="label">Strategic Overlap</p>
            <h2>{overlap:.1f}%</h2>
            <p class="context">Complexity indicator: actions striking multiple democratic pillars.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 9. STICKY NAV
st.markdown("""
    <div style="display: flex; justify-content: space-between; gap: 8px; position: sticky; top: 0; z-index: 999; backdrop-filter: blur(8px); padding: 15px 0;">
        <a href="#timeline" style="flex: 1;"><button class="nav-button">Timeline</button></a>
        <a href="#themes" style="flex: 1;"><button class="nav-button">Themes</button></a>
        <a href="#insights" style="flex: 1;"><button class="nav-button">Insights</button></a>
        <a href="#words" style="flex: 1;"><button class="nav-button">Words</button></a>
        <a href="#search" style="flex: 1;"><button class="nav-button">Search</button></a>
    </div>
""", unsafe_allow_html=True)

# 10. TIMELINE (RESPONSIVE FIX)
st.markdown("<div id='timeline'></div>", unsafe_allow_html=True)
if not filtered_df.empty:
    if comparison_mode:
        st.subheader("Velocity Analysis: Comparative Growth")
        long_cats = [c for c in df.columns if c in CATEGORY_MAP.keys()]
        comp_df = filtered_df.melt(id_vars=['Date', 'Title'], value_vars=long_cats, var_name='Mapping', value_name='Active')
        comp_df = comp_df[comp_df['Active'].str.strip().str.lower() == 'yes']
        comp_df['Theme'] = comp_df['Mapping'].map(CATEGORY_MAP)
        comp_df = comp_df.sort_values('Date')
        comp_df['Cumulative'] = comp_df.groupby('Theme').cumcount() + 1
        
        comp_chart = alt.Chart(comp_df).mark_line(interpolate='step-after', strokeWidth=3).encode(
            x=alt.X('Date:T', title='Timeline'),
            y=alt.Y('Cumulative:Q', title='Actions'),
            color=alt.Color('Theme:N', scale=alt.Scale(scheme='category10')),
            tooltip=['Date', 'Theme', 'Cumulative']
        ).properties(width='container', height=400).interactive()
        st.altair_chart(comp_chart, use_container_width=True)
    else:
        st.subheader(f"Timeline Progression: {selected_short}")
        chart_df = filtered_df.copy().sort_values('Date')
        if selected_short != "All Actions":
            chart_df = chart_df[chart_df[SHORT_TO_LONG[selected_short]].str.strip().str.lower() == 'yes']
        chart_df['Cumulative'] = range(1, len(chart_df) + 1)
        
        line = alt.Chart(chart_df).mark_line(interpolate='step-after', color='#DE0100', strokeWidth=3).encode(
            x=alt.X('Date:T', title='Timeline'),
            y=alt.Y('Cumulative:Q', title='Total Actions'),
            tooltip=['Date', 'Title']
        ).properties(width='container', height=400).interactive()
        st.altair_chart(line, use_container_width=True)

# 11. THEMES (DONUT)
st.markdown("<div id='themes'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🍩 Thematic Distribution (Donut)")
if not filtered_df.empty:
    donut_data = [{"value": int((filtered_df[long].str.strip().str.lower() == 'yes').sum()), "name": short} 
                  for long, short in CATEGORY_MAP.items() if (filtered_df[long].str.strip().str.lower() == 'yes').sum() > 0]
    donut_options = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {"orient": "horizontal", "bottom": "0", "textStyle": {"color": "inherit"}},
        "series": [{"type": "pie", "radius": ["40%", "70%"], "itemStyle": {"borderRadius": 10}, "label": {"show": False}, "data": donut_data}]
    }
    st_echarts(donut_options, height="450px")

# 12. INSIGHTS
st.markdown("<div id='insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: Strategic Diagnostic")
if not filtered_df.empty:
    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown("#### Strategic Velocity & Attrition")
        st.write(f"The administration is maintaining a velocity of **{pace_per_month:.1f} actions per month**. This volume induces 'procedural shock' designed to exhaust judicial oversight.")
    with col_ins2:
        st.markdown("#### The Resistance Heatmap")
        st.write("Opposition is currently concentrated in state-level hubs. Litigation remains the primary friction point.")
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
    st.dataframe(filtered_df[['Date', 'Title', 'URL', 'Themes_List']].sort_values('Date', ascending=False), 
                 column_config={"URL": st.column_config.LinkColumn("Source"), "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")},
                 use_container_width=True, hide_index=True)
st.caption("Dashboard by Celine Nadeau. Last updated 03-03-2026. CC BY 4.0.")
