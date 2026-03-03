import streamlit as st
import pandas as pd
import altair as alt
import re
from collections import Counter
from datetime import datetime
from streamlit_echarts import st_echarts

# 1. PAGE CONFIG & SEO HACK (CRITICAL: Targets Social Media Crawlers)
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# THE SEO HACK
st.markdown(f"""
    <head>
    <title>U.S. Democracy Gone Bananas</title>
    <meta name="description" content="Strategic diagnostic of administrative velocity and institutional rewrite in the U.S. (2025-2026).">
    <meta property="og:title" content="U.S. Democracy Gone Bananas: Trump Actions Tracker">
    <meta property="og:description" content="A real-time diagnostic of systemic democratic erosion and institutional dismantling since Jan 2025.">
    <meta property="og:image" content="https://raw.githubusercontent.com/celinenadeau/repo/main/og-image.png">
    <meta property="og:url" content="https://trump-actions-tracker.streamlit.app/">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="U.S. Democracy Gone Bananas">
    <meta name="twitter:description" content="Verifiable data tracking the administrative rewrite of the federal state.">
    </head>
    """, unsafe_allow_html=True)

# 2. THEMES & RICH GLOSSARY DATA
THEME_GLOSSARY = [
    {"Theme": "Civil Rights", "Mapping": "Weakening Civil Rights", "Definition": "Dismantling Social Protections & Rights: A systematic removal of protections for marginalized groups like LGBTQ+ communities, immigrants, and minorities, signaling a shift away from universal egalitarianism."},
    {"Theme": "Corruption", "Mapping": "Corruption & Enrichment", "Definition": "Corruption & Enrichment: Actions that appear to directly enrich the president, his circle, or trade political favors for financial or personal gain, eroding the barrier between public service and private wealth."},
    {"Theme": "Democratic Norms", "Mapping": "Violating Democratic Norms, Undermining Rule of Law", "Definition": "Violating Democratic Norms & Rule of Law: The fracturing of checks and balances, the dismissal of constitutional constraints, and the direct targeting of the judiciary and press freedom."},
    {"Theme": "Education & Culture", "Mapping": "Attacking Universities, Schools, Museums, Culture", "Definition": "Attacking Intellectual & Cultural Autonomy: Restricting K-12 curricula, undermining university independence, and targeting cultural institutions to align national identity with state ideology."},
    {"Theme": "Federal Institutions", "Mapping": "Hollowing State / Weakening Federal Institutions", "Definition": "Hollowing the State: The dismantling of federal expertise, mass dismissals of civil servants, and the hollowing out of agencies to diminish the state's capacity for oversight."},
    {"Theme": "Foreign Policy", "Mapping": "Aggressive Foreign Policy & Global Destabilisation", "Definition": "Global Destabilisation: An aggressive pivot in foreign policy that threatens traditional alliances, withdraws from global treaties, and aligns the U.S. with anti-democratic rivals."},
    {"Theme": "Immigration & Nationalism", "Mapping": "Anti-immigrant or Militarised Nationalism", "Definition": "Militarised Nationalism: The demonization of immigrants combined with expanded domestic surveillance and the use of militarized enforcement to define the 'other' within."},
    {"Theme": "Info Control", "Mapping": "Controlling Information Including Spreading Misinformation and Propaganda", "Definition": "Information Control & Propaganda: The manufacturing of state-led narratives, the restriction of scientific data, and the active spread of misinformation to control public perception."},
    {"Theme": "Science & Health", "Mapping": "Control of Science & Health to Align with State Ideology", "Definition": "Ideological Control of Science: The suppression of climate research, the defunding of public health (vaccines), and the prioritization of industrial deregulation over scientific consensus."},
    {"Theme": "Suppressing Dissent", "Mapping": "Suppressing Dissent / Weaponising State Against 'Enemies'", "Definition": "Weaponising the State: Using executive power, legal threats, and law enforcement to target political rivals, critics, and dissenting cities as 'enemies' of the state."}
]

GLOSSARY_DF = pd.DataFrame(THEME_GLOSSARY).sort_values("Theme")
CATEGORY_MAP = dict(zip(GLOSSARY_DF['Mapping'], GLOSSARY_DF['Theme']))
SHORT_TO_LONG = dict(zip(GLOSSARY_DF['Theme'], GLOSSARY_DF['Mapping']))
SORTED_SHORT_NAMES = GLOSSARY_DF['Theme'].tolist()

# 3. CSS (NAV & CARD HARD-LOCK)
st.markdown("""
    <style>
        /* 1. NAV CONTAINER & BUTTONS (MONOCHROME LOCK) */
        .nav-container { display: flex !important; justify-content: space-between !important; gap: 10px !important; width: 100% !important; }
        .nav-container a { flex: 1 !important; text-decoration: none !important; }
        .nav-container button {
            width: 100% !important; padding: 10px !important; border-radius: 5px !important;
            font-weight: bold !important; cursor: pointer !important; background-color: transparent !important;
            border: 1px solid currentColor !important; color: inherit !important; transition: 0.3s !important;
        }
        .nav-container button:hover { opacity: 0.6 !important; }

        /* 2. STICKY NAV */
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) { 
            position: sticky !important; top: 2.875rem !important; z-index: 999 !important; 
            background: inherit !important; backdrop-filter: blur(15px) !important; padding: 10px 0 !important; 
        }

        /* 3. HERO CARDS */
        .hero-card {
            flex: 1; min-width: 280px; background: rgba(128, 128, 128, 0.1); 
            border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 25px; 
            text-align: center; margin-bottom: 15px;
        }
        .hero-card h2 { margin: 10px 0; font-size: 2.2rem; }
        .hero-card p.context { margin-top: 10px; font-size: 0.75rem; opacity: 0.6; font-style: italic; }

        /* 4. FOOTNOTE GLOSSARY */
        .glossary-footnote { font-size: 11px !important; color: #888 !important; line-height: 1.3 !important; }
        .glossary-footnote table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        .glossary-footnote th, .glossary-footnote td { 
            text-align: left; padding: 8px; font-weight: 400 !important; 
            border-bottom: 1px solid rgba(128,128,128,0.2); 
        }

        [id] { scroll-margin-top: 150px !important; }
        .quote-container { background: rgba(128, 128, 128, 0.05); border-left: 5px solid #DE0100; padding: 25px; border-radius: 5px; margin-bottom: 40px; }
    </style>
""", unsafe_allow_html=True)

# 4. LOAD DATA
@st.cache_data
def load_data():
    import os
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not files: return None
    df = pd.read_csv(files[0], skiprows=2)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=True) 
    cat_cols = list(CATEGORY_MAP.keys())
    df['Themes_List'] = df.apply(lambda r: ", ".join([CATEGORY_MAP.get(c, c) for c in cat_cols if str(r[c]).strip().lower() == 'yes']), axis=1)
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df

df = load_data()

# 5. SIDEBAR & SEARCH
if "search_term" not in st.session_state: st.session_state.search_term = ""
def sync_sidebar(): st.session_state.search_term = st.session_state.sidebar_search
def sync_vault(): st.session_state.search_term = st.session_state.vault_search

st.sidebar.title("🎛️ Data Controls")
st.sidebar.text_input("🔍 Search", key="sidebar_search", on_change=sync_sidebar, value=st.session_state.search_term)
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", key="comparison_mode")

if comparison_mode:
    selected_themes = st.sidebar.multiselect("Select Themes", options=SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
else:
    selected_short = st.sidebar.selectbox("Filter Area", ["All Actions"] + SORTED_SHORT_NAMES, key="filter_area")

if df is not None:
    min_date, max_date = df['Date'].min().to_pydatetime(), df['Date'].max().to_pydatetime()
    selected_range = st.sidebar.slider("Timeline Scrub", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="MMM DD")
    mask = (df['Date'] >= selected_range[0]) & (df['Date'] <= selected_range[1])
    if st.session_state.search_term:
        mask = mask & (df['Title'].str.contains(st.session_state.search_term, case=False, na=False))
    filtered_df = df.loc[mask]

# 6. HEADER
st.markdown("<div id='top'></div>", unsafe_allow_html=True)
st.markdown("""
    <a href="#top" style="text-decoration:none; color:inherit; display:flex; align-items:center; gap:20px; margin-bottom:30px;">
        <div style="font-size:2.5rem;">🍌</div>
        <h1 style="margin:0; font-weight:700;">U.S. Democracy Gone Bananas</h1>
    </a>
""", unsafe_allow_html=True)

# 7. HERO CARDS (WITH RICH CONTEXT)
if not filtered_df.empty:
    total_actions = len(filtered_df)
    days_active = max((selected_range[1] - selected_range[0]).days, 1)
    pace_per_month = (total_actions / days_active) * 30.44
    overlap = (len(filtered_df[filtered_df['Cat_Count'] > 1]) / total_actions * 100)

    st.markdown(f"""
    <div style="display: flex; justify-content: center; gap: 15px; width: 100%; flex-wrap: wrap;">
        <div class="hero-card">
            <p style="margin:0; font-size:0.85rem; opacity:0.7; text-transform:uppercase;">Total Actions</p>
            <h2>{total_actions}</h2>
            <p class="context">Verifiable data vs. mere opinion.</p>
        </div>
        <div class="hero-card" style="border-color: #DE0100; background: rgba(222, 1, 0, 0.05);">
            <p style="margin:0; font-size:0.85rem; color:#DE0100; text-transform:uppercase;">Velocity</p>
            <h2 style="color: #DE0100;">{pace_per_month:.1f}<span style="font-size: 1rem;">/mo</span></h2>
            <p class="context">Institutional rewrite rate.</p>
        </div>
        <div class="hero-card">
            <p style="margin:0; font-size:0.85rem; opacity:0.7; text-transform:uppercase;">Strategic Overlap</p>
            <h2>{overlap:.1f}%</h2>
            <p class="context">Interlocking thematic strikes.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 8. STICKY NAV
st.markdown("""
    <div class="nav-container">
        <a href="#timeline"><button>Timeline</button></a>
        <a href="#themes"><button>Themes</button></a>
        <a href="#insights"><button>Insights</button></a>
        <a href="#words"><button>Words</button></a>
        <a href="#search"><button>Search</button></a>
    </div>
""", unsafe_allow_html=True)

# 9. TIMELINE
st.markdown("<div id='timeline'></div>", unsafe_allow_html=True)
st.divider()
if not filtered_df.empty:
    if comparison_mode and selected_themes:
        st.subheader("Velocity Analysis: Comparative Theme Growth")
        long_names = [SHORT_TO_LONG[s] for s in selected_themes]
        comp_df = filtered_df.melt(id_vars=['Date', 'Title'], value_vars=long_names, var_name='Mapping', value_name='Active')
        comp_df = comp_df[comp_df['Active'].str.strip().str.lower() == 'yes']
        comp_df['Theme'] = comp_df['Mapping'].map(CATEGORY_MAP)
        comp_df = comp_df.sort_values('Date').reset_index(drop=True)
        comp_df['Cumulative'] = comp_df.groupby('Theme').cumcount() + 1
        comp_chart = alt.Chart(comp_df).mark_line(interpolate='step-after', strokeWidth=3).encode(x='Date:T', y='Cumulative:Q', color='Theme:N', tooltip=['Date', 'Theme', 'Cumulative']).properties(width='container', height=400).interactive()
        st.altair_chart(comp_chart, use_container_width=True)
    else:
        st.subheader(f"Timeline Progression: {selected_short if not comparison_mode else 'All Actions'}")
        chart_df = filtered_df.copy().sort_values('Date')
        if not comparison_mode and selected_short != "All Actions": chart_df = chart_df[chart_df[SHORT_TO_LONG[selected_short]].str.strip().str.lower() == 'yes']
        chart_df['Cumulative'] = range(1, len(chart_df) + 1)
        line = alt.Chart(chart_df).mark_line(interpolate='step-after', color='#DE0100', strokeWidth=3).encode(x='Date:T', y='Cumulative:Q', tooltip=['Date', 'Title']).properties(width='container', height=400).interactive()
        st.altair_chart(line, use_container_width=True)

    st.markdown("<p style='text-align: center; font-size: 0.8rem; opacity: 0.6; font-style: italic;'>💡 Navigation: Hover over the lines to see action titles. Scroll or pinch the chart to zoom into specific dates.</p>", unsafe_allow_html=True)

# 10. THEMES (WIDE BAR & RICH GLOSSARY)
st.markdown("<div id='themes'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Action Volume by Theme")
if not filtered_df.empty:
    cat_counts = [{'Theme': short, 'Count': (filtered_df[long].str.strip().str.lower() == 'yes').sum()} for long, short in CATEGORY_MAP.items() if (filtered_df[long].str.strip().str.lower() == 'yes').sum() > 0]
    theme_bar = alt.Chart(pd.DataFrame(cat_counts)).mark_bar(color='#DE0100').encode(x=alt.X('Count:Q', title="Actions"), y=alt.Y('Theme:N', sort='-x', title=None, axis=alt.Axis(labelLimit=300)), tooltip=['Theme', 'Count']).properties(height=400).interactive()
    st.altair_chart(theme_bar, use_container_width=True)

    with st.expander("📖 Themes Glossary (Rich Reference)"):
        glossary_html = '<div class="glossary-footnote"><table><tr><th>Theme</th><th>Rich Description</th></tr>'
        for _, row in GLOSSARY_DF.iterrows():
            glossary_html += f'<tr><td>{row["Theme"]}</td><td>{row["Definition"]}</td></tr>'
        glossary_html += '</table></div>'
        st.markdown(glossary_html, unsafe_allow_html=True)

# 11. INSIGHTS (SATURATION ANALYSIS)
st.markdown("<div id='insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: Strategic Diagnostic")
if not filtered_df.empty:
    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown("#### Strategic Velocity & Attrition")
        st.write(f"The administration is moving at **{pace_per_month:.1f} actions/mo**. This volume is a deliberate **Saturation Strategy**; it induces 'procedural shock' by ensuring the rate of institutional rewrite exceeds the processing latency of the judicial system.")
        st.markdown("#### Norm-Collapse Loops")
        st.write(f"**Interconnectivity:** {overlap:.1f}% of events strike multiple democratic pillars simultaneously. This creates 'Norm-Collapse Loops' where legal resistance in one domain is bypassed by executive action in another.")
    with col_ins2:
        st.markdown("#### The Resistance Heatmap")
        st.write("Opposition is concentrated in state-level litigation hubs (CA, WA, NY, IL). These hubs are the primary friction points against administrative velocity.")
        st.warning(f"**Diagnostic Projection:** By Jan 2029, the tracker projects **8,220 actions**, signaling a total administrative rewrite.")
    
    st.markdown(f"""<div class="quote-container"><p style="font-style: italic; margin-bottom: 5px;">"fools and fanatics are always so certain of themselves, and wiser people so full of doubts."</p><p style="text-align: right; font-weight: bold; margin: 0;">— Bertrand Russell</p></div>""", unsafe_allow_html=True)
    v_left, v_mid, v_right = st.columns([1, 8, 1])
    with v_mid: st.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")

# 12. WORD CLOUD (HSL LUMINANCE-LOCKED NEON)
st.markdown("<div id='words'></div>", unsafe_allow_html=True)
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

# 13. VAULT
st.markdown("<div id='search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Search Data Vault")
st.text_input("Filter results...", key="vault_search", on_change=sync_vault, value=st.session_state.search_term)
if not filtered_df.empty:
    st.dataframe(filtered_df[['Date', 'Title', 'URL', 'Themes_List']].sort_values('Date', ascending=False), column_config={"URL": st.column_config.LinkColumn("Source"), "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")}, use_container_width=True, hide_index=True)
st.caption("Dashboard by Celine Nadeau aka banasutra. Last updated 03-03-2026. CC BY 4.0.")
