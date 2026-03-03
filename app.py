import streamlit as st
import pandas as pd
import altair as alt
import re
from collections import Counter
from streamlit_echarts import st_echarts

# 1. PAGE CONFIG & SEO HARD-LOCK
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# THE OG SEO WORKAROUND & LAYOUT CSS
st.markdown(f"""
    <head>
    <title>U.S. Democracy Gone Bananas</title>
    <meta name="description" content="Strategic diagnostic of administrative velocity and institutional rewrite (2025-2026).">
    <meta property="og:image" content="https://raw.githubusercontent.com/celinenadeau/repo/main/og-image.png">
    <style>
        /* 1. RESPONSIVE UTILITIES */
        @media (max-width: 768px) {{
            .hero-container {{ flex-direction: column !important; }}
            .nav-container {{ flex-direction: column !important; gap: 5px !important; }}
            .hero-card {{ width: 100% !important; margin-bottom: 10px; }}
        }}
        
        /* 2. PRECISION ANCHORING (NO OVERLAP) */
        [id^="section-"] {{ scroll-margin-top: 75px !important; padding-top: 10px !important; }}
        
        /* 3. HERO BOXES & NAV STYLING */
        .hero-container {{ display: flex; justify-content: space-between; gap: 15px; width: 100%; margin-bottom: 25px; }}
        .hero-card {{ flex: 1; background: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 20px; text-align: center; }}
        .nav-container {{ display: flex; justify-content: space-between; gap: 10px; width: 100%; margin-bottom: 15px; }}
        .nav-container button {{ width: 100%; padding: 8px; border-radius: 5px; font-weight: bold; background: transparent; border: 1px solid currentColor; cursor: pointer; }}
        
        /* 4. STICKY NAV LOCK */
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) {{ 
            position: sticky !important; top: 2.875rem !important; z-index: 999 !important; 
            background: inherit !important; backdrop-filter: blur(15px) !important; padding: 5px 0 !important; 
        }}
    </style>
    </head>
    """, unsafe_allow_html=True)

# 2. STRATEGIC MAPPINGS
THEME_DATA = [
    {"T": "Civil Rights", "M": "Weakening Civil Rights", "D": "Dismantling protections for marginalized groups."},
    {"T": "Corruption", "M": "Corruption & Enrichment", "D": "Actions enriching the executive circle."},
    {"T": "Democratic Norms", "M": "Violating Democratic Norms, Undermining Rule of Law", "D": "Fracturing checks and balances."},
    {"T": "Education", "M": "Attacking Universities, Schools, Museums, Culture", "D": "Restricting curricula and cultural autonomy."},
    {"T": "Federal Inst.", "M": "Hollowing State / Weakening Federal Institutions", "D": "Dismantling federal expertise."},
    {"T": "Foreign Policy", "M": "Aggressive Foreign Policy & Global Destabilisation", "D": "Pivoting away from traditional alliances."},
    {"T": "Immigration", "M": "Anti-immigrant or Militarised Nationalism", "D": "Militarised domestic surveillance."},
    {"T": "Info Control", "M": "Controlling Information Including Spreading Misinformation and Propaganda", "D": "State-led narrative manufacturing."},
    {"T": "Science/Health", "M": "Control of Science & Health to Align with State Ideology", "D": "Suppression of climate/health research."},
    {"T": "Dissent", "M": "Suppressing Dissent / Weaponising State Against 'Enemies'", "D": "Targeting political rivals."}
]
MAP = {item['M']: item['T'] for item in THEME_DATA}
REV_MAP = {item['T']: item['M'] for item in THEME_DATA}

# 3. DATA ENGINE
@st.cache_data
def get_data():
    import os
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not files: return None
    df = pd.read_csv(files[0], skiprows=2)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Themes_List'] = df.apply(lambda r: ", ".join([MAP[c] for c in MAP if str(r[c]).strip().lower() == 'yes']), axis=1)
    df['Cat_Count'] = df[list(MAP.keys())].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df.sort_values('Date')

df = get_data()

# 4. SEARCH SYNC & SIDEBAR
if "q" not in st.session_state: st.session_state.q = ""
def sync(): st.session_state.q = st.session_state.side_q
def sync_v(): st.session_state.q = st.session_state.vault_q

st.sidebar.title("🎛️ Controls")
st.sidebar.text_input("🔍 Search", key="side_q", on_change=sync, value=st.session_state.q)
comp = st.sidebar.toggle("📊 Comparison Mode")

if df is not None:
    f_df = df[df['Title'].str.contains(st.session_state.q, case=False, na=False)]
    
    # 5. HEADER & HERO CARDS (RESTORED)
    st.markdown("""<div style="text-align: left;"><h1 style="margin:0;">🍌 U.S. Democracy Gone Bananas</h1><p style="opacity:0.7; margin:0;">Strategic diagnostic of institutional rewrite (2025–2026).</p><p style="font-size:0.8rem; opacity:0.5;">Dashboard by <b>Celine Nadeau</b> | Source: <a href="https://www.trumpactiontracker.info/" target="_blank" style="color:inherit;">Christina Pagel / Trump Action Tracker</a></p></div>""", unsafe_allow_html=True)
    
    pace = (len(f_df) / 400) * 30.44
    overlap = (len(f_df[f_df['Cat_Count'] > 1]) / len(f_df) * 100) if len(f_df) > 0 else 0
    st.markdown(f"""<div class="hero-container"><div class="hero-card"><p style="margin:0; font-size:0.8rem; opacity:0.7;">Actions</p><h2>{len(f_df)}</h2></div><div class="hero-card" style="border-color:#DE0100;"><p style="margin:0; font-size:0.8rem; color:#DE0100;">Velocity</p><h2 style="color:#DE0100;">{pace:.1f}/mo</h2></div><div class="hero-card"><p style="margin:0; font-size:0.8rem; opacity:0.7;">Strategic Overlap</p><h2>{overlap:.1f}%</h2></div></div>""", unsafe_allow_html=True)

# 6. STICKY NAV
st.markdown("""<div class="nav-container"><a href="#section-timeline"><button>Timeline</button></a><a href="#section-themes"><button>Themes</button></a><a href="#section-insights"><button>Insights</button></a><a href="#section-search"><button>Search</button></a></div>""", unsafe_allow_html=True)

# 7. TIMELINE & COMPARISON
st.markdown("<div id='section-timeline'></div>", unsafe_allow_html=True)
if comp:
    sel = st.sidebar.multiselect("Select Pillars", options=list(REV_MAP.keys()), default=list(REV_MAP.keys())[:3])
    comp_df = f_df.melt(id_vars=['Date','Title','URL','Themes_List'], value_vars=[REV_MAP[s] for s in sel], var_name='M', value_name='A')
    comp_df = comp_df[comp_df['A'].str.strip().str.lower() == 'yes']
    comp_df['Theme'] = comp_df['M'].map(MAP)
    comp_df['Cumulative'] = comp_df.groupby('Theme').cumcount() + 1
    chart = alt.Chart(comp_df).mark_line(interpolate='step-after').encode(x='Date:T', y='Cumulative:Q', color='Theme:N', tooltip=['Date','Title','Theme','Cumulative','URL'])
else:
    chart_df = f_df.copy(); chart_df['Cumulative'] = range(1, len(chart_df)+1)
    chart = alt.Chart(chart_df).mark_line(interpolate='step-after', color='#DE0100').encode(x='Date:T', y='Cumulative:Q', tooltip=['Date','Title','Themes_List','URL'])
st.altair_chart(chart.properties(width='container', height=400).interactive(), use_container_width=True)
st.markdown("<p style='font-size:0.75rem; opacity:0.6; font-style:italic; margin-top:-15px;'>💡 Hover for 4-row diagnostic data. Click points for source URL. Scroll to zoom.</p>", unsafe_allow_html=True)

# 8. THEMES & GLOSSARY
st.markdown("<div id='section-themes'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Action Volume by Pillar")
counts = [{'Pillar': MAP[m], 'Count': (f_df[m].str.strip().str.lower() == 'yes').sum()} for m in MAP]
st.altair_chart(alt.Chart(pd.DataFrame(counts)).mark_bar(color='#DE0100').encode(x='Count:Q', y=alt.Y('Pillar:N', sort='-x'), tooltip=['Pillar','Count']).properties(height=350).interactive(), use_container_width=True)
with st.expander("📖 Strategic Themes Glossary"):
    st.table(pd.DataFrame(THEME_DATA).rename(columns={"T": "Pillar", "D": "Strategic Definition"})[["Pillar", "Strategic Definition"]])

# 9. INSIGHTS
st.markdown("<div id='section-insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights")
c1, c2 = st.columns(2)
with c1: st.write("**Saturation Strategy:** Velocity outpaces judicial latency, inducing procedural shock."); st.write("**Resistance Heatmap:** Litigation friction is highest in state-level hubs (CA, NY).")
with c2: st.write("**Norm-Collapse Loops:** Interlocking strikes hit multiple pillars, rendering single-domain resistance moot.")
st.markdown(f"""<div style="background:rgba(128,128,128,0.05); border-left:5px solid #DE0100; padding:15px; border-radius:5px; margin:20px 0;"><p style="font-style:italic; margin-bottom:5px;">"fools and fanatics are always so certain of themselves..."</p><p style="text-align:right; font-weight:bold; margin:0;">— Bertrand Russell</p></div>""", unsafe_allow_html=True)
v_l, v_c, v_r = st.columns([1, 8, 1]); v_c.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")

# 10. SEARCH VAULT (SYNCED)
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Search Data Vault")
st.text_input("Synchronized Filter", key="vault_q", on_change=sync_v, value=st.session_state.q)
st.dataframe(f_df[['Date', 'Title', 'URL', 'Themes_List']].sort_values('Date', ascending=False), column_config={"URL": st.column_config.LinkColumn("Source")}, use_container_width=True, hide_index=True)
st.caption("Dashboard by Celine Nadeau aka banansutra. Last updated 03-03-2026. CC BY 4.0.")
