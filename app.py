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
    df = pd.read_csv('trump-actions.csv', skiprows=2)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    cat_cols = df.columns[4:].tolist()
    
    def get_active_cats(row):
        return ", ".join([col for col in cat_cols if str(row[col]).strip().lower() == 'yes'])
    
    df['Active_Categories'] = df.apply(get_active_cats, axis=1)
    return df, cat_cols

df, cat_cols = load_data()

# 3. Sidebar Navigation
st.sidebar.title("Navigation & Filters")
st.sidebar.info("To reset the view, simply select 'All Actions' from the dropdown below.")

selected_cat = st.sidebar.selectbox(
    "Filter by Policy Category", 
    ["All Actions"] + cat_cols
)

# 4. Filtering Logic
if selected_cat != "All Actions":
    display_df = df[df[selected_cat].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
else:
    display_df = df.copy()

filtered_daily = display_df.groupby('Date')['Index'].nunique().reset_index().sort_values('Date')
filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
display_df = display_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 5. Header & Intro
st.title("🏛️ Trump Action Tracker")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0 License")
st.info("**Context:** Documenting the actions, statements, and plans of President Trump and his administration that echo those of authoritarian regimes and may pose a threat to American democracy, since January 2025.")

# Metrics Row
col1, col2, col3 = st.columns(3)
col1.metric("Actions in View", len(display_df))
col2.metric("Total in Database", len(df))
col3.metric("Latest Entry", df['Date'].max().strftime('%Y-%m-%d'))

# 6. Progression Graph
st.subheader(f"Timeline Progression: {selected_cat}")
st.caption("💡 Hover over any point to see the specific action and the 'Category' flags it triggered.")

line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(
    x=alt.X('Date:T', title='Timeline'),
    y=alt.Y('Cumulative:Q', title='Cumulative Actions')
)

points = alt.Chart(display_df).mark_circle(size=90, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
    x='Date:T',
    y='Cumulative:Q',
    tooltip=[
        alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
        alt.Tooltip('Title:N', title='Action'),
        alt.Tooltip('Active_Categories:N', title='Categories'),
        alt.Tooltip('URL:N', title='Source URL')
    ]
)

st.altair_chart((line + points).interactive(), use_container_width=True)

# 7. Readable Category Bar Graph
st.divider()
st.subheader("Action Volume by Category")

cat_counts = []
for col in cat_cols:
    count = (display_df[col].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    cat_counts.append({'Category': col, 'Count': count})

bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)

# Fixed: Using y-axis for Categories with labelLimit to ensure readability
bar_chart = alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
    x=alt.X('Count:Q', title='Number of Actions'),
    y=alt.Y('Category:N', sort='-x', title=None, axis=alt.Axis(labelLimit=300, labelFontSize=12)),
    tooltip=['Category:N', 'Count:Q']
).properties(height=450)

st.altair_chart(bar_chart, use_container_width=True)

# 8. Data Vault
st.divider()
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
        "Title": st.column_config.TextColumn("Action Description", width="large")
    },
    use_container_width=True,
    hide_index=True
)

st.caption("Updated to Feb 2026. Interactive dashboard maintained for research and documentation.")
