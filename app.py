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

# 2. Category Mapping & Descriptions
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
    
    df['Active_Categories_Short'] = df.apply(get_active_short, axis=1)
    df['Source_Domain'] = df['URL'].apply(lambda x: urlparse(x).netloc.replace('www.', '') if pd.notnull(x) else "Other")
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    
    return df, cat_cols

df, cat_cols = load_data()

# 4. Sidebar Navigation
st.sidebar.title("Navigation & Filters")
comparison_mode = st.sidebar.toggle("📊 Comparison Mode (Multi-Line)", value=False)

if comparison_mode:
    # UPDATED: Defaulting to ALL categories instead of just 2
    selected_compare = st.sidebar.multiselect(
        "Categories to Compare", 
        list(SHORT_TO_LONG.keys()), 
        default=list(SHORT_TO_LONG.keys()), # Selects everything by default
        help="Remove categories to simplify the comparison chart."
    )
    selected_short = "Comparison View"
else:
    selected_short = st.sidebar.selectbox("Filter by Policy Area", ["All Actions"] + list(SHORT_TO_LONG.keys()))

# 5. Filtering & Comparison Logic
if comparison_mode:
    long_cats = [SHORT_TO_LONG[s] for s in selected_compare]
    df_comp = df.melt(id_vars=['Date', 'Index', 'Title', 'Active_Categories_Short', 'URL'], 
                      value_vars=long_cats, var_name='Category_Long', value_name='Is_Active')
    df_comp = df_comp[df_comp['Is_Active'].fillna('No').astype(str).str.strip().str.lower() == 'yes']
    df_comp['Category_Short'] = df_comp['Category_Long'].map(CATEGORY_MAP)
    
    df_comp = df_comp.sort_values(['Category_Short', 'Date'])
    df_comp['Count'] = 1
    df_comp['Cumulative'] = df_comp.groupby('Category_Short')['Count'].cumsum()
    display_df = df_comp 
else:
    if selected_short != "All Actions":
        long_name = SHORT_TO_LONG[selected_short]
        display_df = df[df[long_name].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
    else:
        display_df = df.copy()
    
    chart_df = display_df.sort_values('Date')
    filtered_daily = chart_df.groupby('Date')['Index'].nunique().reset_index().sort_values('Date')
    filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
    chart_df = chart_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 6. Header
st.title("🙊 U.S. Democracy Gone Bananas")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0")

# 7. Chart Rendering
if comparison_mode:
    st.subheader("Category Comparison: Growth Over Time")
    if not df_comp.empty:
        comp_chart = alt.Chart(df_comp).mark_line(interpolate='step-after', strokeWidth=3).encode(
            x=alt.X('Date:T', title='Timeline'),
            y=alt.Y('Cumulative:Q', title='Cumulative Actions'),
            color=alt.Color('Category_Short:N', title='Category', scale=alt.Scale(scheme='category10')),
            tooltip=['Date:T', 'Category_Short:N', 'Cumulative:Q', 'Title:N']
        ).interactive().properties(height=500)
        st.altair_chart(comp_chart, use_container_width=True)
    else:
        st.info("Please select at least one category in the sidebar to view the comparison chart.")
else:
    st.subheader(f"Timeline Progression: {selected_short}")
    line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(
        x=alt.X('Date:T', title='Timeline'),
        y=alt.Y('Cumulative:Q', title='Cumulative Actions')
    )
    points = alt.Chart(chart_df).mark_circle(size=110, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
        x='Date:T', y='Cumulative:Q', href='URL:N',
        tooltip=[alt.Tooltip('Date:T', format='%Y-%m-%d'), 'Title:N', 'Active_Categories_Short:N']
    )
    st.altair_chart((line + points).interactive(), use_container_width=True)

st.caption("💡 **Export Tip:** Hover over the chart and click the **'...'** (three dots) in the top right to download as PNG/SVG for sharing.")

# 8. Category Volume Bar Chart (Safety Check Added)
st.divider()
st.subheader("Action Volume by Category")
cat_counts = []
for long, short in CATEGORY_MAP.items():
    if comparison_mode and short not in selected_compare: continue
    count = (display_df[long].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum() if not comparison_mode else len(df_comp[df_comp['Category_Short'] == short])
    if count > 0: cat_counts.append({'Category': short, 'Count': count})

# FIX: Check if cat_counts is empty before creating/sorting dataframe
if cat_counts:
    bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)
    bar_chart = alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
        x=alt.X('Count:Q', title='Number of Actions'),
        y=alt.Y('Category:N', sort='-x', title=None, axis=alt.Axis(labelLimit=350)),
        tooltip=['Category:N', 'Count:Q']
    ).properties(height=len(bar_df) * 40 + 50)
    st.altair_chart(bar_chart, use_container_width=True)
else:
    st.info("No data available for the current selection.")

with st.expander("📖 Category Glossary & Multi-Tagging Logic"):
    st.markdown("### Category Glossary")
    st.table(pd.DataFrame({"Short Name": list(SHORT_TO_LONG.keys()), "Full Official Definition": list(SHORT_TO_LONG.values())}))
    st.write("**Pervasive Complexity:** One action often triggers multiple flags. Filtering for one category shows its co-occurrence with others.")

# 9. Latest Actions
st.divider()
st.subheader(f"📍 Latest Actions: {selected_short}")
if not display_df.empty:
    top_5 = display_df.head(5)
    for i, row in top_5.iterrows():
        with st.expander(f"📅 {row['Date'].strftime('%Y-%m-%d')} — {row['Title'][:90]}..."):
            st.write(f"**Description:** {row['Title']}")
            st.link_button("🚀 Open Source", row['URL'])
else:
    st.write("No actions to display.")

# 10. Data Vault & Export
st.divider()
st.subheader("Data Vault")

if not display_df.empty:
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Current View as CSV",
        data=csv,
        file_name=f'trump_actions_{selected_short.replace(" ", "_")}.csv',
        mime='text/csv',
    )

search = st.text_input("Search descriptions...", placeholder="Type here...")
filtered_table = display_df
if search and not display_df.empty:
    filtered_table = display_df[display_df['Title'].str.contains(search, case=False, na=False)]

if not filtered_table.empty:
    st.dataframe(filtered_table[['Date', 'Title', 'URL']], use_container_width=True, hide_index=True)
else:
    st.write("No data found.")

st.caption("Dashboard by Celine Nadeau aka bananasutra. Last updated Mar, 1st 2026. CC BY 4.0.")
