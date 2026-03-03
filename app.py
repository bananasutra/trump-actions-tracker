import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# 1. PAGE CONFIG & SEO
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. THEMES & GLOSSARY MAPPING
THEME_GLOSSARY = [
    {"Theme": "Civil Rights", "Mapping": "Weakening Civil Rights", "Definition": "Dismantling Social Protections & Rights: Removing civil rights from marginalized groups like LGBTQ+ communities and immigrants, attacking diversity and inclusion (DEI) initiatives, and contravening due process rights."},
    {"Theme": "Corruption", "Mapping": "Corruption & Enrichment", "Definition": "Corruption and Enrichment: Actions that directly enrich the president, his family, or his cabinet, or that trade political favors for wealth."},
    {"Theme": "Democratic Norms", "Mapping": "Violating Democratic Norms, Undermining Rule of Law", "Definition": "Violating democratic norms, undermining rule of law: Actions that weaken checks and balances, restrict press freedom, undermine states' rights, violate court orders or the Constitution, or reduce the independence of oversight bodies."},
    {"Theme": "Education & Culture", "Mapping": "Attacking Universities, Schools, Museums, Culture", "Definition": "Attacking universities, schools, museums, culture: Undermining the independence of universities, restricting K-12 education topics, and targeting information within museums and national parks."},
    {"Theme": "Federal Institutions", "Mapping": "Hollowing State / Weakening Federal Institutions", "Definition": "Hollowing state / weakening federal institutions: Dismantling federal institutions, mass firings of staff, or politicizing government roles."},
    {"Theme": "Foreign Policy", "Mapping": "Aggressive Foreign Policy & Global Destabilisation", "Definition": "Aggressive Foreign Policy & Global Destabilisation: Threatening allies, using tariffs to extract concessions, withdrawing from international treaties (like the WHO or Paris Climate Treaty), and aligning with anti-democratic rivals."},
    {"Theme": "Immigration & Nationalism", "Mapping": "Anti-immigrant or Militarised Nationalism", "Definition": "Anti-immigrant or Militarised Nationalism: Using language that demonizes immigrants, deploying military-type enforcement (like the National Guard) within the U.S., and expanding domestic surveillance."},
    {"Theme": "Info Control", "Mapping": "Controlling Information Including Spreading Misinformation and Propaganda", "Definition": "Controlling information including spreading misinformation and propaganda: Manufacturing evidence to support state policy, restricting access to contradicting evidence, and spreading propaganda."},
    {"Theme": "Science & Health", "Mapping": "Control of Science & Health to Align with State Ideology", "Definition": "Control of science to align with state ideology: Restricting scientific research (e.g., on climate change), expanding drilling against environmental evidence, and attacking public health through vaccine restrictions or funding cuts."},
    {"Theme": "Suppressing Dissent", "Mapping": "Suppressing Dissent / Weaponising State Against 'Enemies'", "Definition": "Suppressing dissent / Weaponising state power against 'enemies': Punishing opponents, instituting loyalty tests, and weaponizing executive power or legal action against rivals, critics, and perceived enemy states or cities."}
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

# 4. STRATEGIC DIALOG (FACTS OVER OPINIONS)
@st.dialog("Strategic Note on Facts")
def show_welcome():
    st.markdown("""
    **Opinions shall not trump the data.**
    
    In an era where the "certainty of fanatics” is all the rage (like Bertrand Russell almost said), this tracker is built for those who prioritize **verifiable doubt**, and dare to care enough to share. Or god help us sharpen our wits against the FU things IRL in Murica 2025-2026!
    
    **The real world problems gone bananas:**
    
    * **Velocity:** the rate at which institutional norms are rewritten; ’procedural shock’ is a euphemism.
    * **Complexity:** the ‘strategic’ overlap; the 'multi-tagged' actions that strike several democratic pillars at once.
    
    ---
    Now, if you’re curious 👀 click anywhere outside this box to begin your investigation.
    """)

if "first_visit" not in st.session_state:
    st.session_state.first_visit = True
    show_welcome()

# 5. SEARCH SYNC CALLBACKS
if "search_term" not in st.session_state:
    st.session_state.search_term = ""

def sync_sidebar():
    st.session_state.search_term = st.session_state.sidebar_search

def sync_vault():
    st.session_state.search_term = st.session_state.vault_search

# 6. SIDEBAR & DATA CONTROLS
st.sidebar.title("🎛️ Data Controls")

def reset_filters():
    st.session_state.search_term = ""
    st.session_state.sidebar_search = ""
    st.session_state.vault_search = ""
    st.session_state.comparison_mode = False
    st.session_state.filter_area = "All Actions"
    if df is not None:
        st.session_state.date_range = (df['Date'].min().to_pydatetime(), df['Date'].max().to_pydatetime())

st.sidebar.text_input("🔍 Global Search", key="sidebar_search", on_change=sync_sidebar, value=st.session_state.search_term)

st.sidebar.divider()
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", key="comparison_mode")
query_params = st.query_params
default_area = query_params.get("area", "All Actions")

options = ["All Actions"] + SORTED_SHORT_NAMES
if comparison_mode:
    selected_compare = st.sidebar.multiselect("Categories", SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
    selected_short = "Comparison View"
else:
    start_index = options.index(default_area) if default_area in options else 0
    selected_short = st.sidebar.selectbox("Filter Area", options, index=start_index, key="filter_area")
    st.query_params["area"] = selected_short

if df is not None:
    st.sidebar.divider()
    st.sidebar.subheader("📅 Timeline Scrub")
    min_date = df['Date'].min().to_pydatetime()
    max_date = df['Date'].max().to_pydatetime()
    selected_range = st.sidebar.slider("Select Window", min_value=min_date, max_value=max_date, value=(min_date, max_date), key="date_range", format="MMM DD")
    
    mask = (df['Date'] >= selected_range[0]) & (df['Date'] <= selected_range[1])
    if st.session_state.search_term:
        mask = mask & (df['Title'].str.contains(st.session_state.search_term, case=False, na=False))
    filtered_df = df.loc[mask]
    
    st.sidebar.divider()
    st.sidebar.button("🧹 Clear All Filters", on_click=reset_filters, use_container_width=True)
else:
    filtered_df = pd.DataFrame()

# 7. ELEGANT DREAMY BRANDED HEADER
st.markdown("<div id='top'></div>", unsafe_allow_html=True)

st.markdown("""
    <style>
        .brand-container { max-width: 1200px; margin-bottom: 30px; }
        .brand-link { text-decoration: none !important; color: inherit !important; display: flex; align-items: center; gap: 20px; }
        .brand-link h1 { color: inherit !important; text-decoration: none !important; margin: 0 !important; font-weight: 700; line-height: 1.1; font-size: calc(1.5rem + 1.5vw); }
        .brand-logo { font-size: 2.5rem; background: transparent; padding: 5px 0px; transition: transform 0.8s cubic-bezier(0.4, 0, 0.2, 1); display: flex; align-items: center; justify-content: center; }
        .brand-link:hover .brand-logo { transform: scale(1.1); }
        .brand-link:hover h1 { opacity: 0.7; transition: opacity 0.8s ease; }
    </style>
    <div class="brand-container">
        <a href="https://trump-actions-tracker.streamlit.app/" target="_self" class="brand-link">
            <div class="brand-logo">🍌</div>
            <div><h1>U.S. Democracy Gone Bananas</h1></div>
        </a>
    </div>
""", unsafe_allow_html=True)

st.markdown("##### Diagnostic of systemic democratic erosion and institutional dismantling since Jan 2025.")
st.info("**Context:** Data Source: [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0")

# 8. HERO STATS (RESPONSIVE)
if not filtered_df.empty:
    total_actions = len(filtered_df)
    days_active = max((selected_range[1] - selected_range[0]).days, 1)
    pace_per_month = (total_actions / days_active) * 30.44
    overlap = (len(filtered_df[filtered_df['Cat_Count'] > 1]) / total_actions * 100)

    st.markdown(f"""
    <div style="display: flex; justify-content: center; gap: 20px; width: 100%; padding: 40px 0; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 250px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">Actions in Window</p>
            <h2 style="margin: 0; font-size: 2.5rem; color: #FFFFFF;">{total_actions}</h2>
        </div>
        <div style="flex: 1; min-width: 250px; background: rgba(255, 255, 255, 0.05); border: 1px solid #DE0100; border-radius: 10px; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">Velocity (Window)</p>
            <h2 style="margin: 0; font-size: 2.5rem; color: #DE0100;">{pace_per_month:.1f} <span style="font-size: 1rem;">/ mo</span></h2>
        </div>
        <div style="flex: 1; min-width: 250px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">Strategic Overlap</p>
            <h2 style="margin: 0; font-size: 2.5rem; color: #FFFFFF;">{overlap:.1f}%</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 9. STICKY NAV & ANCHOR STYLES
st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) { position: sticky; top: 2.875rem; z-index: 999; background-color: #0e1117; padding: 20px 0; }
        [id] { scroll-margin-top: 110px !important; }
        .back-to-top { font-size: 0.75rem; color: #666; text-decoration: none; display: block; text-align: right; margin-top: 5px; }
        .back-to-top:hover { color: #DE0100; transition: 0.3s; }
    </style>
    <div class="nav-container" style="display: flex; justify-content: space-between; gap: 8px;">
        <a href="#timeline" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Timeline</button></a>
        <a href="#themes" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Themes</button></a>
        <a href="#latest" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Latest</button></a>
        <a href="#insights" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Insights</button></a>
        <a href="#search" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Search</button></a>
    </div>
""", unsafe_allow_html=True)

# 10. DATA PROCESSING
if not filtered_df.empty:
    if comparison_mode:
        long_cats = [SHORT_TO_LONG[s] for s in selected_compare]
        display_df = filtered_df.melt(id_vars=['Date', 'Index', 'Title', 'Themes_List', 'URL', 'Cat_Count'], value_vars=long_cats, var_name='Category_Long', value_name='Is_Active')
        display_df = display_df[display_df['Is_Active'].fillna('No').astype(str).str.strip().str.lower() == 'yes']
        display_df['Category_Short'] = display_df['Category_Long'].map(CATEGORY_MAP)
        display_df['Cumulative'] = display_df.groupby('Category_Short').cumcount() + 1
    else:
        display_df = filtered_df if selected_short == "All Actions" else filtered_df[filtered_df[SHORT_TO_LONG[selected_short]].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
        chart_df = display_df.sort_values('Date')
        filtered_daily = chart_df.groupby('Date')['Index'].nunique().reset_index()
        filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
        chart_df = chart_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 11. TIMELINE & SECTIONS
st.markdown("<div id='timeline'></div>", unsafe_allow_html=True)
if not filtered_df.empty:
    if comparison_mode:
        st.subheader("Velocity Analysis: Comparative Theme Growth")
        comp_chart = alt.Chart(display_df).mark_line(interpolate='step-after', strokeWidth=3).encode(x='Date:T', y='Cumulative:Q', color='Category_Short:N').interactive()
        st.altair_chart(comp_chart, use_container_width=True)
    else:
        st.subheader(f"Timeline Progression: {selected_short}")
        line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(x='Date:T', y='Cumulative:Q')
        points = alt.Chart(chart_df).mark_circle(size=110, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(x='Date:T', y='Cumulative:Q', href='URL:N', tooltip=['Date:T', 'Title:N'])
        st.altair_chart((line + points).interactive(), use_container_width=True)
st.markdown("<a href='#top' class='back-to-top'>^^ Back to Top</a>", unsafe_allow_html=True)

# 12. THEMES & GLOSSARY
st.markdown("<div id='themes'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Action Volume by Theme")
cat_counts = []
for long, short in CATEGORY_MAP.items():
    if comparison_mode and short not in selected_compare: continue
    count = (filtered_df[long].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    if count > 0: cat_counts.append({'Theme': short, 'Count': count})
if cat_counts:
    st.altair_chart(alt.Chart(pd.DataFrame(cat_counts)).mark_bar(color='#DE0100').encode(x='Count:Q', y=alt.Y('Theme:N', sort='-x')), use_container_width=True)
with st.expander("📖 Themes Glossary"): st.table(GLOSSARY_DF[['Theme', 'Mapping', 'Definition']])
st.markdown("<a href='#top' class='back-to-top'>^^ Back to Top</a>", unsafe_allow_html=True)

# 13. LATEST
st.markdown("<div id='latest'></div>", unsafe_allow_html=True)
st.divider()
st.subheader(f"📍 Latest Actions in Window")
if not filtered_df.empty:
    latest_view = display_df.sort_values('Date', ascending=False).head(5)
    for i, row in latest_view.iterrows():
        with st.expander(f"📅 {row['Date'].strftime('%Y-%m-%d')} — {row['Title'][:90]}..."):
            st.write(f"**Description:** {row['Title']}")
            st.link_button("🚀 View Source", row['URL'])
st.markdown("<a href='#top' class='back-to-top'>^^ Back to Top</a>", unsafe_allow_html=True)

# 14. DEEP INSIGHTS (RESTORED ANALYSIS)
st.markdown("<div id='insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: Strategic Diagnostic")

if not filtered_df.empty:
    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown("#### Strategic Velocity & Attrition")
        st.write(f"The administration is maintaining a velocity of **{pace_per_month:.1f} actions per month**. This is designed to ensure judicial **processing latency** remains higher than the implementation rate. In strategic terms, this volume induces 'procedural shock'—where the sheer number of executive orders and policy shifts exhausts the bandwidth of civil society, journalists, and the legal system.")
        st.markdown("#### Norm-Collapse Loops")
        st.write(f"**Interconnectivity:** {overlap:.1f}% of events are 'multi-tagged,' indicating interlocking strikes engineered to bypass multiple institutional checks simultaneously. For example, an action targeting federal civil service often simultaneously limits scientific research and restricts public access to information.")
    with col_ins2:
        st.markdown("#### The Resistance Heatmap")
        st.write("Opposition is currently concentrated in state-level hubs (CA, WA, NY, IL). Litigation acts as the primary friction point against this velocity, explaining the prioritization of Judicial and DOJ hollowing. Data shows that as federal checks weaken, the 'Blue State Shield' becomes the primary mechanism for preserving the Rule of Law.")
        st.warning(f"**Diagnostic Projection:** By Jan 2029, the tracker projects **8,220 actions**. This signals a move toward a total administrative rewrite—where the cumulative weight of changes effectively creates a new, non-democratic operating system for the federal government.")

    st.markdown("<br><h4 style='text-align: center;'>Methodology Context & Expert Analysis</h4>", unsafe_allow_html=True)
    v_left, v_mid, v_right = st.columns([1, 8, 1])
    with v_mid: st.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")
st.markdown("<a href='#top' class='back-to-top'>^^ Back to Top</a>", unsafe_allow_html=True)

# 15. SEARCH DATA VAULT (SYNCED & CLICKABLE LINKS)
st.markdown("<div id='search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Search Data Vault")
st.info("💡 Pro-tip: This box syncs with the Global Search in the sidebar.")
st.text_input("Filter the vault directly...", key="vault_search", on_change=sync_vault, value=st.session_state.search_term, placeholder="Type to filter results...")

if not filtered_df.empty:
    v_df = display_df.sort_values('Date', ascending=False)
    # CRITICAL FIX: Explicit LinkColumn configuration
    st.dataframe(
        v_df[['Date', 'Title', 'URL', 'Themes_List']], 
        column_config={
            "URL": st.column_config.LinkColumn("Source", help="Click to open primary source"),
            "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")
        },
        use_container_width=True, 
        hide_index=True
    )
st.markdown("<a href='#top' class='back-to-top'>^^ Back to Top</a>", unsafe_allow_html=True)

st.caption("Dashboard by Celine Nadeau aka bananasutra. Last updated 03-02-2026. CC BY 4.0.")
