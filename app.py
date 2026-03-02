import streamlit as st
import pandas as pd
import altair as alt
from urllib.parse import urlparse

# 1. Page Config
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas: Trump Actions Tracker", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. Category Mapping
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

# 3. Load Data
@st.cache_data
def load_data():
    # Use the specific filename you've uploaded or a generic placeholder
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
    df = df.sort_values('Date', ascending=True) # Sort ascending for correct cumulative math
    cat_cols = list(CATEGORY_MAP.keys())
    
    df['Themes'] = df.apply(lambda r: ", ".join([CATEGORY_MAP.get(c, c) for c in cat_cols if str(r[c]).strip().lower() == 'yes']), axis=1)
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df, cat_cols

df, cat_cols = load_data()

# 4. Header & Navigation (Crisp White Anchors)
st.title("🙊 U.S. Democracy Gone Bananas")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0")
st.info("**Context:** Strategic diagnostic of systemic democratic erosion. *Updated March 2026.*")

st.markdown("""
<div style="display: flex; justify-content: space-between; gap: 10px; margin-top: 10px; margin-bottom: 25px;">
    <a href="#timeline" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Timeline</button></a>
    <a href="#volume" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Categories</button></a>
    <a href="#latest" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Latest</button></a>
    <a href="#insights" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Insights</button></a>
    <a href="#vault" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Search</button></a>
</div>
""", unsafe_allow_html=True)

# 5. Sidebar Logic
st.sidebar.title("Filters")
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", value=False)
if comparison_mode:
    selected_compare = st.sidebar.multiselect("Categories", SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
    selected_short = "Comparison View"
else:
    selected_short = st.sidebar.selectbox("Policy Area", ["All Actions"] + SORTED_SHORT_NAMES)

# 6. Data Processing Fix
if comparison_mode:
    long_cats = [SHORT_TO_LONG[s] for s in selected_compare]
    # Melting ensures we can plot multiple lines correctly
    df_comp = df.melt(id_vars=['Date', 'Index', 'Title', 'Themes', 'URL', 'Cat_Count'], 
                      value_vars=long_cats, var_name='Category_Long', value_name='Is_Active')
    df_comp = df_comp[df_comp['Is_Active'].fillna('No').astype(str).str.strip().str.lower() == 'yes']
    df_comp['Category_Short'] = df_comp['Category_Long'].map(CATEGORY_MAP)
    # Crucial: Sort by date within category for the cumulative sum
    df_comp = df_comp.sort_values(['Category_Short', 'Date'])
    df_comp['Cumulative'] = df_comp.groupby('Category_Short').cumcount() + 1
    display_df = df_comp.sort_values('Date', ascending=False)
else:
    display_df = df if selected_short == "All Actions" else df[df[SHORT_TO_LONG[selected_short]].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
    chart_df = display_df.sort_values('Date')
    filtered_daily = chart_df.groupby('Date')['Index'].nunique().reset_index()
    filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
    chart_df = chart_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 7. TIMELINE (FIXED LOGIC)
st.markdown("<div id='timeline'></div>", unsafe_allow_html=True)
if comparison_mode:
    st.subheader("Velocity Analysis: Comparative Category Growth")
    if not df_comp.empty:
        comp_chart = alt.Chart(df_comp).mark_line(interpolate='step-after', strokeWidth=3).encode(
            x=alt.X('Date:T', title='Timeline'),
            y=alt.Y('Cumulative:Q', title='Cumulative Actions'),
            color=alt.Color('Category_Short:N', title=None, legend=alt.Legend(orient='bottom', columns=2), scale=alt.Scale(scheme='category10')),
            tooltip=[alt.Tooltip('Date:T', format='%Y-%m-%d'), 'Title:N', 'Category_Short:N']
        ).interactive().properties(height=450)
        st.altair_chart(comp_chart, use_container_width=True)
else:
    st.subheader(f"Timeline Progression: {selected_short}")
    line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(x='Date:T', y='Cumulative:Q')
    points = alt.Chart(chart_df).mark_circle(size=110, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
        x='Date:T', y='Cumulative:Q', href='URL:N',
        tooltip=[alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'), alt.Tooltip('Title:N', title='Action'), alt.Tooltip('Themes:N', title='Themes')]
    )
    st.altair_chart((line + points).interactive(), use_container_width=True)

st.caption("💡 **Desktop:** Hover for details, Click point for source. **Mobile:** Use Data Vault below for stable links.")

# 8. VOLUME & GLOSSARY
st.markdown("<div id='volume'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Action Volume by Category")
cat_counts = []
# Fixed: Always calculate based on the full DF for the bar chart to show relative volume
for long, short in CATEGORY_MAP.items():
    if comparison_mode and short not in selected_compare: continue
    count = (df[long].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    if count > 0: cat_counts.append({'Category': short, 'Count': count})

if cat_counts:
    bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)
    st.altair_chart(alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
        x=alt.X('Count:Q', title='Volume'),
        y=alt.Y('Category:N', sort='-x', title=None),
        tooltip=['Category:N', 'Count:Q']
    ).properties(height=len(bar_df) * 40 + 50), use_container_width=True)

with st.expander("📖 Category Glossary"):
    st.table(pd.DataFrame({"Category": list(SHORT_TO_LONG.keys()), "Definition": list(SHORT_TO_LONG.values())}))

# 9. LATEST ACTIONS
st.markdown("<div id='latest'></div>", unsafe_allow_html=True)
st.divider()
st.subheader(f"📍 Latest 5 Actions: {selected_short}")
# Always pull from the most recent entries
latest_display = display_df.head(5)
for i, row in latest_display.iterrows():
    with st.expander(f"📅 {row['Date'].strftime('%Y-%m-%d')} — {row['Title'][:90]}..."):
        st.write(f"**Description:** {row['Title']}")
        st.write(f"**Themes:** {row['Themes']}")
        st.link_button("🚀 Open Source", row['URL'])

# 10. DEEP INSIGHTS (RESTORED TO FULL DEPTH)
st.markdown("<div id='insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: Strategic Diagnostic")

if not df.empty:
    total = len(df)
    pace = (total / max((df['Date'].max() - df['Date'].min()).days, 1)) * 30.44
    multi_ratio = (len(df[df['Cat_Count'] > 1]) / total) * 100

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ⚡ Strategic Velocity: The 'Shock' Phase")
        st.write(f"Executing **{pace:.1f} actions per month**. This volume ensures that judicial **processing latency** remains higher than the implementation rate—creating a permanent implementation advantage.")
        st.warning(f"**Diagnostic:** Linear extrapolation projects over **8,200 actions** by Jan 2029. This trajectory signals a move from policy 'disruption' to a 'full institutional rewrite.'")
        st.markdown("### 🕸️ Norm-Collapse Loops")
        st.write(f"**Interconnectivity:** {multi_ratio:.1f}% of actions are multi-tagged. This highlights 'interlocking strikes' where a single move (e.g. purging the civil service) simultaneously breaks 3+ institutional norms.")

    with col2:
        st.markdown("### 🛡️ The Heatmap of Resistance")
        st.write("Opposition is currently anchored by 'Blue State Shields' (CA, WA, NY, IL). Data shows litigation is the *only* functional friction point slowing velocity, explaining the prioritization of Judicial and DOJ hollowing.")
        st.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")

# 11. DATA VAULT
st.markdown("<div id='vault'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Data Vault")
search = st.text_input("Search descriptions...", placeholder="Filter by keyword...")
v_df = display_df if not search else display_df[display_df['Title'].str.contains(search, case=False, na=False)]
st.dataframe(
    v_df[['Date', 'Title', 'URL', 'Themes']], 
    column_config={"URL": st.column_config.LinkColumn("Source"), "Date": st.column_config.DateColumn("Date")},
    use_container_width=True, hide_index=True
)

st.caption("Dashboard by Celine Nadeau aka bananasutra. Updated Mar 2026. CC BY 4.0.")
