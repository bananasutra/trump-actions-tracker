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

st.markdown(f"""
    <head>
    <title>U.S. Democracy Gone Bananas</title>
    <meta name="description" content="Strategic diagnostic of administrative velocity and institutional rewrite (2025-2026).">
    <meta property="og:title" content="U.S. Democracy Gone Bananas: Tracker">
    <meta property="og:image" content="https://raw.githubusercontent.com/celinenadeau/repo/main/og-image.png">
    <meta name="twitter:card" content="summary_large_image">
    </head>
    """, unsafe_allow_html=True)

# 2. WELCOME DIALOG
@st.dialog("Strategic Note on Facts")
def show_welcome():
    st.markdown("""
    **Opinions shall not trump the data.** In an era of certainty, this tracker is built for **verifiable doubt**.
    * **Velocity:** institutional rewrite rate.
    * **Complexity:** interlocking thematic strikes.
    ---
    Click anywhere outside this box to begin your investigation.
    """)

if "first_visit" not in st.session_state:
    st.session_state.first_visit = True
    show_welcome()

# 3. THEMES & RICH GLOSSARY
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

# 4. CSS (PRECISION ANCHORING & TOOLTIP COMPACTION)
st.markdown("""
    <style>
        /* 1. NUCLEAR NAV RESET (BLUE-FREE + TIGHT PADDING) */
        .nav-container { display: flex !important; justify-content: space-between !important; gap: 10px !important; width: 100% !important; }
        .nav-container a { flex: 1 !important; text-decoration: none !important; color: inherit !important; }
        .nav-container button, .nav-container button:hover, .nav-container button:active, .nav-container button:focus {
            width: 100% !important; padding: 6px 12px !important; border-radius: 5px !important;
            font-weight: bold !important; background-color: transparent !important;
            border: 1px solid currentColor !important; color: inherit !important; 
            box-shadow: none !important; transition: 0.2s !important;
        }

        /* 2. PRECISION ANCHORING & SECTION BREATHING */
        [id] { 
            scroll-margin-top: 135px !important; 
            padding-top: 25px !important; 
        }

        /* 3. COMPACT TOOLTIPS (NEGATIVE MARGIN LOCK) */
        .compact-tips { 
            margin-top: -40px !important; 
            padding: 0 !important;
            display: flex; 
            justify-content: space-between; 
            gap: 20px; 
            flex-wrap: wrap; 
        }
        .compact-tips p { margin: 0 !important; padding: 0 !important; line-height: 1.1 !important; font-size: 0.72rem !important; opacity: 0.6; font-style: italic; }

        /* 4. HEADER STYLING (LEFT ALIGNED) */
        .main-header { font-size: 2.8rem !important; font-weight: 800; margin-bottom: 0px; text-align: left; }
        .sub-header { opacity: 0.7; font-size: 1.1rem; margin-top: -5px; margin-bottom: 5px; text-align: left; }
        .source-line { font-size: 0.8rem; opacity: 0.5; margin-bottom: 30px; text-align: left; }

        /* 5. STICKY NAV RE-ANCHOR */
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) { 
            position: sticky !important; top: 2.875rem !important; z-index: 999 !important; 
            background: inherit !important; backdrop-filter: blur(15px) !important; padding: 5px 0 !important; 
        }

        /* 6. UI HERO CARDS */
        .hero-card { flex: 1; background: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 20px; text-align: center; }
        .hero-container { display: flex !important; justify-content: space-between !important; gap: 15px !important; width: 100% !important; margin-bottom: 10px; }
        
        @media (max-width: 768px) {
            .nav-container, .hero-container { flex-direction: column !important; }
            .nav-container a, .hero-card { width: 100% !important; }
        }
    </style>
""", unsafe_allow_html=True)

# 5. DATA LOADING
@st.cache_data
def load_data():
    import os
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not files: return None
    target = 'trump-actions.csv' if 'trump-actions.csv' in files else files[0]
    df = pd.read_csv(target, skiprows=2)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=True) 
    cat_cols = list(CATEGORY_MAP.keys())
    df['Themes_List'] = df.apply(lambda r: ", ".join([CATEGORY_MAP.get(c, c) for c in cat_cols if str(r[c]).strip().lower() == 'yes']), axis=1)
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df

df = load_data()

# 6. HEADER (LEFT-ALIGNED AUTHORITY)
st.markdown("<div id='top'></div>", unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: left;">
        <a href="/?" style="text-decoration:none; color:inherit; display:flex; align-items:center; gap:15px;">
            <div style="font-size:2.5rem;">🍌</div>
            <h1 class="main-header">U.S. Democracy Gone Bananas</h1>
        </a>
        <p class="sub-header">A real-time diagnostic of systemic institutional dismantle and administrative rewrite (2025–2026).</p>
        <p class="source-line">
            Dashboard by <b>Celine Nadeau</b> | 
            Source: <a href="https://www.trumpactiontracker.info/" target="_blank" style="color:inherit; text-decoration:underline;">Christina Pagel / Trump Action Tracker</a> | 
            <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" style="color:inherit; text-decoration:underline;">CC BY 4.0</a>
        </p>
    </div>
""", unsafe_allow_html=True)

# 7. SIDEBAR & SEARCH
if "search_term" not in st.session_state: st.session_state.search_term = ""
def sync_sidebar(): st.session_state.search_term = st.session_state.sidebar_search
def sync_vault(): st.session_state.search_term = st.session_state.vault_search

st.sidebar.title("🎛️ Data Controls")
st.sidebar.text_input("🔍 Search", key="sidebar_search", on_change=sync_sidebar, value=st.session_state.search_term)
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", key="comparison_mode")

if df is not None:
    min_date, max_date = df['Date'].min().to_pydatetime(), df['Date'].max().to_pydatetime()
    selected_range = st.sidebar.slider("Timeline Scrub", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="MMM DD")
    mask = (df['Date'] >= selected_range[0]) & (df['Date'] <= selected_range[1])
    if st.session_state.search_term:
        mask = mask & (df['Title'].str.contains(st.session_state.search_term, case=False, na=False))
    filtered_df = df.loc[mask]

    def reset_all():
        st.session_state.search_term = ""
        st.session_state.sidebar_search = ""
        st.session_state.vault_search = ""
        st.session_state.comparison_mode = False
    st.sidebar.button("🧹 Clear All Filters", on_click=reset_all, use_container_width=True)

# 8. HERO CARDS (DIAGNOSTIC CONTEXT)
if not filtered_df.empty:
    total_actions = len(filtered_df)
    days_active = max((selected_range[1] - selected_range[0]).days, 1)
    pace_per_month = (total_actions / days_active) * 30.44
    overlap = (len(filtered_df[filtered_df['Cat_Count'] > 1]) / total_actions * 100)

    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-card">
            <p style="margin:0; font-size:0.75rem; opacity:0.7; text-transform:uppercase;">Total Actions</p>
            <h2 style="margin:5px 0;">{total_actions}</h2>
            <p style="margin:0; font-size:0.65rem; opacity:0.6; font-style:italic;">Verifiable data (Doubt).</p>
        </div>
        <div class="hero-card" style="border-color: #DE0100; background: rgba(222, 1, 0, 0.05);">
            <p style="margin:0; font-size:0.75rem; color:#DE0100; text-transform:uppercase;">Velocity</p>
            <h2 style="margin:5px 0; color: #DE0100;">{pace_per_month:.1f}<span style="font-size: 0.9rem;">/mo</span></h2>
            <p style="margin:0; font-size:0.65rem; opacity:0.6; font-style:italic;">Institutional rewrite rate.</p>
        </div>
        <div class="hero-card">
            <p style="margin:0; font-size:0.75rem; opacity:0.7; text-transform:uppercase;">Strategic Overlap</p>
            <h2 style="margin:5px 0;">{overlap:.1f}%</h2>
            <p style="margin:0; font-size:0.65rem; opacity:0.6; font-style:italic;">Thematic strikes (Complexity).</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 9. STICKY NAV
st.markdown("""
    <div class="nav-container">
        <a href="#timeline"><button>Timeline</button></a>
        <a href="#themes"><button>Themes</button></a>
        <a href="#insights"><button>Insights</button></a>
        <a href="#words"><button>Words</button></a>
        <a href="#search"><button>Search</button></a>
    </div>
""", unsafe_allow_html=True)

# 10. TIMELINE (COMPACT TIPS)
st.markdown("<div id='timeline'></div>", unsafe_allow_html=True)
st.divider()
if not filtered_df.empty:
    chart_df = filtered_df.copy().sort_values('Date')
    chart_df['Cumulative'] = range(1, len(chart_df) + 1)
    line = alt.Chart(chart_df).mark_line(interpolate='step-after', color='#DE0100', strokeWidth=3).encode(
        x='Date:T', 
        y=alt.Y('Cumulative:Q', title="Actions"), 
        tooltip=['Date', 'Title']
    ).properties(width='container', height=400).interactive()
    st.altair_chart(line, use_container_width=True)
    
    st.markdown("""
    <div class="compact-tips">
        <p>💡 <b>Nav:</b> Hover for titles. Scroll/pinch to zoom.</p>
        <p>🔗 <b>Links:</b> Fallback to <b>Data Vault</b> if URLs are unstable.</p>
    </div>
    """, unsafe_allow_html=True)

# 11. THEMES & GLOSSARY
st.markdown("<div id='themes'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Action Volume by Theme")
if not filtered_df.empty:
    cat_counts = [{'Theme': short, 'Count': (filtered_df[long].str.strip().str.lower() == 'yes').sum()} for long, short in CATEGORY_MAP.items()]
    theme_bar = alt.Chart(pd.DataFrame(cat_counts)).mark_bar(color='#DE0100').encode(
        x=alt.X('Count:Q', title="Actions"), 
        y=alt.Y('Theme:N', sort='-x', title=None), 
        tooltip=['Theme', 'Count']
    ).properties(height=400).interactive()
    st.altair_chart(theme_bar, use_container_width=True)

    with st.expander("📖 Themes Glossary (Strategic Definitions)"):
        gloss_html = '<div style="font-size:0.8rem; opacity:0.8;"><table>'
        for _, row in GLOSSARY_DF.iterrows():
            gloss_html += f'<tr><td style="padding:5px; font-weight:bold; width:120px;">{row["Theme"]}</td><td style="padding:5px;">{row["Definition"]}</td></tr>'
        gloss_html += '</table></div>'
        st.markdown(gloss_html, unsafe_allow_html=True)

# 12. INSIGHTS (SATURATION ANALYSIS)
st.markdown("<div id='insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Strategic Diagnostic")
col_ins1, col_ins2 = st.columns(2)
with col_ins1:
    st.markdown("#### Saturation & Attrition")
    st.write(f"Moving at **{pace_per_month:.1f} actions/mo**, this volume induces 'procedural shock'—institutional rewrite outpaces judicial processing latency.")
with col_ins2:
    st.markdown("#### Norm-Collapse Loops")
    st.write(f"**Interconnectivity:** {overlap:.1f}% of events strike multiple democratic pillars simultaneously, bypassing single-domain resistance.")

st.markdown(f"""<div style="background: rgba(128, 128, 128, 0.05); border-left: 5px solid #DE0100; padding: 20px; border-radius: 5px; margin: 30px 0;"><p style="font-style: italic; margin-bottom: 5px;">"fools and fanatics are always so certain of themselves, and wiser people so full of doubts."</p><p style="text-align: right; font-weight: bold; margin: 0;">— Bertrand Russell</p></div>""", unsafe_allow_html=True)

# 13. WORD CLOUD (HSL NEON)
st.markdown("<div id='words'></div>", unsafe_allow_html=True)
st.divider()
if not filtered_df.empty:
    all_titles = " ".join(filtered_df['Title'].values).lower()
    words = re.findall(r'\w+', all_titles)
    filtered_words = [w for w in words if w not in {'the', 'and', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'up', 'about', 'into', 'over', 'after', 'trump', 'administration', 'order', 'federal', 'u.s.', 'president', 'will', 'this', 'that'} and len(w) > 3]
    word_counts = Counter(filtered_words).most_common(50)
    js_color = "function () { return 'hsl(' + (Math.random() * 360) + ', 100%, ' + (Math.round(Math.random() * 15) + 75) + '%)'; }"
    wc_options = {"backgroundColor": "transparent", "series": [{"type": "wordCloud", "gridSize": 15, "sizeRange": [16, 70], "rotationRange": [0,0], "textStyle": {"fontWeight": "bold", "color": js_color}, "data": [{"name": word, "value": count} for word, count in word_counts]}]}
    st_echarts(wc_options, height="450px")

# 14. VAULT
st.markdown("<div id='search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Data Vault")
st.text_input("Filter results...", key="vault_search", on_change=sync_vault, value=st.session_state.search_term)
if not filtered_df.empty:
    st.dataframe(filtered_df[['Date', 'Title', 'URL', 'Themes_List']].sort_values('Date', ascending=False), column_config={"URL": st.column_config.LinkColumn("Source"), "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")}, use_container_width=True, hide_index=True)
st.caption("Dashboard by Celine Nadeau. Last updated 03-03-2026. CC BY 4.0.")
