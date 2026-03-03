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
    <meta name="description" content="Strategic diagnostic of authoritarian velocity and institutional rewrite (2025-2026).">
    <style>
        @media (max-width: 768px) {{
            .hero-container, .nav-container {{ flex-direction: column !important; }}
            .hero-card {{ width: 100% !important; margin-bottom: 10px; }}
            .nav-container {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 15px; }}
            .nav-container button {{ width: 100%; padding: 6px 12px; border-radius: 5px; font-weight: bold; background: transparent; border: 1px solid currentColor; }}
        }}
        /* Refined Anchor Offsets */
        #top {{ scroll-margin-top: 100px; }}
        [id^="section-"] {{ scroll-margin-top: 120px !important; }}
        
        .hero-container {{ display: flex; justify-content: space-between; gap: 15px; margin-bottom: 25px; }}
        .hero-card {{ flex: 1; background: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 20px; text-align: center; }}
        .nav-container {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 15px; }}
        .nav-container button {{ width: 100%; padding: 6px 12px; border-radius: 5px; font-weight: bold; background: transparent; border: 1px solid currentColor; }}
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) {{ 
            position: sticky !important; top: 2.875rem !important; z-index: 999 !important; 
            background: inherit !important; backdrop-filter: blur(15px) !important; padding: 5px 0 !important; 
        }}
        .back-to-top {{ text-align: right; font-size: 0.75rem; opacity: 0.6; }}
        .back-to-top a {{ color: inherit; text-decoration: none; }}
    </style>
    </head>
    <div id="top"></div>
    """, unsafe_allow_html=True)

# Helper for the back-to-top link
back_to_top = '<div class="back-to-top"><a href="#top">⌃ back to top</a></div>'

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

# 4. DATA CONTROL SIDEBAR
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

# 5. HEADER & HERO BOXES
st.markdown("""<div style="text-align: left;"><h1 style="margin:0;">🍌 U.S. Democracy Gone Bananas</h1>
<p style="opacity:0.8; margin:10;">Documenting the actions, statements, and plans of President Trump and his administration that echo those of authoritarian regimes and may pose a threat to American democracy, since January 2025.</p>
<p style="font-size:0.8rem; opacity:0.6; margin:10;">Source: <a href="https://www.trumpactiontracker.info/" target="_blank" style="color:inherit;">Trump Action Tracker</a> by <a href="https://www.trumpactiontracker.info/about" target="_blank" style="color:inherit;">Professor Christina Pagel</a> | <a href="https://creativecommons.org/" target="_blank" style="color:inherit;" rel="noopener noreferrer">Creative Commons License</a></p></div>""", unsafe_allow_html=True)
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

# 7. TIMELINE & THEMES GRAPHS
st.markdown("<div id='section-timeline'></div>", unsafe_allow_html=True)
st.subheader("Action Progression")
if not f_df.empty:
    if comp_mode:
        long_names = [SHORT_TO_LONG[s] for s in selected_themes]
        comp_plot_df = f_df.melt(id_vars=['Date', 'Title', 'URL', 'Themes_List'], value_vars=long_names, var_name='Mapping', value_name='Active')
        comp_plot_df = comp_plot_df[comp_plot_df['Active'].str.strip().str.lower() == 'yes']
        comp_plot_df['Theme'] = comp_plot_df['Mapping'].map(CATEGORY_MAP)
        comp_plot_df['Cumulative'] = comp_plot_df.groupby('Theme').cumcount() + 1
        
        chart = alt.Chart(comp_plot_df).mark_line(interpolate='step-after', strokeWidth=3).encode(
            x='Date:T', y='Cumulative:Q', color='Theme:N', href='URL:N',
            tooltip=['Date:T', 'Title:N', 'Theme:N', 'Cumulative:Q']
        ).properties(width='container', height=400).interactive()
    else:
        chart_df = f_df.copy().sort_values('Date')
        chart_df['Cumulative'] = range(1, len(chart_df) + 1)
        chart = alt.Chart(chart_df).mark_line(interpolate='step-after', color='#DE0100', strokeWidth=3).encode(
            x='Date:T', y='Cumulative:Q', href='URL:N',
            tooltip=[alt.Tooltip('Date:T', format='%Y-%m-%d'), alt.Tooltip('Title:N', title='Action'), alt.Tooltip('Themes_List:N', title='Themes Hit'), alt.Tooltip('URL:N', title='Source URL')]
        ).properties(width='container', height=400).interactive()
    st.altair_chart(chart, use_container_width=True)
    st.markdown("<p style='font-size:0.75rem; opacity:0.6; font-style:italic; margin-top:-20px;'>💡 Hover for diagnostic data. Click points for source URL. Scroll/pinch to zoom.</p>", unsafe_allow_html=True)
st.markdown(back_to_top, unsafe_allow_html=True)

st.markdown("<div id='section-themes'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Trump Actions: Volume by Pillar")
if not f_df.empty:
    cat_counts = [{'Theme': short, 'Count': (f_df[long].str.strip().str.lower() == 'yes').sum()} for long, short in CATEGORY_MAP.items()]
    theme_bar = alt.Chart(pd.DataFrame(cat_counts)).mark_bar(color='#DE0100').encode(x=alt.X('Count:Q', title="Actions"), y=alt.Y('Theme:N', sort='-x', title=None), tooltip=['Theme', 'Count']).properties(height=400).interactive()
    st.altair_chart(theme_bar, use_container_width=True)

    with st.expander("📖 Strategic Themes Glossary"):
        gloss_html = '<div style="font-size:0.85rem; opacity:0.9;"><table>'
        for _, row in GLOSSARY_DF.iterrows():
            gloss_html += f'<tr><td style="padding:8px; font-weight:bold; width:140px; border-bottom:1px solid rgba(128,128,128,0.2);">{row["Theme"]}</td><td style="padding:8px; border-bottom:1px solid rgba(128,128,128,0.2);">{row["Definition"]}</td></tr>'
        gloss_html += '</table></div>'
        st.markdown(gloss_html, unsafe_allow_html=True)
st.markdown(back_to_top, unsafe_allow_html=True)

# 8. DEEP INSIGHTS 
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
st.markdown(back_to_top, unsafe_allow_html=True)

# 10. VAULT SEARCH 
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Search Trump Actions Data Vault")
st.text_input("Synchronized Filter", key="vault_q", on_change=sync_v, value=st.session_state.q)
st.dataframe(f_df[['Date', 'Title', 'URL', 'Themes_List']].sort_values('Date', ascending=False), column_config={"URL": st.column_config.LinkColumn("Source")}, use_container_width=True, hide_index=True)
st.markdown(back_to_top, unsafe_allow_html=True)

# 11. FOOTER
st.divider()
st.caption("Dashboard by Celine Nadeau aka bananasutra. Last updated 03-03-2026. CC BY 4.0.")
