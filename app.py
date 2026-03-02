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

# 3. Load and Clean Data
@st.cache_data
def load_data():
    files_to_try = ['trump-actions-3-1-26.csv', 'trump-actions.csv']
    df = None
    for file in files_to_try:
        try:
            df = pd.read_csv(file, skiprows=2)
            break
        except FileNotFoundError:
            continue
    
    if df is None:
        st.error("Data file not found. Ensure the latest CSV is in your repository.")
        return None, None

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=False)
    cat_cols = list(CATEGORY_MAP.keys())
    
    def get_active_short(row):
        return ", ".join([CATEGORY_MAP.get(col, col) for col in cat_cols if str(row[col]).strip().lower() == 'yes'])
    
    df['Themes'] = df.apply(get_active_short, axis=1)
    df['Source_Domain'] = df['URL'].apply(lambda x: urlparse(str(x)).netloc.replace('www.', '') if pd.notnull(x) else "Other")
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    
    return df, cat_cols

df, cat_cols = load_data()

# 4. Sidebar Navigation
st.sidebar.title("Navigation & Filters")
comparison_mode = st.sidebar.toggle("📊 Comparison Mode (Multi-Line)", value=False)

if comparison_mode:
    selected_compare = st.sidebar.multiselect("Categories to Compare", SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
    selected_short = "Comparison View"
else:
    selected_short = st.sidebar.selectbox("Filter by Policy Area", ["All Actions"] + SORTED_SHORT_NAMES)

# 5. Filtering Logic
if comparison_mode:
    long_cats = [SHORT_TO_LONG[s] for s in selected_compare]
    df_comp = df.melt(id_vars=['Date', 'Index', 'Title', 'Themes', 'URL', 'Source_Domain', 'Cat_Count'], 
                      value_vars=long_cats, var_name='Category_Long', value_name='Is_Active')
    df_comp = df_comp[df_comp['Is_Active'].fillna('No').astype(str).str.strip().str.lower() == 'yes']
    df_comp['Category_Short'] = df_comp['Category_Long'].map(CATEGORY_MAP)
    df_comp = df_comp.sort_values(['Category_Short', 'Date'])
    df_comp['Count'] = 1
    df_comp['Cumulative'] = df_comp.groupby('Category_Short')['Count'].cumsum()
    display_df = df_comp 
else:
    display_df = df if selected_short == "All Actions" else df[df[SHORT_TO_LONG[selected_short]].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
    chart_df = display_df.sort_values('Date')
    filtered_daily = chart_df.groupby('Date')['Index'].nunique().reset_index().sort_values('Date')
    filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
    chart_df = chart_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 6. Top Anchored Navigation Menu
st.markdown("### 🧭 Quick Navigation")
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)
if nav_col1.button("📈 Timeline", use_container_width=True): st.write('<style>div.row-widget.stButton > button { border: 2px solid red; }</style>', unsafe_allow_html=True)
if nav_col2.button("📊 Volume", use_container_width=True): pass
if nav_col3.button("🚨 Insights", use_container_width=True): pass
if nav_col4.button("📍 Latest", use_container_width=True): pass
if nav_col5.button("🗄️ Vault", use_container_width=True): pass

# 7. Header
st.title("🙊 U.S. Democracy Gone Bananas")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0")

# 8. Charts Section
if comparison_mode:
    st.subheader("Category Comparison: Growth Over Time")
    if not df_comp.empty:
        comp_chart = alt.Chart(df_comp).mark_line(interpolate='step-after', strokeWidth=3).encode(
            x=alt.X('Date:T', title='Timeline'),
            y=alt.Y('Cumulative:Q', title='Cumulative Actions'),
            color=alt.Color('Category_Short:N', title=None, legend=alt.Legend(orient='bottom', columns=2)),
            tooltip=[alt.Tooltip('Date:T', format='%Y-%m-%d'), 'Title:N', 'Category_Short:N']
        ).interactive().properties(height=450)
        st.altair_chart(comp_chart, use_container_width=True)
    else:
        st.info("Select a category to view comparison.")
else:
    st.subheader(f"Timeline Progression: {selected_short}")
    line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(x='Date:T', y='Cumulative:Q')
    points = alt.Chart(chart_df).mark_circle(size=110, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
        x='Date:T', y='Cumulative:Q', href='URL:N',
        tooltip=[alt.Tooltip('Date:T', format='%Y-%m-%d'), 'Title:N', 'Themes:N']
    )
    st.altair_chart((line + points).interactive(), use_container_width=True)

# RESTORED: Hover & Links Tip
st.caption("💡 **Desktop:** Hover for details, Click point for source. **Mobile:** Use Data Vault below for stable links.")
st.caption("⚠️ **Note on Links:** Many sites (like *The Guardian*, *NYT*, *AP*) block direct opening from external apps. Search the action in the Data Vault to use the direct source link.")

# 9. Category Volume
st.divider()
st.subheader("Action Volume by Category")
cat_counts = []
for long, short in CATEGORY_MAP.items():
    if comparison_mode and short not in selected_compare: continue
    count = (display_df[long].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum() if not comparison_mode else len(df_comp[df_comp['Category_Short'] == short])
    if count > 0: cat_counts.append({'Category': short, 'Count': count})

if cat_counts:
    bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)
    st.altair_chart(alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
        x=alt.X('Count:Q', title='Volume'),
        y=alt.Y('Category:N', sort='-x', title=None),
        tooltip=['Category:N', 'Count:Q']
    ).properties(height=len(bar_df) * 40 + 50), use_container_width=True)

# 10. ANALYTICAL INSIGHTS (Moved below charts)
st.divider()
st.subheader("🚨 Deep Insights & Projections")

if not display_df.empty:
    total_actions = len(df)
    days_active = (df['Date'].max() - df['Date'].min()).days
    pace_per_month = (total_actions / max(days_active, 1)) * 30.44
    multi_cat_pct = (len(df[df['Cat_Count'] > 1]) / total_actions) * 100
    top_source = df['Source_Domain'].value_counts().idxmax()

    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.write("### ⚡ Pace of Power")
        st.write(f"The administration is moving at **{pace_per_month:.1f} actions per month**. Projection: **8,200 actions** by Jan 2029.")
        st.write("### 🛡️ Heatmap of Resistance")
        st.write("State-led litigation (led by WA, CA, NY) acts as the primary friction point against this velocity.")
    with col_ins2:
        st.write("### 📽️ Tracker Context")
        st.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")
        st.caption(f"**Multi-Tagging:** {multi_cat_pct:.1f}% of events impact multiple democratic norms.")

# 11. Glossary & Latest Actions
with st.expander("📖 Glossary & Multi-Tagging Logic"):
    st.table(pd.DataFrame({"Short Name": list(SHORT_TO_LONG.keys()), "Official Definition": list(SHORT_TO_LONG.values())}))

st.divider()
st.subheader(f"📍 Latest Actions: {selected_short}")
for i, row in display_df.head(5).iterrows():
    with st.expander(f"📅 {row['Date'].strftime('%Y-%m-%d')} — {row['Title'][:90]}..."):
        st.write(f"**Description:** {row['Title']}")
        st.link_button("🚀 Open Source", row['URL'])

# 12. Data Vault
st.divider()
st.subheader("Data Vault")
if not display_df.empty:
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Download View as CSV", data=csv, file_name=f'trump_actions.csv', mime='text/csv')

search = st.text_input("Search descriptions...", placeholder="Type here...")
filtered_table = display_df if not search else display_df[display_df['Title'].str.contains(search, case=False, na=False)]
if not filtered_table.empty:
    st.dataframe(filtered_table[['Date', 'Title', 'URL', 'Themes']], column_config={"URL": st.column_config.LinkColumn("Source Link"), "Date": st.column_config.DateColumn("Date")}, use_container_width=True, hide_index=True)

st.caption("Dashboard by Celine Nadeau aka bananasutra. Updated 03/01/2026. CC BY 4.0.")
