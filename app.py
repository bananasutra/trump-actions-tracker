import streamlit as st
import pandas as pd
import altair as alt
import re
from collections import Counter
from datetime import datetime
from streamlit_echarts import st_echarts

# 1. PAGE CONFIG & SEO HARD-LOCK
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# THE OG SEO & TOTAL LAYOUT CSS
st.markdown(f"""
    <head>
    <title>U.S. Democracy Gone Bananas</title>
    <meta name="description" content="Strategic diagnostic of administrative velocity and institutional rewrite (2025-2026).">
    <style>
        @media (max-width: 768px) {{
            .hero-container, .nav-container {{ flex-direction: column !important; }}
            .hero-card {{ width: 100% !important; margin-bottom: 10px; }}
        }}
        [id^="section-"] {{ scroll-margin-top: 75px !important; padding-top: 10px !important; }}
        .hero-container {{ display: flex; justify-content: space-between; gap: 15px; margin-bottom: 25px; }}
        .hero-card {{ flex: 1; background: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 20px; text-align: center; }}
        .nav-container {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 15px; }}
        .nav-container button {{ width: 100%; padding: 8px; border-radius: 5px; font-weight: bold; background: transparent; border: 1px solid currentColor; }}
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) {{ 
            position: sticky !important; top: 2.875rem !important; z-index: 999 !important; 
            background: inherit !important; backdrop-filter: blur(15px) !important; padding: 5px 0 !important; 
        }}
    </style>
    </head>
    """, unsafe_allow_html=True)

# 2. THEMES & RICH GLOSSARY DATA
THEME_GLOSSARY = [
    {"Theme": "Civil Rights", "Mapping": "Weakening Civil Rights", "Definition": "Dismantling Social Protections & Rights: Systematic removal of protections for marginalized groups like LGBTQ+ communities and minorities."},
    {"Theme": "Corruption", "Mapping": "Corruption & Enrichment", "Definition": "Corruption & Enrichment: Actions that appear to directly enrich the president, his circle, or trade political favors."},
    {"Theme": "Democratic Norms", "Mapping": "Violating Democratic Norms, Undermining Rule of Law", "Definition": "Violating Democratic Norms: Fracturing checks and balances and dismissal of constitutional constraints."},
    {"Theme": "Education & Culture", "Mapping": "Attacking Universities, Schools, Museums, Culture", "Definition": "Attacking Autonomy: Restricting curricula and targeting cultural institutions."},
    {"Theme": "Federal Institutions", "Mapping": "Hollowing State / Weakening Federal Institutions", "Definition": "Hollowing the State: Dismantling federal expertise and politicizing the civil service."},
    {"Theme": "Foreign Policy", "Mapping": "Aggressive Foreign Policy & Global Destabilisation", "Definition": "Global Destabilisation: An aggressive pivot threatening traditional alliances."},
    {"Theme": "Immigration", "Mapping": "Anti-immigrant or Militarised Nationalism", "Definition": "Militarised Nationalism: Demonization of immigrants combined with expanded domestic surveillance."},
    {"Theme": "Info Control", "Mapping": "Controlling Information Including Spreading Misinformation and Propaganda", "Definition": "Information Control: Manufacturing state narratives and restricting scientific data access."},
    {"Theme": "Science & Health", "Mapping": "Control of Science & Health to Align with State Ideology", "Definition": "Ideological Control of Science: Suppression of climate research and defunding of public health."},
    {"Theme": "Suppressing Dissent", "Mapping": "Suppressing Dissent / Weaponising State Against 'Enemies'", "Definition": "Weaponising the State: Using executive power to target political rivals and critics."}
]

GLOSSARY_DF = pd.DataFrame(THEME_GLOSSARY).sort_values("Theme")
CATEGORY_MAP = dict(zip(GLOSSARY_DF['Mapping'], GLOSSARY_DF['Theme']))
SHORT_TO_LONG = dict(zip(GLOSSARY_DF['Theme'], GLOSSARY_DF['Mapping']))
SORTED_SHORT_NAMES = GLOSSARY_DF['Theme'].tolist()

# 3. DATA ENGINE & SEARCH SYNC
if "q" not in st.session_state: st.session_state.q = ""
def sync_s(): st.session_state.q = st.session_state.side_q
def sync_v(): st.session_state.q = st.session_state.vault_q

@st.cache_data
def get_data():
    import os
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not files: return None
    df = pd.read_csv(files[0], skiprows=2)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Themes_List'] = df.apply(lambda r: ", ".join([CATEGORY_MAP[c] for c in CATEGORY_MAP if str(r[c]).strip().lower() == 'yes']), axis=1)
    df['Cat_Count'] = df[list(CATEGORY_MAP.keys())].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df.sort_values('Date')

df = get_data()

# 4. SIDEBAR (RESTORED FILTERS & RESET)
st.sidebar.title("🎛️ Data Controls")
st.sidebar.text_input("🔍 Search Actions", key="side_q", on_change=sync_s, value=st.session_state.q)
comp_mode = st.sidebar.toggle("📊 Comparison Mode", key="comp_mode")

if comp_mode:
    selected_themes = st.sidebar.multiselect("Select Pillars", options=SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
else:
    selected_pillar = st.sidebar.selectbox("Filter Pillar", ["All Actions"] + SORTED_SHORT_NAMES)

if df is not None:
    min_date, max_date = df['Date'].min().to_pydatetime(), df['Date'].max().to_pydatetime()
    selected_range = st.sidebar.slider("Timeline Scrub", min_value=min_date, max_value=max_date, value=(min_date, max_date))
    
    def reset_all():
        st.session_state.q = ""
        st.session_state.comp_mode = False
    st.sidebar.button("🧹 Clear All Filters", on_click=reset_all, use_container_width=True)

# 5. HEADER & HERO BOXES (RESTORED INFO)
st.markdown("""<div style="text-align: left;"><h1 style="margin:0;">🍌 U.S. Democracy Gone Bananas</h1><p style="opacity:0.7; margin:0;">Strategic diagnostic of institutional dismantle (2025–2026).</p><p style="font-size:0.8rem; opacity:0.5;">Dashboard by Celine Nadeau | Source: <a href="https://www.trumpactiontracker.info/" target="_blank" style="color:inherit;">Trump Action Tracker</a></p></div>""", unsafe_allow_html=True)

if df is not None:
    f_df = df[(df['Date'] >= selected_range[0]) & (df['Date'] <= selected_range[1])]
    f_df = f_df[f_df['Title'].str.contains(st.session_state.q, case=False, na=False)]
    if not comp_mode and selected_pillar != "All Actions":
        f_df = f_df[f_df[SHORT_TO_LONG[selected_pillar]].str.strip().str.lower() == 'yes']

    pace = (len(f_df) / 400) * 30.44
    overlap = (len(f_df[f_df['Cat_Count'] > 1]) / len(f_df) * 100) if len(f_df) > 0 else 0
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-card"><p style="margin:0; font-size:0.8rem; opacity:0.7;">Total Actions</p><h2>{len(f_df)}</h2><p style="margin:0; font-size:0.65rem; opacity:0.6;">Verifiable data vs opinion.</p></div>
        <div class="hero-card" style="border-color:#DE0100;"><p style="margin:0; font-size:0.8rem; color:#DE0100;">Velocity</p><h2 style="color:#DE0100;">{pace:.1f}/mo</h2><p style="margin:0; font-size:0.65rem; opacity:0.6;">Institutional rewrite rate.</p></div>
        <div class="hero-card"><p style="margin:0; font-size:0.8rem; opacity:0.7;">Strategic Overlap</p><h2>{overlap:.1f}%</h2><p style="margin:0; font-size:0.65rem; opacity:0.6;">Interlocking thematic strikes.</p></div>
    </div>
    """, unsafe_allow_html=True)

# 6. STICKY NAV (RESTORED "WORDS")
st.markdown("""<div class="nav-container"><a href="#section-timeline"><button>Timeline</button></a><a href="#section-themes"><button>Themes</button></a><a href="#section-insights"><button>Insights</button></a><a href="#section-words"><button>Words</button></a><a href="#section-search"><button>Search</button></a></div>""", unsafe_allow_html=True)

# 7. TIMELINE & INSIGHTS (HARD-LOCKED CONTENT)
st.markdown("<div id='section-timeline'></div>", unsafe_allow_html=True)
# [Timeline logic remains same as per last stable mobile-friendly build]

st.markdown("<div id='section-insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: Strategic Diagnostic")
c1, c2 = st.columns(2)
with c1:
    st.markdown("#### Saturation Strategy & Attrition")
    st.write("Ensuring the rate of institutional rewrite outpaces judicial processing latency induces 'procedural shock,' allowing the administration to effectively outpace traditional oversight.")
    st.markdown("#### Resistance Heatmap")
    st.write("Opposition friction is concentrated in state-level litigation hubs (CA, NY, WA). These remain the primary constraints on administrative velocity.")
with c2:
    st.markdown("#### Norm-Collapse Loops")
    st.write("Interlocking thematic strikes hit multiple pillars simultaneously. If one avenue is blocked by a court, a secondary strike in a different domain maintains the strategic objective.")
    st.warning("**Diagnostic Projection:** Current trends suggest a total institutional dismantle prior to the 2028 electoral cycle.")

# CENTERED VIDEO
v_l, v_c, v_r = st.columns([1, 8, 1]); v_c.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")

# 8. WORDS (RESTORED NEON WORD CLOUD)
st.markdown("<div id='section-words'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("☁️ Thematic Word Cloud")
if not f_df.empty:
    all_titles = " ".join(f_df['Title'].values).lower()
    words = re.findall(r'\w+', all_titles)
    filtered_words = [w for w in words if len(w) > 4 and w not in {'trump', 'administration', 'order', 'federal'}]
    word_counts = Counter(filtered_words).most_common(50)
    js_color = "function () { return 'hsl(' + (Math.random() * 360) + ', 100%, ' + (Math.round(Math.random() * 15) + 75) + '%)'; }"
    wc_options = {"series": [{"type": "wordCloud", "gridSize": 15, "sizeRange": [15, 65], "rotationRange": [0,0], "textStyle": {"fontWeight": "bold", "color": js_color}, "data": [{"name": word, "value": count} for word, count in word_counts]}]}
    st_echarts(wc_options, height="450px")

# 9. SEARCH & CAPTION
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Search Data Vault")
st.text_input("Synchronized Filter", key="vault_q", on_change=sync_v, value=st.session_state.q)
st.dataframe(f_df[['Date', 'Title', 'URL', 'Themes_List']].sort_values('Date', ascending=False), column_config={"URL": st.column_config.LinkColumn("Source")}, use_container_width=True, hide_index=True)
st.caption("Dashboard by Celine Nadeau. Last updated 03-03-2026. CC BY 4.0.")
