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
            .hero-container, .nav-container, .intro-container {{ flex-direction: column !important; }}
            .hero-card, .intro-column {{ width: 100% !important; margin-bottom: 10px; }}
            .nav-container {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 15px; }}
            .nav-container button {{ width: 100%; padding: 6px 12px; border-radius: 5px; font-weight: bold; background: transparent; border: 1px solid currentColor; }}
        }}
        /* Refined Anchor Offsets */
        #top {{ scroll-margin-top: 100px; }}
        [id^="section-"] {{ scroll-margin-top: 120px !important; }}
        
        /* Layout Elements */
        .hero-container {{ 
            display: flex; 
            justify-content: space-between; 
            gap: 15px; 
            margin-bottom: 25px; 
            align-items: stretch;
        }}
        .hero-card {{ 
            flex: 1; 
            background: rgba(128, 128, 128, 0.1); 
            border: 1px solid rgba(128, 128, 128, 0.2); 
            border-radius: 12px; 
            padding: 20px; 
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.2s ease;
        }}
        .hero-card:hover {{
            border-color: rgba(128, 128, 128, 0.4);
            transform: translateY(-2px);
        }}
        
        /* Typography */
        .source-line {{
            font-size: 0.82rem;
            opacity: 0.8;
            margin: 20px 0 25px 0;
            padding-top: 12px;
            border-top: 1px solid rgba(128, 128, 128, 0.15);
            line-height: 1.4;
        }}
        
        .russell-quote {{
            font-size: 1.25rem;
            line-height: 1.4;
            max-width: 800px;
            margin: 22px 0 8px 0;
            padding-left: 18px;
            border-left: 3px solid rgba(128, 128, 128, 0.3);
            font-weight: 500;
            font-style: italic;
        }}
        .quote-author {{
            text-align: left;
            padding-left: 21px;
            font-size: 0.95rem;
            font-weight: bold;
            opacity: 0.8;
            margin-bottom: 20px;
        }}
        
        .intro-header {{
            font-size: 1.05rem;
            font-weight: bold;
            margin-bottom: 2px;
            opacity: 0.9;
        }}
        .intro-text {{
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
            opacity: 0.85;
            margin-bottom: 25px; /* Spacing with chart */
        }}
        
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

# 2. THEMES & DATA MAPPING
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

# 3. DATA ENGINE
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

# 4. SIDEBAR
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

# 5. HEADER SECTION
st.markdown("""
    <div style="text-align: left;">
        <h1 style="margin:0;">🍌 U.S. Democracy Gone Bananas</h1>
        <p style="font-weight: bold; font-size: 1.15rem; margin: 8px 0 0 0; opacity: 0.95;">
            An interactive diagnostic tool for curious, conscious, and caring humans—because facts sure trump opinions.
        </p>
        <div class="russell-quote">
            "The fundamental cause of the trouble is that in the modern world the stupid are cocksure while the intelligent are full of doubt."
        </div>
        <div class="quote-author">— Bertrand Russell</div>
    </div>
""", unsafe_allow_html=True)

if df is not None:
    f_df = df[(df['Date'] >= selected_range[0]) & (df['Date'] <= selected_range[1])]
    f_df = f_df[f_df['Title'].str.contains(st.session_state.q, case=False, na=False)]
    if not comp_mode and selected_pillar != "All Actions":
        f_df = f_df[f_df[SHORT_TO_LONG[selected_pillar]].str.strip().str.lower() == 'yes']

    pace = (len(f_df) / 400) * 30.44
    overlap = (len(f_df[f_df['Cat_Count'] > 1]) / len(f_df) * 100) if len(f_df) > 0 else 0
    
    # WHY & HOW COLUMNS
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="intro-header">Why use this tool?</p>', unsafe_allow_html=True)
        st.markdown('<p class="intro-text">Because democracy matters, and in a world of loud opinions, documentation is the antidote. Tracking the <b>Volume, Velocity, and Complexity</b> of current actions reveals the systematic dismantle of our state. Replace doubt with evidence and rhetoric with reality.</p>', unsafe_allow_html=True)
    with col2:
        st.markdown('<p class="intro-header">How to use this tool?</p>', unsafe_allow_html=True)
        st.markdown('<p class="intro-text">This dashboard is interactive; all metrics sync to your inputs. Use the <b>Sidebar</b> to search terms like "<b>Musk</b>" or "<b>Deportation</b>" and filter by <b>Pillar</b> to investigate specific threats and quantify the institutional footprint in real-time.</p>', unsafe_allow_html=True)

    # SOURCE LINE
    st.markdown("""
        <div class="source-line">
            <b>Source:</b> <a href="https://www.trumpactiontracker.info/" target="_blank" style="color:inherit; text-decoration: underline;">Trump Action Tracker</a> by Professor Christina Pagel | 
            <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" style="color:inherit; text-decoration: underline;">Creative Commons CC BY 4.0</a>
        </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.subheader("Institutional Health Diagnostic")
    st.markdown('<p class="intro-text"><b>Real-time indicators:</b> These metrics provide a high-level assessment of institutional health. By monitoring <b>Strategic Volume</b>, <b>Systemic Velocity</b>, and <b>Tactical Complexity</b>, we quantify administrative efforts to bypass traditional democratic guardrails.</p>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-card">
            <p style="margin:0; font-size:0.8rem; font-weight:bold; opacity:0.7;">STRATEGIC VOLUME</p>
            <h2 style="margin:10px 0;">{len(f_df)}</h2>
            <p style="margin:0; font-size:0.75rem; opacity:0.9; line-height:1.4;">
                <b>Institutional Footprint:</b> Total recorded strikes. Every action represents a structural rewrite of the American state.
            </p>
        </div>
        <div class="hero-card">
            <p style="margin:0; font-size:0.8rem; font-weight:bold; opacity:0.7;">SYSTEMIC VELOCITY</p>
            <h2 style="margin:10px 0;">{pace:.1f}/mo</h2>
            <p style="margin:0; font-size:0.75rem; opacity:0.9; line-height:1.4;">
                <b>Saturation Strategy:</b> The speed is the point. High-frequency actions are designed to outpace judicial oversight.
            </p>
        </div>
        <div class="hero-card">
            <p style="margin:0; font-size:0.8rem; font-weight:bold; opacity:0.7;">TACTICAL COMPLEXITY</p>
            <h2 style="margin:10px 0;">{overlap:.1f}%</h2>
            <p style="margin:0; font-size:0.75rem; opacity:0.9; line-height:1.4;">
                <b>Interlocking Strategy:</b> The overlap is the point. Multi-pillar strikes ensure results even if one is blocked.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 7. TIMELINE OF ACTIONS
st.markdown("<div id='section-timeline'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Timeline of Actions")
st.markdown('<p class="intro-text"><b>Visualizing momentum:</b> This graph tracks the cumulative progression of actions over time. Use search and filters to identify "spikes" in activity—periods where the velocity of the institutional rewrite intensified. Use the Comparison Mode in the sidebar to contrast specific thematic velocities.</p>', unsafe_allow_html=True)

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
    st.caption("💡 On desktop, hover any data point to view the specific action and its source.")
st.markdown(back_to_top, unsafe_allow_html=True)

# 8. VOLUME BY THEME
st.markdown("<div id='section-themes'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Volume by Theme")
st.markdown('<p class="intro-text"><b>Mapping the targets:</b> This breakdown reveals which democratic pillars are under the heaviest stress. It helps isolate the administration\'s primary strategic focus.</p>', unsafe_allow_html=True)

if not f_df.empty:
    cat_counts = [{'Theme': short, 'Count': (f_df[long].str.strip().str.lower() == 'yes').sum()} for long, short in CATEGORY_MAP.items()]
    theme_bar = alt.Chart(pd.DataFrame(cat_counts)).mark_bar(color='#DE0100').encode(x=alt.X('Count:Q', title="Actions"), y=alt.Y('Theme:N', sort='-x', title=None), tooltip=['Theme', 'Count']).properties(height=400).interactive()
    st.altair_chart(theme_bar, use_container_width=True)
    st.caption("💡 Use search and/or filter to investigate overlaps and hover over the bars to see exact counts.")

    with st.expander("📖 Strategic Themes Glossary"):
        gloss_html = '<div style="font-size:0.85rem; opacity:0.9;"><table>'
        for _, row in GLOSSARY_DF.iterrows():
            gloss_html += f'<tr><td style="padding:8px; font-weight:bold; width:140px; border-bottom:1px solid rgba(128,128,128,0.2);">{row["Theme"]}</td><td style="padding:8px; border-bottom:1px solid rgba(128,128,128,0.2);">{row["Definition"]}</td></tr>'
        gloss_html += '</table></div>'
        st.markdown(gloss_html, unsafe_allow_html=True)
st.markdown(back_to_top, unsafe_allow_html=True)

# 9. STRATEGIC ANALYSIS
st.markdown("<div id='section-insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Strategic Analysis")
st.markdown('<p class="intro-text"><b>Diagnostic findings:</b> Beyond the raw numbers, these insights explain the methodology of the dismantle. This section identifies patterns like <b>Saturation</b> and <b>Interlocking Strikes</b>.</p>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("#### Saturation Strategy & Attrition")
    st.write("Ensuring the rate of institutional rewrite outpaces judicial processing latency induces 'procedural shock.'")
    st.markdown("#### Resistance Heatmap")
    st.write("Opposition friction is concentrated in state-level litigation hubs (CA, NY, WA).")
with c2:
    st.markdown("#### Norm-Collapse Loops")
    st.write("Interlocking thematic strikes hit multiple pillars simultaneously.")
    st.warning("**Diagnostic Projection:** Current trends suggest total institutional dismantle prior to 2028.")

v_l, v_c, v_r = st.columns([1, 8, 1]); v_c.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")
st.markdown(back_to_top, unsafe_allow_html=True)

# 10. DATA SEARCH
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Data Search")
st.markdown('<p class="intro-text"><b>Granular evidence:</b> The complete repository of verifiable data. Use the search bar below to find specific keywords, people, or policies.</p>', unsafe_allow_html=True)

st.text_input("Synchronized Filter", key="vault_q", on_change=sync_v, value=st.session_state.q)
st.dataframe(f_df[['Date', 'Title', 'URL', 'Themes_List']].sort_values('Date', ascending=False), column_config={"URL": st.column_config.LinkColumn("Source")}, use_container_width=True, hide_index=True)
st.markdown(back_to_top, unsafe_allow_html=True)

# 11. FOOTER
st.divider()
st.caption("Dashboard by Celine Nadeau aka bananasutra. Last updated 03-03-2026. CC BY 4.0.")
