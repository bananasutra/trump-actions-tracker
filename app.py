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
            .hero-container, .nav-container, .intro-container, .analysis-grid {{ flex-direction: column !important; }}
            .hero-card, .intro-column, .analysis-column {{ width: 100% !important; margin-bottom: 10px; }}
            .nav-container {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 15px; }}
            .nav-container button {{ width: 100%; padding: 6px 12px; border-radius: 5px; font-weight: bold; background: transparent; border: 1px solid currentColor; }}
        }}
        /* Refined Anchor Offsets */
        #top {{ scroll-margin-top: 100px; }}
        [id^="section-"] {{ scroll-margin-top: 120px !important; }}
        
        /* Sidebar UX Fixes */
        [data-testid="stSidebarNav"] {{ display: none; }}
        [data-testid="collapsedControl"] {{
            background-color: #DE0100 !important;
            color: white !important;
            border-radius: 0 5px 5px 0 !important;
            width: 40px !important;
            height: 40px !important;
            left: 0 !important;
            top: 10px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        /* Sidebar spacing & legibility */
        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 1.5rem !important;
        }}
        [data-testid="stSidebar"] label {{
            font-size: 0.85rem !important;
            line-height: 1.2 !important;
        }}
        
        /* Layout Elements */
        .hero-container {{ display: flex; justify-content: space-between; gap: 15px; margin-bottom: 25px; align-items: stretch; }}
        .hero-card {{ flex: 1; background: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 20px; text-align: center; }}
        
        /* Analysis Layout & Semantic Hierarchy */
        .analysis-grid {{ display: flex; gap: 40px; margin-bottom: 30px; }}
        .analysis-column {{ flex: 1; }}
        .analysis-card {{ margin-bottom: 25px; }}
        
        h2 {{ font-size: 1.75rem !important; font-weight: bold !important; margin-top: 10px !important; }}
        h3 {{ font-size: 1.5rem !important; font-weight: bold !important; margin-bottom: 20px !important; opacity: 0.95; border-bottom: 1px solid rgba(128,128,128,0.3); padding-bottom: 10px; }}
        h4 {{ font-size: 1.1rem !important; font-weight: bold !important; margin-bottom: 8px !important; color: inherit !important; }}
        
        /* Typography */
        .source-line {{ font-size: 0.85rem; opacity: 0.85; margin: 25px 0 25px 0; padding-top: 15px; border-top: 1px solid rgba(128, 128, 128, 0.2); line-height: 1.5; }}
        .russell-quote {{ font-size: 1.3rem; line-height: 1.5; max-width: 850px; margin: 35px 0 12px 0; padding-left: 20px; border-left: 4px solid rgba(128, 128, 128, 0.3); font-weight: 500; font-style: italic; }}
        .quote-author {{ text-align: left; padding-left: 24px; font-size: 1rem; font-weight: bold; opacity: 0.8; margin-bottom: 35px; }}
        .intro-text {{ font-size: 0.95rem !important; line-height: 1.6 !important; opacity: 0.85; margin-bottom: 25px; }}
        
        .analysis-bullet {{ font-size: 0.88rem; line-height: 1.5; margin-bottom: 10px; opacity: 0.9; }}
        .projection-block {{ background: rgba(222, 1, 0, 0.05); padding: 25px; border-left: 5px solid #DE0100; border-radius: 4px; margin-top: 25px; }}

        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) {{ 
            position: sticky !important; top: 2.875rem !important; z-index: 999 !important; 
            background: inherit !important; backdrop-filter: blur(15px) !important; padding: 5px 0 !important; 
        }}
        .back-to-top {{ text-align: right; font-size: 0.75rem; opacity: 0.6; }}
    </style>
    </head>
    <div id="top"></div>
    """, unsafe_allow_html=True)

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
    if not files:
        return None
    df = pd.read_csv(files[0], skiprows=2)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Themes_List'] = df.apply(
        lambda r: ", ".join(
            [CATEGORY_MAP[c] for c in CATEGORY_MAP if str(r[c]).strip().lower() == 'yes']
        ),
        axis=1,
    )
    df['Cat_Count'] = df[list(CATEGORY_MAP.keys())].apply(
        lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1
    )
    return df.sort_values('Date')

with st.spinner("Retrieving data..."):
    df = get_data()

if df is None:
    st.error("⚠️ CRITICAL: Data engine failed to locate the CSV file.")
    st.info(
        "Ensure your data file (e.g., 'trump-actions-3-1-26.csv') "
        "is in the main folder of your GitHub repository."
    )
    st.stop()

# 4. HARMONIZED SIDEBAR
st.sidebar.title("🎛️ Data Controls")
st.sidebar.divider()
comp_mode = st.sidebar.toggle("📊 Comparison Mode", key="comp_mode")
st.sidebar.divider()

if df is not None:
    min_date, max_date = df['Date'].min().to_pydatetime(), df['Date'].max().to_pydatetime()
    selected_range = st.sidebar.slider(
        "Filter by Date",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        key="date_range",
    )
    st.sidebar.divider()
    
    if comp_mode:
        selected_themes = st.sidebar.multiselect(
            "Filter by Theme",
            options=SORTED_SHORT_NAMES,
            default=SORTED_SHORT_NAMES,
            key="theme_multi",
        )
    else:
        selected_pillar = st.sidebar.selectbox(
            "Filter by Theme",
            ["All Actions"] + SORTED_SHORT_NAMES,
            key="theme_select",
        )
    st.sidebar.divider()

    st.sidebar.text_input("Filter by Keyword", key="side_q", on_change=sync_s, value=st.session_state.q)
    st.sidebar.divider()
    
    def reset_all():
        st.session_state.q = ""
        st.session_state.comp_mode = False
        st.session_state.side_q = ""
        st.session_state.vault_q = ""
        if "date_range" in st.session_state:
            st.session_state.date_range = (min_date, max_date)
        if "theme_select" in st.session_state:
            st.session_state.theme_select = "All Actions"
        if "theme_multi" in st.session_state:
            st.session_state.theme_multi = SORTED_SHORT_NAMES
    st.sidebar.button("Sweep All Filters", on_click=reset_all, use_container_width=True)

# 5. HEADER SECTION
st.markdown("""
    <div style="text-align: left;">
        <h1 style="margin:0;">🍌 U.S. Democracy Gone Bananas</h1>
        <p style="font-weight: bold; font-size: 1.15rem; margin: 8px 0 4px 0; opacity: 0.95;">
            An interactive diagnostic tool for curious, conscious, and caring humans—because facts sure trump opinions.
        </p>
        <p style="font-size: 0.9rem; opacity: 0.8; margin: 4px 0 0 0;">
            “The fundamental cause of the trouble is that in the modern world the stupid are cocksure while the intelligent are full of doubt.”
            <span style="font-weight:bold;">— Bertrand Russell</span>
        </p>
    </div>
""", unsafe_allow_html=True)

if df is not None:
    f_df = df[(df['Date'] >= selected_range[0]) & (df['Date'] <= selected_range[1])]
    f_df = f_df[f_df['Title'].str.contains(st.session_state.q, case=False, na=False)]
    if not comp_mode and selected_pillar != "All Actions":
        f_df = f_df[f_df[SHORT_TO_LONG[selected_pillar]].str.strip().str.lower() == 'yes']

    pace = (len(f_df) / 400) * 30.44
    overlap = (len(f_df[f_df['Cat_Count'] > 1]) / len(f_df) * 100) if len(f_df) > 0 else 0

    # Full dataset range for clarity (Tier 1)
    data_start = df['Date'].min().strftime('%b %d, %Y')
    data_end = df['Date'].max().strftime('%b %d, %Y')
    data_range_str = f"{data_start} – {data_end}"

    # Compact always-visible copy; move HOW/WHY depth into an expander
    with st.expander("How and why to use this tool", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<p class="intro-header">Why use this tool?</p>', unsafe_allow_html=True)
            st.markdown('<p class="intro-text">Because democracy matters, and in a world of loud opinions, documentation is the antidote. Tracking the <b>Volume, Velocity, and Complexity</b> of current actions reveals the systematic dismantle of our state. Replace doubt with evidence and rhetoric with reality.</p>', unsafe_allow_html=True)
        with col2:
            st.markdown('<p class="intro-header">How to use this tool?</p>', unsafe_allow_html=True)
            st.markdown('<p class="intro-text">This dashboard is interactive; all metrics sync to your inputs. Use the <b>Sidebar</b> to search terms like "<b>Musk</b>" or "<b>Deportation</b>" and filter by <b>Pillar</b> to investigate specific threats and quantify the institutional footprint in real-time.</p>', unsafe_allow_html=True)

    st.markdown(f"""
        <div class="source-line">
            <b>Source:</b> <a href="https://www.trumpactiontracker.info/" target="_blank" style="color:inherit; text-decoration: underline;">Trump Action Tracker</a> by Professor Christina Pagel | 
            <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" style="color:inherit; text-decoration: underline;">Creative Commons CC BY 4.0</a> | 
            <b>Data range:</b> {data_range_str}
        </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("<h2>Institutional Health Diagnostic</h2>", unsafe_allow_html=True)
    # Dynamic narrative (Tier 2): updates with filters
    range_start = selected_range[0].strftime('%b %d, %Y')
    range_end = selected_range[1].strftime('%b %d, %Y')
    top_themes = sorted(
        [(short, (f_df[long].str.strip().str.lower() == 'yes').sum()) for long, short in CATEGORY_MAP.items()],
        key=lambda x: -x[1]
    )[:2]
    top_line = ", ".join(f"{name} ({count})" for name, count in top_themes if count > 0) or "—"
    st.markdown(
        f'<p class="intro-text"><b>In this view:</b> From {range_start} to {range_end}, you\'re viewing '
        f'<b>{len(f_df)}</b> actions at <b>{pace:.1f}/mo</b>, with <b>{overlap:.1f}%</b> touching multiple themes. '
        f'Top themes: {top_line}.</p>',
        unsafe_allow_html=True
    )
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
st.markdown("<h2>Timeline of Actions</h2>", unsafe_allow_html=True)
# Dynamic line above chart: reflects date range, keyword, and theme filters
kw = (st.session_state.q or "").strip()
range_start_tl = selected_range[0].strftime('%b %d, %Y')
range_end_tl = selected_range[1].strftime('%b %d, %Y')
theme_note = "" if (comp_mode or selected_pillar == "All Actions") else f" in <b>{selected_pillar}</b>"
if kw:
    timeline_intro = (
        f'<p class="intro-text"><b>In this view:</b> From {range_start_tl} to {range_end_tl}, '
        f'showing <b>{len(f_df)}</b> actions matching "<b>{kw}</b>"{theme_note}.</p>'
    )
else:
    timeline_intro = (
        f'<p class="intro-text"><b>In this view:</b> From {range_start_tl} to {range_end_tl}, '
        f'showing <b>{len(f_df)}</b> actions{theme_note}.</p>'
    )
st.markdown(timeline_intro, unsafe_allow_html=True)
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
st.markdown("<h2>Volume by Theme</h2>", unsafe_allow_html=True)
theme_filter_note = "" if (comp_mode or selected_pillar == "All Actions") else f" within <b>{selected_pillar}</b>"
if kw:
    volume_intro_dynamic = (
        f'<p class="intro-text"><b>Mapping the targets:</b> In this filtered view, '
        f'<b>{len(f_df)}</b> actions matching "<b>{kw}</b>"{theme_filter_note} '
        'concentrate pressure across the themes below.</p>'
    )
else:
    volume_intro_dynamic = (
        f'<p class="intro-text"><b>Mapping the targets:</b> This breakdown reveals which democratic pillars are '
        f'under the heaviest stress{theme_filter_note}. It helps isolate the administration\'s primary strategic focus.</p>'
    )
st.markdown(volume_intro_dynamic, unsafe_allow_html=True)

if not f_df.empty:
    cat_counts = [{'Theme': short, 'Count': (f_df[long].str.strip().str.lower() == 'yes').sum()} for long, short in CATEGORY_MAP.items()]
    theme_bar = alt.Chart(pd.DataFrame(cat_counts)).mark_bar(color='#DE0100').encode(
        x=alt.X('Count:Q', title="Actions"), 
        y=alt.Y('Theme:N', sort='-x', title=None, axis=alt.Axis(labelLimit=300, labelPadding=10)), 
        tooltip=['Theme', 'Count']
    ).properties(height=400).configure_view(stroke=None).interactive()
    
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
st.markdown("<h2>Strategic Analysis</h2>", unsafe_allow_html=True)
st.markdown('<p class="intro-text">Institutional rehearsal for a total state rewrite is no longer a risk—it is a documented fact. Headlines that speak of "sliding" or "risks" are beyond euphemisms; they are forms of dangerous denial. Quantifiable data is the only tool that moves past the noise of daily outrage to confront the structural dismantling of democracy.</p>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
        <h3>Critical Risks</h3>
        <div class="analysis-card">
            <h4>1. Volume & Velocity: Saturation Strategy</h4>
            <p class="analysis-bullet"><b>The Risk:</b> High-velocity actions induce "procedural shock" by overwhelming oversight capacity. The state ensures institution rewrite outpaces legal response, making damage permanent before review begins.</p>
            <p class="analysis-bullet"><b>The Framework:</b> <i>Bertrand Russell</i> warned that democracy requires the courage to demand evidence; saturation exhausts that courage through sheer overwhelming mass.</p>
            <p class="analysis-bullet" style="font-size:0.8rem; opacity:0.7;"><i>Example: Simultaneous Inspector General purges alongside the removal of job protections for thousands of career civil servants.</i></p>
        </div>
        <div class="analysis-card">
            <h4>2. Complexity: Norm-Collapse Loops</h4>
            <p class="analysis-bullet"><b>The Risk:</b> Complexity is weaponized via "interlocking strikes." By hitting multiple domains simultaneously, the state ensures the objective is met even if a court blocks one specific channel.</p>
            <p class="analysis-bullet"><b>The Framework:</b> <i>Umberto Eco</i> identified that autocracy relies on "Newspeak"—a restricted vocabulary that prevents critical thought and creates a new reality where dissent is chilled.</p>
            <p class="analysis-bullet" style="font-size:0.8rem; opacity:0.7;"><i>Example: Coordinated assaults on universities using funding freezes, visa revocations, and civil rights probes.</i></p>
        </div>
        <div class="analysis-card">
            <h4>3. Apathy: The Erosion of Accountability</h4>
            <p class="analysis-bullet"><b>The Risk:</b> Normalization is the final stage of dismantle. When outrage fatigue leads to apathy, the state is freed from the burden of justification, turning unchecked power into the new institutional baseline.</p>
            <p class="analysis-bullet"><b>The Framework:</b> <i>Hannah Arendt</i> warned that the danger to democracy is not just active malice, but the "banality" of those who stop questioning the systematic erosion of truth.</p>
            <p class="analysis-bullet" style="font-size:0.8rem; opacity:0.7;"><i>Example: The public transition from questioning state motives to accepting them as "just the way things are."</i></p>
        </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown("""
        <h3>Actionable Paths</h3>
        <div class="analysis-card">
            <h4>1. Break the Silence of Enablers</h4>
            <p class="analysis-bullet"><b>The Strategy:</b> Autocracy requires the collaboration of elites. <i>Robert Paxton</i> emphasizes that fascism thrives on the willing cooperation of those who share power to suppress opposition.</p>
            <p class="analysis-bullet"><b>The Action:</b> Apply relentless social and financial pressure on the corporations, law firms, and tech firms actively profiting from the surveillance and deportation apparatus.</p>
            <p class="analysis-bullet" style="font-size:0.8rem; opacity:0.7;"><i>Example: Publicly targeting stakeholders and municipal contracts of private entities enmeshed in the rewrite.</i></p>
        </div>
        <div class="analysis-card">
            <h4>2. Document Reality Daily</h4>
            <p class="analysis-bullet"><b>The Strategy:</b> In a "post-truth" era, documentation is a vital act of resistance. Refuse to adopt dehumanizing "Newspeak." <i>Do not obey in advance.</i></p>
            <p class="analysis-bullet"><b>The Action:</b> Aggressively share authoritative data projects. Confront disinformation with irrefutable evidence. Do not let rhetoric replace institutional reality.</p>
            <p class="analysis-bullet" style="font-size:0.8rem; opacity:0.7;"><i>Example: Actively distributing verified trackers to local networks and archiving state deletions of public data.</i></p>
        </div>
        <div class="analysis-card">
            <h4>3. Choose Courage Over Comfort</h4>
            <p class="analysis-bullet"><b>The Strategy:</b> True knowledge requires bravery. Banasutra philosophy holds that radical empathy and kindness are the ultimate defiance against a system built on cruelty.</p>
            <p class="analysis-bullet"><b>The Action:</b> Practice emotional courage. Question authority relentlessly, protect the marginalized in your community, and recognize kindness as a tactical guardrail.</p>
            <p class="analysis-bullet" style="font-size:0.8rem; opacity:0.7;"><i>Example: Establishing community-led mutual aid and protective networks for those targeted by systemic purges.</i></p>
        </div>
    """, unsafe_allow_html=True)

# FULL WIDTH DIAGNOSTIC PROJECTION
st.markdown("""
    <div class="projection-block">
        <p style="font-weight:bold; color:#DE0100; margin-bottom:8px; font-size:1.1rem;">Diagnostic Projection</p>
        <p class="analysis-bullet" style="font-size:0.95rem;">Current trends suggest a total institutional dismantle prior to the 2028 electoral cycle. The manipulation of emergency powers and defunding of independent media are systemically removing the guardrails required for free and fair elections. As <i>Timothy Snyder</i> warns: <b>Institutions do not protect themselves.</b></p>
    </div>
""", unsafe_allow_html=True)

st.markdown(back_to_top, unsafe_allow_html=True)

# 10. DATA SEARCH
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
st.divider()
st.markdown("<h2>Data Search</h2>", unsafe_allow_html=True)
kw_search = (st.session_state.q or "").strip()
if kw_search:
    st.markdown(
        f'<p class="intro-text"><b>Granular evidence:</b> Showing '
        f'<b>{len(f_df)}</b> records matching "<b>{kw_search}</b>". '
        'Use the search bar below to find specific keywords, people, or policies.</p>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<p class="intro-text"><b>Granular evidence:</b> The complete repository of verifiable data. '
        'Use the search bar below to find specific keywords, people, or policies.</p>',
        unsafe_allow_html=True,
    )

st.text_input("Synchronized Filter", key="vault_q", on_change=sync_v, value=st.session_state.q)
st.dataframe(
    f_df[['Date', 'Title', 'URL', 'Themes_List']].sort_values('Date', ascending=False),
    column_config={"URL": st.column_config.LinkColumn("Source")},
    use_container_width=True,
    hide_index=True,
)
st.markdown(back_to_top, unsafe_allow_html=True)

# 11. FOOTER
st.divider()
st.caption("Dashboard by Celine Nadeau aka bananasutra. Last updated 03-03-2026. CC BY 4.0. Data: " + data_range_str + ".")
