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

st.markdown("""
    <head>
    <meta property="og:title" content="U.S. Democracy Gone Bananas: Trump Actions Tracker" />
    <meta property="og:description" content="A strategic diagnostic of systemic democratic erosion in the U.S. since Jan 2025." />
    <meta property="og:image" content="https://raw.githubusercontent.com/celinenadeau/repo/main/og-image.png" />
    <meta name="twitter:card" content="summary_large_image">
    </head>
    """, unsafe_allow_html=True)

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

# 4. SIDEBAR (FILTERS & DATE SLIDER)
st.sidebar.title("Filters")
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", value=False)
query_params = st.query_params
default_area = query_params.get("area", "All Actions")

if comparison_mode:
    selected_compare = st.sidebar.multiselect("Categories", SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
    selected_short = "Comparison View"
else:
    options = ["All Actions"] + SORTED_SHORT_NAMES
    start_index = options.index(default_area) if default_area in options else 0
    selected_short = st.sidebar.selectbox("Filter Area", options, index=start_index)
    st.query_params["area"] = selected_short

if df is not None:
    st.sidebar.divider()
    st.sidebar.subheader("📅 Timeline Scrub")
    min_date = df['Date'].min().to_pydatetime()
    max_date = df['Date'].max().to_pydatetime()
    selected_range = st.sidebar.slider("Select Window", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="MMM DD")
    mask = (df['Date'] >= selected_range[0]) & (df['Date'] <= selected_range[1])
    filtered_df = df.loc[mask]
else:
    filtered_df = df

# 5. HEADER & HERO
st.title("🙊 U.S. Democracy Gone Bananas")
st.markdown("##### Diagnostic of systemic democratic erosion and institutional dismantling since Jan 2025.")
st.info("**Context:** Data Source: [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0")

if filtered_df is not None and not filtered_df.empty:
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
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">Velocity (Current Window)</p>
            <h2 style="margin: 0; font-size: 2.5rem; color: #DE0100;">{pace_per_month:.1f} <span style="font-size: 1rem;">/ mo</span></h2>
            <p style="margin: 0; font-size: 0.8rem; color: #DE0100; font-weight: bold;">⚠️ Critical Pace</p>
        </div>
        <div style="flex: 1; min-width: 250px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">Strategic Overlap</p>
            <h2 style="margin: 0; font-size: 2.5rem; color: #FFFFFF;">{overlap:.1f}%</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 6. STICKY NAVIGATION & ANCHOR FIX
st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) {
            position: sticky; top: 2.875rem; z-index: 999; 
            background-color: #0e1117; padding: 20px 0;
        }
        [id] { scroll-margin-top: 110px !important; }
    </style>
    <div class="nav-container" style="display: flex; justify-content: space-between; gap: 8px;">
        <a href="#timeline" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Timeline</button></a>
        <a href="#themes" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Themes</button></a>
        <a href="#latest" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Latest</button></a>
        <a href="#insights" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Insights</button></a>
        <a href="#search" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Search</button></a>
    </div>
""", unsafe_allow_html=True)

# 7. DATA PROCESSING
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

# 8. TIMELINE
st.markdown("<div id='timeline'></div>", unsafe_allow_html=True)
if comparison_mode:
    st.subheader("Velocity Analysis: Comparative Theme Growth")
    if not display_df.empty:
        comp_chart = alt.Chart(display_df).mark_line(interpolate='step-after', strokeWidth=3).encode(
            x=alt.X('Date:T', title='Timeline'), y=alt.Y('Cumulative:Q', title='Actions'),
            color=alt.Color('Category_Short:N', legend=alt.Legend(orient='bottom', columns=2))
        ).interactive().properties(height=450)
        st.altair_chart(comp_chart, use_container_width=True)
else:
    st.subheader(f"Timeline Progression: {selected_short}")
    if not display_df.empty:
        line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(x='Date:T', y='Cumulative:Q')
        points = alt.Chart(chart_df).mark_circle(size=110, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
            x='Date:T', y='Cumulative:Q', href='URL:N',
            tooltip=[alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'), 'Title:N', 'Themes_List:N']
        )
        st.altair_chart((line + points).interactive(), use_container_width=True)

st.caption("💡 **Desktop:** Hover for details, Click point for source. **Mobile:** Use Search section for stable links.")

# 9. THEMES & GLOSSARY
st.markdown("<div id='themes'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Action Volume by Theme")
cat_counts = []
for long, short in CATEGORY_MAP.items():
    if comparison_mode and short not in selected_compare: continue
    count = (filtered_df[long].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    if count > 0: cat_counts.append({'Theme': short, 'Count': count})

if cat_counts:
    bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)
    st.altair_chart(alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
        x=alt.X('Count:Q', title='Volume'),
        y=alt.Y('Theme:N', sort='-x', title=None, axis=alt.Axis(labelLimit=300))
    ).properties(height=len(bar_df) * 40 + 50), use_container_width=True)

with st.expander("📖 Themes Glossary"):
    st.table(GLOSSARY_DF[['Theme', 'Mapping', 'Definition']])

# 10. LATEST
st.markdown("<div id='latest'></div>", unsafe_allow_html=True)
st.divider()
st.subheader(f"📍 Latest 5 Actions in Window: {selected_short}")
latest_view = display_df.sort_values('Date', ascending=False).head(5)
for i, row in latest_view.iterrows():
    with st.expander(f"📅 {row['Date'].strftime('%Y-%m-%d')} — {row['Title'][:90]}..."):
        st.write(f"**Description:** {row['Title']}")
        st.write(f"**Themes:** {row['Themes_List']}")
        st.link_button("🚀 View Source", row['URL'])

# 11. DEEP INSIGHTS (REFINED LAYOUT)
st.markdown("<div id='insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: Strategic Diagnostic")

if filtered_df is not None and not filtered_df.empty:
    total_raw = len(filtered_df)
    multi_ratio = (len(filtered_df[filtered_df['Cat_Count'] > 1]) / total_raw * 100)
    
    # ROW 1: EQUALIZED COLUMNS
    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown("#### Strategic Velocity & Attrition")
        st.write(f"The administration is maintaining a velocity of **{pace_per_month:.1f} actions per month**. This volume induces 'procedural shock'—where the sheer number of executive orders exhausts the bandwidth of civil society and the legal system.")
        
        st.markdown("#### Norm-Collapse Loops")
        st.write(f"**Interconnectivity:** {multi_ratio:.1f}% of events are 'multi-tagged,' indicating interlocking strikes engineered to bypass multiple institutional checks simultaneously.")

    with col_ins2:
        st.markdown("#### The Resistance Heatmap")
        st.write("Opposition centers in CA, WA, NY, IL. Litigation acts as the primary friction point against this velocity, explaining the prioritization of Judicial and DOJ hollowing.")
        
        # MOVED DIAGNOSTIC HIGHLIGHT HERE
        st.warning(f"**Diagnostic Projection:** By Jan 2029, the tracker projects **8,220 actions**. This signals a total administrative rewrite—where the cumulative weight of changes effectively creates a new operating system for the federal government.")

    # ROW 2: FULL WIDTH VIDEO
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Methodology Context & Expert Analysis")
    st.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")

# 12. SEARCH
st.markdown("<div id='search'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Search Data Vault")
search = st.text_input("Filter Window...", placeholder="Type keywords...")
v_df = display_df.sort_values('Date', ascending=False)
if search:
    v_df = v_df[v_df['Title'].str.contains(search, case=False, na=False)]
st.dataframe(
    v_df[['Date', 'Title', 'URL', 'Themes_List']], 
    column_config={"URL": st.column_config.LinkColumn("Source"), "Themes_List": "Themes"},
    use_container_width=True, hide_index=True
)

st.caption("Dashboard by Celine Nadeau aka bananasutra. Last updated 03-02-2026. CC BY 4.0.")
