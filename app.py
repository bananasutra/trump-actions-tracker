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

# 2. Advanced Mapping Strategy
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
    # Attempting to load the newest CSV first
    files_to_try = ['trump-actions-3-1-26.csv', 'trump-actions.csv']
    df = None
    for file in files_to_try:
        try:
            df = pd.read_csv(file, skiprows=2)
            break
        except FileNotFoundError:
            continue
    
    if df is None:
        st.error("Data file not found. Please ensure 'trump-actions-3-1-26.csv' is in your repository.")
        return None, None

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=False)
    
    cat_cols = df.columns[4:].tolist()
    
    def get_active_long(row):
        return ", ".join([col for col in cat_cols if str(row[col]).strip().lower() == 'yes'])
    
    def get_active_short(row):
        return ", ".join([CATEGORY_MAP.get(col, col) for col in cat_cols if str(row[col]).strip().lower() == 'yes'])
    
    df['Active_Categories_Full'] = df.apply(get_active_long, axis=1)
    df['Active_Categories_Short'] = df.apply(get_active_short, axis=1)
    
    def extract_domain(url):
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '')
        except:
            return "Other"
    df['Source_Domain'] = df['URL'].apply(extract_domain)
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    
    return df, cat_cols

df, cat_cols = load_data()

# 4. Sidebar Navigation
st.sidebar.title("Navigation & Filters")
st.sidebar.info("To reset the view, select 'All Actions' from the dropdown.")

selected_short = st.sidebar.selectbox(
    "Filter by Policy Area", 
    ["All Actions"] + list(SHORT_TO_LONG.keys()),
    help="Select a category to filter the entire dashboard."
)

# 5. Filtering Logic
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
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0 License")
st.info("**Context:** Documenting actions, statements, and plans of the Trump administration that echo authoritarian regimes and threaten American democracy, since Jan 2025.")

# Metrics Row
col1, col2, col3 = st.columns(3)
col1.metric("Actions in View", len(display_df))
col2.metric("Total in Database", len(df))
col3.metric("Latest Entry", df['Date'].max().strftime('%Y-%m-%d'))

# 7. Progression Graph
st.subheader(f"Timeline Progression: {selected_short}")

line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(
    x=alt.X('Date:T', title='Timeline'),
    y=alt.Y('Cumulative:Q', title='Cumulative Actions')
)

points = alt.Chart(chart_df).mark_circle(size=110, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
    x=alt.X('Date:T', title='Date'),
    y=alt.Y('Cumulative:Q', title='Progression'),
    href='URL:N',
    tooltip=[
        alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
        alt.Tooltip('Title:N', title='Action'),
        alt.Tooltip('Active_Categories_Short:N', title='Themes'),
        alt.Tooltip('Active_Categories_Full:N', title='Official Classifications'),
        alt.Tooltip('URL:N', title='Source URL (Click to open)')
    ]
)

# 7b. GLOBAL CONFIG (The Fix for 'LayerChart' error)
# We apply configuration to the combined chart object
final_progression_chart = (line + points).interactive().configure_view(
    stroke=None
).configure_axis(
    grid=False
).configure_legend(
    orient='bottom'
).configure_view(
    fill='#f9f9f9'
)

# Streamlit-specific: We can't always use configure_tooltip on layered charts, 
# so we ensure the chart renders and use standard styling.
st.altair_chart(final_progression_chart, use_container_width=True)

st.caption("💡 **Desktop:** Hover to see details. **Click** any point to open source URL in a new window.")
st.caption("⚠️ **Note on Links:** Many sites (like *The Guardian*, *NYT*, *NBC News*, and *AP News*) block direct opening from external apps. You can search action in Data Vault to use direct link.")

# 8. Category Summary
st.divider()
st.subheader("Action Volume by Category")

cat_counts = []
for long, short in CATEGORY_MAP.items():
    count = (display_df[long].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    if count > 0:
        cat_counts.append({'Category': short, 'Count': count})

bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)
dynamic_height = len(bar_df) * 40 + 50

bar_chart = alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
    x=alt.X('Count:Q', title='Number of Actions'),
    y=alt.Y('Category:N', sort='-x', title=None, axis=alt.Axis(labelLimit=350, labelFontSize=12)),
    tooltip=['Category:N', 'Count:Q']
).properties(height=dynamic_height)

st.altair_chart(bar_chart, use_container_width=True)

# 9. LATEST ACTIONS HIGHLIGHT
st.divider()
st.subheader(f"📍 Latest Actions: {selected_short}")
st.markdown(f"*The 5 most recent entries documented under the **{selected_short}** category.*")

top_5 = display_df.head(5)
for i, row in top_5.iterrows():
    with st.expander(f"📅 {row['Date'].strftime('%Y-%m-%d')} — {row['Title'][:90]}..."):
        st.write(f"**Full Description:** {row['Title']}")
        st.write(f"**Themes:** {row['Active_Categories_Short']}")
        st.link_button("🚀 Open Original Source", row['URL'])

# 10. Analytical Insights
st.divider()
st.subheader("📊 Data Insights (Jan 2025 – Feb 2026)")

top_cats_list = bar_df.head(2)['Category'].tolist() if not bar_df.empty else ["N/A", "N/A"]
avg_cats = df['Cat_Count'].mean()
multi_cat_pct = (len(df[df['Cat_Count'] > 1]) / len(df)) * 100
top_source = df['Source_Domain'].value_counts().idxmax()

col_i1, col_i2 = st.columns(2)
with col_i1:
    st.write("### 📈 Volume & Progression")
    st.write(f"Since Jan 2025, the tracker has logged **{len(df)} significant actions**. The data reveals a steady, near-linear increase in policy shifts, with notable bursts observed around the start of the term and the first quarter of 2026.")
    st.write("### 🏛️ Dominant Themes")
    st.write(f"The tracking data is currently dominated by **'{top_cats_list[0]}'**, followed closely by **'{top_cats_list[1]}'**.")

with col_i2:
    st.write("### 🔗 Diversity & Impact")
    st.write(f"Complexity is high: **{multi_cat_pct:.1f}%** of all documented events trigger multiple category flags. On average, each action impacts **{avg_cats:.1f}** distinct institutional norms simultaneously.")
    st.write("### 📰 Source Documentation")
    st.write(f"The most frequent primary documentation source in the dataset is **{top_source}**, highlighting the role of investigative journalism in tracking these shifts.")

# 11. Data Vault
st.divider()
st.subheader("Data Vault")
search_query = st.text_input("Search descriptions...", placeholder="Type here to filter table...")

filtered_table = display_df
if search_query:
    filtered_table = display_df[display_df['Title'].str.contains(search_query, case=False, na=False)]

st.dataframe(
    filtered_table[['Date', 'Title', 'Active_Categories_Short', 'URL']], 
    column_config={
        "URL": st.column_config.LinkColumn("Source Link"),
        "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
        "Title": st.column_config.TextColumn("Description", width="large"),
        "Active_Categories_Short": st.column_config.TextColumn("Themes")
    },
    use_container_width=True,
    hide_index=True
)

st.caption("Dashboard created by bananasutra. Updated via GitHub. CC BY 4.0 License.")
