import streamlit as st
import pandas as pd
import altair as alt

# 1. Page Config
st.set_page_config(
    page_title="Trump Action Tracker", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. Load and Clean Data
@st.cache_data
def load_data():
    # Load data skipping the first 2 lines of metadata
    df = pd.read_csv('trump-actions.csv', skiprows=2)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    # Identify category columns (everything after 'URL')
    cat_cols = df.columns[4:].tolist()
    
    # Helper for tooltips to show all tags an action has
    def get_active_cats(row):
        return ", ".join([col for col in cat_cols if str(row[col]).strip().lower() == 'yes'])
    
    df['Active_Categories'] = df.apply(get_active_cats, axis=1)
    return df, cat_cols

df, cat_cols = load_data()

# 3. Sidebar Navigation & Reset
st.sidebar.title("Navigation & Filters")

if st.sidebar.button("🔄 Reset All Filters"):
    st.rerun()

selected_cat = st.sidebar.selectbox(
    "Filter by Policy Category", 
    ["All Actions"] + cat_cols,
    help="Select a specific category to see its progression and related actions."
)

# 4. Bulletproof Filtering Logic
if selected_cat != "All Actions":
    # Ensure empty cells don't break the string comparison
    display_df = df[df[selected_cat].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
else:
    display_df = df.copy()

# 5. Dynamic Cumulative Calculation (Ensures graph updates on filter)
filtered_daily = display_df.groupby('Date')['Index'].nunique().reset_index()
filtered_daily = filtered_daily.sort_values('Date')
filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()

# Merge back to display_df so points align with the new line height
display_df = display_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 6. Header & Intro
st.title("🏛️ Trump Action Tracker")

st.markdown("""
**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0 License
""")

st.info("""
**Context:** Documenting the actions, statements, and plans of President Trump and his administration 
that echo those of authoritarian regimes and may pose a threat to American democracy, since January 2025.
""")

# Metrics Row
col1, col2, col3 = st.columns(3)
col1.metric("Actions in View", len(display_df))
col2.metric("Total in Database", len(df))
col3.metric("Latest Entry", df['Date'].max().strftime('%Y-%m-%d'))

# 7. High-Contrast Chart Overhaul
st.subheader(f"Timeline Progression: {selected_cat}")

# The Bold Red Trendline
line = alt.Chart(filtered_daily).mark_line(
    color='#DE0100', 
    strokeWidth=4, 
    interpolate='step-after'
).encode(
    x=alt.X('Date:T', title='Timeline'),
    y=alt.Y('Cumulative:Q', title='Cumulative Actions')
)

# High-Contrast Points (White fill with Red border for visibility)
points = alt.Chart(display_df).mark_circle(
    size=90, 
    color='white',      # Pop against dark backgrounds
    opacity=0.8, 
    stroke='#DE0100',   # Match the line color
    strokeWidth=2
).encode(
    x='Date:T',
    y='Cumulative:Q',
    tooltip=[
        alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
        alt.Tooltip('Title:N', title='Action'),
        alt.Tooltip('Active_Categories:N', title='Categories'),
        alt.Tooltip('URL:N', title='Source URL')
    ]
)

final_chart = (line + points).interactive().properties(height=500)
st.altair_chart(final_chart, use_container_width=True)

# 8. Searchable Data Vault (Corrected Syntax for st.column_config)
st.subheader("Data Vault")
search_query = st.text_input("Search titles or descriptions...", placeholder="Type to filter table...")

if search_query:
    filtered_table = display_df[display_df['Title'].str.contains(search_query, case=False, na=False)]
else:
    filtered_table = display_df

st.dataframe(
    filtered_table[['Date', 'Title', 'Active_Categories', 'URL']], 
    column_config={
        "URL": st.column_config.LinkColumn("Source Link"),
        "Date": st.column_config.DateColumn("Action Date", format="YYYY-MM-DD"),
        "Title": st.column_config.TextColumn("Action Description", width="large"),
        "Active_Categories": st.column_config.TextColumn("Full Categories")
    },
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.caption("Site deployed via Streamlit Cloud. Data updated to Feb 2026.")
