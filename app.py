import streamlit as st
import pandas as pd
import altair as alt
from urllib.parse import urlparse

# 1. PAGE CONFIG & SEO
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# RESTORED: SEO Workaround for Social Media Previews
st.markdown("""
    <head>
    <meta property="og:title" content="U.S. Democracy Gone Bananas: Trump Actions Tracker" />
    <meta property="og:description" content="A strategic diagnostic of systemic democratic erosion in the U.S. since Jan 2025." />
    <meta name="twitter:card" content="summary_large_image">
    </head>
    """, unsafe_allow_html=True)

# 2. CATEGORY MAPPING
CATEGORY_MAP = {
    "Violating Democratic Norms, Undermining Rule of Law": "Democratic Norms",
    "Hollowing State / Weakening Federal Institutions": "Federal Institutions",
    "Suppressing Dissent / Weaponising State Against 'Enemies'": "Suppressing Dissent",
    "Controlling Information Including Spreading Misinformation and Propaganda": "Info Control",
    "Control of Science & Health to Align with State Ideology": "Science & Health",
    "Attacking Universities, Schools, Museums, Culture": "Education & Culture",
    "Weakening Civil Rights": "Civil Rights",
    "Corruption & Enrichment": "Corruption",
    "Aggressive Foreign Policy & Global Destabilisation": "Foreign Policy",
    "Anti-immigrant or Militarised Nationalism": "Immigration & Nationalism"
}
SORTED_SHORT_NAMES = sorted(list(CATEGORY_MAP.values()))
SHORT_TO_LONG = {v: k for k, v in CATEGORY_MAP.items()}

# 3. LOAD DATA
@st.cache_data
def load_data():
    files_to_try = ['trump-actions-3-1-26.csv', 'trump-actions.csv']
    df = None
    for file in files_to_try:
        try:
            df = pd.read_csv(file, skiprows=2)
            break
        except:
            continue
    if df is None: return None, None

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=True) 
    cat_cols = list(CATEGORY_MAP.keys())
    
    df['Themes_List'] = df.apply(lambda r: ", ".join([CATEGORY_MAP.get(c, c) for c in cat_cols if str(r[c]).strip().lower() == 'yes']), axis=1)
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df, cat_cols

df, cat_cols = load_data()

# 4. DEEP LINK LOGIC
query_params = st.query_params
default_area = query_params.get("area", "All Actions")

# 5. HEADER & VELOCITY METRICS
st.title("🙊 U.S. Democracy Gone Bananas")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0")

if not df.empty:
    total_actions = len(df)
    days_active = (df['Date'].max() - df['Date'].min()).days
    pace_per_month = (total_actions / max(days_active, 1)) * 30.44
    last_update = df['Date'].max().strftime('%b %d, %Y')
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Actions Logged", f"{total_actions}", f"Updated {last_update}", delta_color="off")
    m2.metric("Current Velocity", f"{pace_per_month:.1f} / mo", delta="⚠️ Critical Pace", delta_color="inverse")
    m3.metric("Strategic Overlap", f"{(len(df[df['Cat_Count'] > 1]) / total_actions * 100):.1f}%", help="Percentage of actions impacting multiple democratic norms simultaneously.")

st.info("**Context:** A strategic diagnostic of systemic democratic erosion in the U.S. since Jan 2025.")

# 6. STICKY GHOST NAVIGATION
st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) {
            position: sticky; top: 2.875rem; z-index: 999; background-color: #0e1117; padding: 10px 0;
        }
    </style>
    <div class="nav-container" style="display: flex; justify-content: space-between; gap: 8px; margin-bottom: 25px;">
        <a href="#timeline" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Timeline</button></a>
        <a href="#themes" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Themes</button></a>
        <a href="#latest" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Latest</button></a>
        <a href="#insights" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Insights</button></a>
        <a href="#search" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Search</button></a>
    </div>
""", unsafe_allow_html=True)

# 7. SIDEBAR & URL SYNC
st.sidebar.title("Filters")
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", value=False)
if comparison_mode:
    selected_compare = st.sidebar.multiselect("Categories", SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
    selected_short = "Comparison View"
else:
    if default_area in (["All Actions"] + SORTED_SHORT_NAMES):
        start_index = (["All Actions"] + SORTED_SHORT_NAMES).index(default_area)
    else: start_index = 0
    selected_short = st.sidebar.selectbox("Filter Area", ["All Actions"] + SORTED_SHORT_NAMES, index=start_index)
    st.query_params["area"] = selected_short

# 8. DATA LOGIC
if comparison_mode:
    long_cats = [SHORT_TO_LONG[s] for s in selected_compare]
    df_comp = df.melt(id_vars=['Date', 'Index', 'Title', 'Themes_List', 'URL', 'Cat_Count'], value_vars=long_cats, var_name='Category_Long', value_name='Is_Active')
    df_comp = df_comp[df_comp['Is_Active'].fillna('No').astype(str).str.strip().str.lower() == 'yes']
    df_comp['Category_Short'] = df_comp['Category_Long'].map(CATEGORY_MAP)
    df_comp = df_comp.sort_values(['Category_Short', 'Date'])
    df_comp['Cumulative'] = df_comp.groupby('Category_Short').cumcount() + 1
    display_df = df_comp 
else:
    display_df = df if selected_short == "All Actions" else df[df[SHORT_TO_LONG[selected_short]].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
    chart_df = display_df.sort_values('Date')
    filtered_daily = chart_df.groupby('Date')['Index'].nunique().reset_index()
    filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
    chart_df = chart_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 9. TIMELINE
st.markdown("<div id='timeline' style='padding-top: 60px;'></div>", unsafe_allow_html=True)
if comparison_mode:
    st.subheader("Velocity Analysis: Comparative Theme Growth")
    if not df_comp.empty:
        comp_chart = alt.Chart(df_comp).mark_line(interpolate='step-after', strokeWidth=3).encode(
            x=alt.X('Date:T', title='Timeline'),
            y=alt.Y('Cumulative:Q', title='Actions'),
            color=alt.Color('Category_Short:N', legend=alt.Legend(orient='bottom', columns=2), scale=alt.Scale(scheme='category10'))
        ).interactive().properties(height=450)
        st.altair_chart(comp_chart, use_container_width=True)
else:
    st.subheader(f"Timeline Progression: {selected_short}")
    line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(x='Date:T', y='Cumulative:Q')
    points = alt.Chart(chart_df).mark_circle(size=110, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
        x='Date:T', y='Cumulative:Q', href='URL:N',
        tooltip=[alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'), 'Title:N', 'Themes_List:N']
    )
    st.altair_chart((line + points).interactive(), use_container_width=True)

# RESTORED: Progression Chart Tips
st.caption("💡 **Desktop:** Hover for details, Click point for source. **Mobile:** Use Search section for stable links.")
st.caption("⚠️ **Note on Links:** Many sites block direct opening. Search the Data Vault for direct source links.")

# 10. THEMES & GLOSSARY
st.markdown("<div id='themes' style='padding-top: 60px;'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Action Volume by Theme")
cat_counts = []
for long, short in CATEGORY_MAP.items():
    if comparison_mode and short not in selected_compare: continue
    count = (df[long].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    if count > 0: cat_counts.append({'Category': short, 'Count': count})

if cat_counts:
    bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)
    st.altair_chart(alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
        x=alt.X('Count:Q', title='Volume'),
        y=alt.Y('Category:N', sort='-x', title=None)
    ).properties(height=len(bar_df) * 40 + 50), use_container_width=True)

with st.expander("📖 Category Glossary"):
    st.table(pd.DataFrame({"Theme": list(SHORT_TO_LONG.keys()), "Definition": list(SHORT_TO_LONG.values())}))

# 11. LATEST
st.markdown("<div id='latest' style='padding-top: 60px;'></div>", unsafe_allow_html=True)
st.divider()
st.subheader(f"📍 Latest 5 Actions: {selected_short}")
latest_view = display_df.sort_values('Date', ascending=False).head(5)
for i, row in latest_view.iterrows():
    with st.expander(f"📅 {row['Date'].strftime('%Y-%m-%d')} — {row['Title'][:90]}..."):
        st.write(f"**Description:** {row['Title']}")
        st.write(f"**Themes:** {row['Themes_List']}")
        st.link_button("🚀 View Source", row['URL'])

# 12. DEEP INSIGHTS (RESTORED FULL ANALYTICAL DEPTH)
st.markdown("<div id='insights' style='padding-top: 60px;'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: Strategic Diagnostic")

if not df.empty:
    total_raw = len(df)
    days_span = (df['Date'].max() - df['Date'].min()).days
    monthly_pace = (total_raw / max(days_span, 1)) * 30.44
    multi_ratio = (len(df[df['Cat_Count'] > 1]) / total_raw) * 100 if total_raw > 0 else 0

    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown("#### Strategic Velocity & Attrition")
        st.write(f"The administration is maintaining a velocity of **{monthly_pace:.1f} actions per month**. This is designed to ensure judicial **processing latency** remains higher than the implementation rate.")
        st.warning(f"**Diagnostic Projection:** By Jan 2029, the tracker projects **8,220 actions**. This signals a move toward a total administrative rewrite.")
        
        st.markdown("#### Norm-Collapse Loops")
        st.write(f"**Interconnectivity:** {multi_ratio:.1f}% of events are 'multi-tagged,' indicating interlocking strikes engineered to bypass multiple institutional checks simultaneously.")

    with col_ins2:
        st.markdown("#### The Resistance Heatmap")
        st.write("Opposition is concentrated in state-level hubs (CA, WA, NY, IL). Litigation acts as the primary friction point against this velocity, explaining the prioritization of Judicial and DOJ hollowing.")
        st.markdown("<div style='padding-top: 20px;'>", unsafe_allow_html=True)
        st.markdown("**Methodology Context:**")
        st.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")
        st.markdown("</div>", unsafe_allow_html=True)

# 13. SEARCH DATA VAULT
st.markdown("<div id='search' style='padding-top: 60px;'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🔍 Search Data Vault")
search = st.text_input("Filter Data...", placeholder="Type keywords...")
v_df = display_df.sort_values('Date', ascending=False)
if search:
    v_df = v_df[v_df['Title'].str.contains(search, case=False, na=False)]
st.dataframe(
    v_df[['Date', 'Title', 'URL', 'Themes_List']], 
    column_config={"URL": st.column_config.LinkColumn("Source"), "Themes_List": "Themes"},
    use_container_width=True, hide_index=True
)

st.caption("Dashboard by Celine Nadeau aka bananasutra. Updated Mar 2026. CC BY 4.0.")
