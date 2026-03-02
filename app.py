import streamlit as st
import pandas as pd
import altair as alt

# 1. Page Config
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas: Trump Actions Tracker", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. Load and Clean Data
@st.cache_data
def load_data():
    # Skipping metadata lines to get to the data
    df = pd.read_csv('trump-actions.csv', skiprows=2)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    # Category columns are everything after 'URL'
    cat_cols = df.columns[4:].tolist()
    
    # Tooltip helper for categories
    def get_active_cats(row):
        return ", ".join([col for col in cat_cols if str(row[col]).strip().lower() == 'yes'])
    
    df['Active_Categories'] = df.apply(get_active_cats, axis=1)
    
    # Calculate categories per action for insights
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    
    return df, cat_cols

df, cat_cols = load_data()

# 3. Sidebar Navigation
st.sidebar.title("Navigation & Filters")
st.sidebar.info("To reset the view, select 'All Actions' from the dropdown.")

selected_cat = st.sidebar.selectbox(
    "Filter by Policy Category", 
    ["All Actions"] + cat_cols,
    help="Note: Categories match the official tracker classification headers."
)

# 4. Filtering Logic
if selected_cat != "All Actions":
    display_df = df[df[selected_cat].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
else:
    display_df = df.copy()

# Dynamic Cumulative Calculation for the filtered view
filtered_daily = display_df.groupby('Date')['Index'].nunique().reset_index().sort_values('Date')
filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
display_df = display_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 5. Header & Intro
st.title("🙊 U.S. Democracy Gone Bananas: Trump Actions Tracker")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0 License")
st.info("**Context:** Documenting actions, statements, and plans of the Trump administration that echo authoritarian regimes and threaten American democracy, since Jan 2025.")

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Actions in View", len(display_df))
col2.metric("Total in Database", len(df))
col3.metric("Latest Entry", df['Date'].max().strftime('%Y-%m-%d'))

# 6. Progression Graph (With Click Function & Smaller Notes)
st.subheader(f"Timeline Progression: {selected_cat}")

# Link usage and browser notes in smaller font
st.caption("💡 **Hover** to see details. **Click** any point to open source URL in a new window.")
st.caption("⚠️ **Note on Links:** Source URLs will open in a new window. Some sites (like *The Guardian*, the *NY Times*, *NBC News*, and *AP News*) block links from external apps.")

line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(
    x=alt.X('Date:T', title='Timeline'),
    y=alt.Y('Cumulative:Q', title='Cumulative Actions')
)

points = alt.Chart(display_df).mark_circle(size=100, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
    x='Date:T',
    y='Cumulative:Q',
    href='URL:N',
    tooltip=[
        alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
        alt.Tooltip('Title:N', title='Action'),
        alt.Tooltip('Active_Categories:N', title='Categories'),
        alt.Tooltip('URL:N', title='Source URL (Click to open)')
    ]
)

st.altair_chart((line + points).interactive(), use_container_width=True)

# 7. Category Bar Graph
st.divider()
st.subheader("Action Volume by Category")

if selected_cat != "All Actions":
    st.write(f"Showing overlaps within the **'{selected_cat}'** subset.")

cat_counts = []
for col in cat_cols:
    count = (display_df[col].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    if count > 0:
        cat_counts.append({'Category': col, 'Count': count})

bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)

bar_chart = alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
    x=alt.X('Count:Q', title='Number of Actions'),
    y=alt.Y('Category:N', sort='-x', title=None, axis=alt.Axis(labelLimit=400, labelFontSize=12)),
    tooltip=['Category:N', 'Count:Q']
).properties(height=450)

st.altair_chart(bar_chart, use_container_width=True)

# 8. Dynamic Insights Section
st.divider()
st.subheader("📊 Data Insights (Feb 2025 – Feb 2026)")

# Calculate dominant categories
top_cats = bar_df.head(2)['Category'].tolist()
avg_cats = df['Cat_Count'].mean()

insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.write("### Volume & Progression")
    st.write(f"Since Jan 2025, the tracker has logged **{len(df)} actions**. There has been a steady, near-linear increase in actions, with notable spikes observed around the start of 2025 and again in early 2026.")
    
    st.write("### Dominant Categories")
    st.write(f"The most frequent classifications are **'{top_cats[0]}'** and **'{top_cats[1]}'**, which dominate the current policy landscape according to the data.")

with insight_col2:
    st.write("### Diversity of Action")
    st.write(f"Many individual actions are multi-classified. On average, each action triggers **{avg_cats:.1f} category flags**, indicating that policy shifts often impact multiple institutional norms simultaneously.")
    
    st.write("### Policy Focus")
    st.write("The distribution shows a high concentration of actions targeting federal institutional strength and democratic norms, reflecting the primary focus of the tracking project.")

# 9. Data Vault
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

st.caption("Dashboard created by bananasutra. Updated via GitHub Integration. CC BY 4.0 License.")
