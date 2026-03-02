import streamlit as st
import pandas as pd
import altair as alt

# 1. Page Config
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas: Trump Actions Tracker", 
    layout="wide", 
    initial_sidebar_state="collapsed" # Better for mobile start
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
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df, cat_cols

df, cat_cols = load_data()

# 3. Sidebar Navigation
st.sidebar.title("Navigation & Filters")
selected_cat = st.sidebar.selectbox("Filter by Policy Category", ["All Actions"] + cat_cols)

# 4. Filtering Logic
if selected_cat != "All Actions":
    display_df = df[df[selected_cat].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
else:
    display_df = df.copy()

filtered_daily = display_df.groupby('Date')['Index'].nunique().reset_index().sort_values('Date')
filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
display_df = display_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 5. Header
st.title("🙊 U.S. Democracy Gone Bananas: Trump Actions Tracker")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0")

# 6. Progression Graph (Mobile Optimized)
st.subheader(f"Timeline Progression: {selected_cat}")

# Detection for small screens (approximate via container width logic or sidebar)
# Note: Streamlit doesn't have a direct 'is_mobile', but we can optimize the chart for both.
st.caption("💡 **Mobile:** Tap points to see details. **Desktop:** Hover for details, Click for source.")

# We create a Selection object for the chart to handle 'Taps' better on mobile
selection = alt.selection_point(on='click', nearest=True, fields=['Date'], empty=False)

line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=3, interpolate='step-after').encode(
    x=alt.X('Date:T', title='Timeline'),
    y=alt.Y('Cumulative:Q', title='Cumulative Actions')
)

points = alt.Chart(display_df).mark_circle(size=120, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
    x='Date:T',
    y='Cumulative:Q',
    href='URL:N',
    tooltip=[
        alt.Tooltip('Date:T', title='Date', format='%b %d, %Y'),
        alt.Tooltip('Title:N', title='Action'),
        alt.Tooltip('Active_Categories:N', title='Categories')
    ],
    # Add conditional opacity to show what's "tapped" on mobile
    opacity=alt.condition(selection, alt.value(1), alt.value(0.6))
).add_params(selection)

st.altair_chart((line + points).interactive(), use_container_width=True)

st.caption("⚠️ **Note on Links:** Clicking points opens the source in a new window. Some sites (Guardian/NYT) may block direct opening; if so, use the Data Vault links below.")

# 7. Category Bar Graph (Responsive)
st.divider()
st.subheader("Action Volume by Category")

cat_counts = []
for col in cat_cols:
    count = (display_df[col].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    if count > 0:
        cat_counts.append({'Category': col, 'Count': count})
bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)

# VIBE FIX: On mobile, we use a much larger labelLimit and dynamic height
# or offer a simple Table view if the chart is too cramped.
bar_chart = alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
    x=alt.X('Count:Q', title='Actions'),
    y=alt.Y('Category:N', sort='-x', title=None, 
           axis=alt.Axis(labelLimit=200, labelFontSize=10, labelPadding=10)),
    tooltip=['Category:N', 'Count:Q']
).properties(height=alt.Step(30)) # This makes the chart grow vertically with more data

st.altair_chart(bar_chart, use_container_width=True)

# 8. Dynamic Insights
st.divider()
st.subheader("📊 Data Insights")
top_cats = bar_df.head(2)['Category'].tolist() if len(bar_df) > 1 else ["N/A", "N/A"]
avg_c = df['Cat_Count'].mean()

st.write(f"**Dominant Themes:** {top_cats[0]} and {top_cats[1]}.")
st.write(f"**Classification Complexity:** Each action averages **{avg_c:.1f}** flags, showing how single policies often cross multiple democratic norms.")

# 9. Data Vault (The best mobile experience)
st.divider()
st.subheader("Data Vault")
st.caption("Searchable table below is optimized for mobile scrolling.")
search_query = st.text_input("Search titles...", placeholder="Type here...")

filtered_table = display_df
if search_query:
    filtered_table = display_df[display_df['Title'].str.contains(search_query, case=False, na=False)]

st.dataframe(
    filtered_table[['Date', 'Title', 'URL']], 
    column_config={"URL": st.column_config.LinkColumn("Source"), "Date": st.column_config.DateColumn("Date")},
    use_container_width=True, hide_index=True
)

st.caption("Dashboard by bananasutra. Updated Mar 2026.")
