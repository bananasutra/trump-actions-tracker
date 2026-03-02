import streamlit as st
import pandas as pd
import altair as alt

# 1. Page Config
st.set_page_config(page_title="Trump Action Tracker", layout="wide", initial_sidebar_state="expanded")

# 2. Load and Clean Data
@st.cache_data
def load_data():
    # Skipping first 2 lines based on your CSV structure
    df = pd.read_csv('trump-actions.csv', skiprows=2)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    # Identify category columns (everything after URL)
    cat_cols = df.columns[4:].tolist()
    
    # Create a helper for tooltips
    def get_active_cats(row):
        return ", ".join([col for col in cat_cols if str(row[col]).strip().lower() == 'yes'])
    
    df['Active_Categories'] = df.apply(get_active_cats, axis=1)
    
    # Calculate Cumulative Count
    daily = df.groupby('Date')['Index'].nunique().reset_index()
    daily['Cumulative'] = daily['Index'].cumsum()
    return df, daily, cat_cols

df, daily, cat_cols = load_data()

# 3. Sidebar Filters
st.sidebar.title("Navigation & Filters")
st.sidebar.markdown("Use these to drill down into specific policy areas.")

selected_cat = st.sidebar.selectbox("Filter by Policy Category", ["All Actions"] + cat_cols)

if selected_cat != "All Actions":
    display_df = df[df[selected_cat].fillna('No').astype(str).str.strip().str.lower() == 'yes']
else:
    display_df = df

# 4. Main Dashboard UI
st.title("🏛️ Trump Action Tracker")
st.markdown(f"**Tracking {len(df)} total actions from Jan 2025 to Feb 2026.**")

# Metric Row
col1, col2 = st.columns(2)
col1.metric("Total Unique Actions", len(df))
col2.metric("Latest Update", df['Date'].max().strftime('%B %d, %Y'))

# 5. The Progression Chart
st.subheader("Action Progression Over Time")

# Base line for the trend
line = alt.Chart(daily).mark_line(
    color='#e63946', 
    strokeWidth=3, 
    interpolate='step-after'
).encode(
    x=alt.X('Date:T', title='Timeline'),
    y=alt.Y('Cumulative:Q', title='Cumulative Actions')
)

# Invisible points for better tooltip interaction
points = alt.Chart(df).mark_circle(size=60, color='#1d3557', opacity=0.4).encode(
    x='Date:T',
    y='Cumulative_Total:Q', # Note: We merge this in load_data if needed, or use daily
    tooltip=[
        alt.Tooltip('Date:T', title='Date'),
        alt.Tooltip('Title:N', title='Action'),
        alt.Tooltip('Active_Categories:N', title='Categories'),
        alt.Tooltip('URL:N', title='Source')
    ]
).transform_lookup(
    lookup='Date',
    from_=alt.LookupData(daily, 'Date', ['Cumulative'])
).encode(y='Cumulative:Q')

st.altair_chart((line + points).interactive(), use_container_width=True)

# 6. Searchable Data Vault
st.subheader("Data Vault")
search_query = st.text_input("Search titles or descriptions...", "")

if search_query:
    filtered_df = display_df[display_df['Title'].str.contains(search_query, case=False)]
else:
    filtered_df = display_df

st.dataframe(
    filtered_df[['Date', 'Title', 'Active_Categories', 'URL']], 
    column_config={
        "URL": st.column_config.LinkColumn("Source Link"),
        "Date": st.column_config.DateColumn("Date")
    },
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.caption("Data Source: Christina Pagel / Trump Action Tracker Info. CC BY 4.0 License.")
