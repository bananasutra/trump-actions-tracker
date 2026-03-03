import streamlit as st
import pandas as pd
import altair as alt
import re
from collections import Counter
from datetime import datetime
from streamlit_echarts import st_echarts

# 1. PAGE CONFIG & SEO HACK (HARD LOCK)
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# THE OG SEO WORKAROUND (Syntax-Safe with Doubled Braces)
st.markdown(f"""
    <head>
    <title>U.S. Democracy Gone Bananas</title>
    <meta name="description" content="Strategic diagnostic of administrative velocity and institutional rewrite (2025-2026).">
    <meta property="og:title" content="U.S. Democracy Gone Bananas: Tracker">
    <meta property="og:description" content="A real-time diagnostic of systemic democratic erosion and institutional dismantling.">
    <meta property="og:image" content="https://raw.githubusercontent.com/celinenadeau/repo/main/og-image.png">
    <meta name="twitter:card" content="summary_large_image">
    <style>
        /* SURGICAL SCROLL OFFSET - 70px precision to match sticky bar */
        [id^="section-"] {{
            scroll-margin-top: 70px !important;
            padding-top: 5px !important;
        }}
        
        /* BLUE-FREE NAV LOCK */
        .nav-container {{ 
            display: flex !important; 
            justify-content: space-between !important; 
            gap: 10px !important; 
            width: 100% !important; 
            margin-bottom: -5px !important; 
        }}
        .nav-container a {{ flex: 1 !important; text-decoration: none !important; color: inherit !important; }}
        .nav-container button {{
            width: 100% !important; padding: 6px 12px !important; border-radius: 5px !important;
            font-weight: bold !important; background-color: transparent !important;
            border: 1px solid currentColor !important; color: inherit !important; 
            box-shadow: none !important; transition: 0.2s !important;
        }}
        
        /* STICKY NAV RE-ANCHOR */
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) {{ 
            position: sticky !important; top: 2.875rem !important; z-index: 999 !important; 
            background: inherit !important; backdrop-filter: blur(15px) !important; padding: 5px 0 !important; 
        }}
    </style>
    </head>
    """, unsafe_allow_html=True)

# 2. WELCOME DIALOG
@st.dialog("Strategic Note on Facts")
def show_welcome():
    st.markdown("""
    **Opinions shall not trump the data.** In an era of certainty, this tracker is built for **verifiable doubt**.
    ---
    Click anywhere outside this box to begin your investigation.
    """)

if "first_visit" not in st.session_state:
    st.session_state.first_visit = True
    show_welcome()

# 3. SEARCH SYNC LOGIC
if "search_term" not in st.session_state: st.session_state.search_term = ""
def sync_sidebar(): st.session_state.search_term = st.session_state.sidebar_search
def sync_vault(): st.session_state.search_term = st.session_state.vault_search

# 4. THEMES & GLOSSARY DATA
THEME_GLOSSARY = [
    {"Theme": "Civil Rights", "Mapping": "Weakening Civil Rights", "Definition": "Dismantling Social Protections & Rights: A systematic removal of protections for marginalized groups like LGBTQ+ communities, immigrants, and minorities."},
    {"Theme": "Corruption", "Mapping": "Corruption & Enrichment", "Definition": "Corruption & Enrichment: Actions that appear to directly enrich the president, his circle, or trade political favors."},
    {"Theme": "Democratic Norms", "Mapping": "Violating Democratic Norms, Undermining Rule of Law", "Definition": "Violating Democratic Norms & Rule of Law: The fracturing of checks and balances and dismissal of constitutional constraints."},
    {"Theme": "Education & Culture", "Mapping": "Attacking Universities, Schools, Museums, Culture", "Definition": "Attacking Intellectual & Cultural Autonomy: Restricting curricula and targeting cultural institutions."},
    {"Theme": "Federal Institutions", "Mapping": "Hollowing State / Weakening Federal Institutions", "Definition": "Hollowing the State: Dismantling federal expertise and politicizing the civil service."},
    {"Theme": "Foreign Policy", "Mapping": "Aggressive Foreign Policy & Global Destabilisation", "Definition": "Global Destabilisation: An aggressive pivot that threatens traditional alliances and aligns with rivals."},
    {"Theme": "Immigration & Nationalism", "Mapping": "Anti-immigrant or Militarised Nationalism", "Definition": "Militarised Nationalism: The demonization of immigrants combined with expanded domestic surveillance."},
    {"Theme": "Info Control", "Mapping": "Controlling Information Including Spreading Misinformation and Propaganda", "Definition": "Information Control: Manufacturing state narratives and restricting scientific data access."},
    {"Theme": "Science & Health", "Mapping": "Control of Science & Health to Align with State Ideology", "Definition": "Ideological Control of Science: Suppression of climate research and defunding of public health."},
    {"Theme": "Suppressing Dissent", "Mapping": "Suppressing Dissent / Weaponising State Against 'Enemies'", "Definition": "Weaponising the State: Using executive power to target political rivals and critics."}
]

GLOSSARY_DF = pd.DataFrame(THEME_GLOSSARY).sort_values("Theme")
CATEGORY_MAP = dict(zip(GLOSSARY_DF['Mapping'], GLOSSARY_DF['Theme']))
SHORT_TO_LONG = dict(zip(GLOSSARY_DF['Theme'], GLOSSARY_DF['Mapping']))
SORTED_SHORT_NAMES = GLOSSARY_DF['Theme'].tolist()

# 5. DATA LOADING
@st.cache_data
def load_data():
    import os
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not files: return None
    target = files[0]
    df = pd.read_csv(target, skiprows=2)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=True) 
    cat_cols = list(CATEGORY_MAP.keys())
    df['Themes_List'] = df.apply(lambda r: ", ".join([CATEGORY_MAP.get(c, c) for c in cat_cols if str(r[c]).strip().lower() == 'yes']), axis=1)
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df

df = load_data()

# 6. HEADER (LEFT-ALIGNED)
st.markdown("""
    <div style="text-align: left;">
        <a href="/?" style="text-decoration:none; color:inherit; display:flex; align-items:center; gap:15px;">
            <div style="font-size:2.5rem;">🍌</div>
            <h1 style="font-size: 2.8rem; font-weight: 800; margin-bottom: 0px;">U.S. Democracy Gone Bananas</h1>
        </a>
        <p style="opacity:0.7; font-size:1.1rem; margin-top:-5px; margin-bottom:5px;">A real-time diagnostic of systemic institutional dismantle and administrative rewrite (2025–2026).</p>
        <p style="font-size:0.8rem; opacity:0.5; margin-bottom:15px;">Dashboard by <b>Celine Nadeau</b> | Source: <a href="https://www.trumpactiontracker.info/" target="_blank" style="color:inherit; text-decoration:underline;">Christina Pagel / Trump Action Tracker</a></p>
    </div>
""", unsafe_allow_html=True)

# 7. SIDEBAR & SEARCH LOGIC
st.sidebar.title("🎛️ Data Controls")
st.sidebar.text_input("🔍 Search Actions", key="sidebar_search", on_change=sync_sidebar, value=st.session_state.search_term)
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", key="comparison_toggle")

if comparison_mode:
    selected_themes = st.sidebar.multiselect("Select Themes", options=SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
else:
    selected_theme = st.sidebar.selectbox("Filter Pillar", ["All Actions"] + SORTED_SHORT_NAMES)

if df is not None:
    min_date, max_date = df['Date'].min().to_pydatetime(), df['Date'].max().to_pydatetime()
    selected_range = st.sidebar.slider("Timeline Scrub", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="MMM DD")
    mask = (df['Date'] >= selected_range[0]) & (df['Date'] <= selected_range[1])
    if st.session_state.search_term:
        mask = mask & (df['Title'].str.contains(st.session_state.search_term, case=False, na=False))
    filtered_df = df.loc[mask]
    if not comparison_mode and selected_theme != "All Actions":
        filtered_df = filtered_df[filtered_df[SHORT_TO_LONG[selected_theme]].str.strip().str.lower() == 'yes']

# 8. STICKY NAV
st.markdown("""<div class="nav-container"><a href="#section-timeline"><button>Timeline</button></a><a href="#section-themes"><button>Themes</button></a><a href="#section-insights"><button>Insights</button></a><a href="#section-words"><button>Words</button></a><a href="#section-search"><button>Search</button></a></div>""", unsafe_allow_html=True)

# 9. TIMELINE (4-ROW TOOLTIP & LINK WARNING)
st.markdown("<div id='section-timeline'></div>", unsafe_allow_html=True)
st.subheader("Action Progression")
if not filtered_df.empty:
    chart_df = filtered_df.copy().sort_values('Date')
    chart_df['Cumulative'] = range(1, len(chart_df) + 1)
    
    line = alt.Chart(chart_df).mark_line(interpolate='step-after', color='#DE0100', strokeWidth=3).encode(
        x='Date:T', y='Cumulative:Q', href='URL:N',
        tooltip=[
            alt.Tooltip('Date:T', format='%Y-%m-%d'),
            alt.Tooltip('Title:N', title='Action'),
            alt.Tooltip('Themes_List:N', title='Themes Hit'),
            alt.Tooltip('URL:N', title='Source URL')
        ]
    ).properties(width='container', height=400).interactive()
    
    st.altair_chart(line, use_container_width=True)
    
    # HARD-LOCKED LINK BEHAVIOR WARNING
    st.markdown("""<p style='font-size:0.75rem; opacity:0.6; font-style:italic; margin-top:-20px;'>💡 <b>Navigation:</b> Hover for 4-row data. Scroll/pinch to zoom. <br>🔗 <b>Link Behavior:</b> Some sites (Guardian, NYT, NBC, AP) block internal opening. Use the <b>Search Data Vault</b> below for direct links.</p>""", unsafe_allow_html=True)

# 10. THEMES
st.markdown("<div id='section-themes'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Action Volume by Pillar")
if not filtered_df.empty:
    cat_counts = [{'Theme': short, 'Count': (filtered_df[long].str.strip().str.lower() == 'yes').sum()} for long, short in CATEGORY_MAP.items()]
    theme_bar = alt.Chart(pd.DataFrame(cat_counts)).mark_bar(color='#DE0100').encode(x=alt.X('Count:Q', title="Actions"), y=alt.Y('Theme:N', sort='-x', title=None), tooltip=['Theme', 'Count']).properties(height=400).interactive()
    st.altair_chart(theme_bar, use_container_width=True)

# 11. INSIGHTS (DUAL COLUMN + CENTERED VIDEO)
st.markdown("<div id='section-insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: Strategic Diagnostic")
if not filtered_df.empty:
    ins_col1, ins_col2 = st.columns(2)
    with ins_col1:
        st.markdown("#### Strategic Velocity & Attrition")
        st.write("Moving at high administrative velocity induces 'procedural shock.' By ensuring the rate of institutional rewrite outpaces judicial processing latency, the administration effectively outruns traditional oversight.")
    with ins_col2:
        st.markdown("#### Norm-Collapse Loops")
        st.write("Interlocking thematic strikes hit multiple pillars simultaneously. If one avenue is blocked by a court, a secondary strike in a different domain maintains the strategic objective.")

    st.markdown(f"""<div style="background: rgba(128, 128, 128, 0.05); border-left: 5px solid #DE0100; padding: 20px; border-radius: 5px; margin: 25px 0;"><p style="font-style: italic; margin-bottom: 5px;">"fools and fanatics are always so certain of themselves, and wiser people so full of doubts."</p><p style="text-align: right; font-weight: bold; margin: 0;">— Bertrand Russell</p></div>""", unsafe_allow_html=True)
    
    v_l, v_c, v_r = st.columns([1, 8, 1])
    with v_c: st.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")

# 12. WORD CLOUD
st.markdown("<div id='section-words'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("☁️ Thematic Word Cloud")
if not filtered_df.empty:
    all_titles = " ".join(filtered_df['Title'].values).lower()
    words = re.findall(r'\w+', all_titles)
    filtered_words = [w for w in words if w not in {'the', 'and', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'up', 'about', 'into', 'over', 'after', 'trump', 'administration', 'order', 'federal', 'u.s.', 'president', 'will', 'this', 'that'} and len(w) > 3]
    word_counts = Counter(filtered_words).most_common(50)
    js_color = "function () { return 'hsl(' + (Math.random() * 360) + ', 100%, ' + (Math.round(Math.random() * 15) + 75) + '%)'; }"
    wc_options = {"backgroundColor": "transparent", "series": [{"type": "wordCloud", "gridSize": 15, "sizeRange": [16, 70], "rotationRange": [0,0], "textStyle": {"fontWeight": "bold", "color": js_color}, "data": [{"name": word, "value": count} for word, count in word_counts]}]}
    st_echarts(wc_options, height="450px")

# 13. VAULT (SYNCHRONIZED SEARCH RESTORED)
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Search Data Vault")
st.text_input("Synchronized Search (Updates sidebar filters)", key="vault_search", on_change=sync_vault, value=st.session_state.search_term)

if not filtered_df.empty:
    st.dataframe(filtered_df[['Date', 'Title', 'URL', 'Themes_List']].sort_values('Date', ascending=False), column_config={"URL": st.column_config.LinkColumn("Source"), "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")}, use_container_width=True, hide_index=True)
st.caption("Dashboard by Celine Nadeau. Last updated 03-03-2026. CC BY 4.0.")
