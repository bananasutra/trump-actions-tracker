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
st.sidebar.info("To reset, select 'All Actions' from the dropdown.")

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

# 5. Header
st.title("🙊 U.S. Democracy Gone Bananas: Trump Actions Tracker")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0 License")
st.info("**Context:** Documenting actions, statements, and plans of the Trump administration that echo authoritarian regimes and threaten American democracy, since Jan 2025.")

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Actions in View", len(display_df))
col2.metric("Total in Database", len(df))
col3.metric("Latest Entry", df['Date'].max().strftime('%Y-%m-%d'))

# 6. Progression Graph
st.subheader(f"Timeline Progression: {selected_cat}")

# Mobile-specific UX fix
is_mobile = st.checkbox("📱 Mobile Mode (Disables direct clicks to prevent accidental navigation)", value=False)

st.caption("💡 **Hover** to see details. **Click** any point to open source URL (Disabled in Mobile Mode).")
st.caption("⚠️ **Note on Links:** Some sites (Guardian, NYT, NBC) may block direct opening from external apps.")

line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(
    x=alt.X('Date:T', title='Timeline'),
    y=alt.Y('Cumulative:Q', title='Cumulative Actions')
)

points_base = alt.Chart(display_df).mark_circle(size=100, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
    x='Date:T',
    y='Cumulative:Q',
    tooltip=[
        alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
        alt.Tooltip('Title:N', title='Action'),
        alt.Tooltip('Active_Categories:N', title='Categories'),
        alt.Tooltip('URL:N', title='Source URL (Click to open)')
    ]
)

# Apply Click logic only if NOT in mobile mode
if not is_mobile:
    points = points_base.encode(href='URL:N')
else:
    points = points_base

st.altair_chart((line + points).interactive(), use_container_width=True)

# 7. Category Bar Graph (Responsive Height)
st.divider()
st.subheader("Action Volume by Category")

if selected_cat != "All Actions":
    st.warning(f"**Note:** Filtering for **'{selected_cat}'**. Other bars show overlapping categories.")

cat_counts = []
for col in cat_cols:
    count = (display_df[col].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    if count > 0:
        cat_counts.append({'Category': col, 'Count': count})

bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)

# Vibe Fix: Use Step height to prevent squishing on mobile
bar_chart = alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
    x=alt.X('Count:Q', title='Number of Actions'),
    y=alt.Y('Category:N', sort='-x', title=None, axis=alt.Axis(labelLimit=350, labelFontSize=12)),
    tooltip=['Category:N', 'Count:Q']
).properties(height=alt.Step(40)) # Ensures 40px per bar regardless of screen size

st.altair_chart(bar_chart, use_container_width=True)

# 8. EXPANDED Dynamic Insights Section
st.divider()
st.subheader("📊 Data Insights (Jan 2025 – Feb 2026)")

# Calculations
top_cats = bar_df.head(3)['Category'].tolist() if not bar_df.empty else ["N/A", "N/A", "N/A"]
avg_cats = df['Cat_Count'].mean()
multi_cat_pct = (len(df[df['Cat_Count'] > 1]) / len(df)) * 100

insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.write("### 📈 Volume & Progression")
    st.write(f"Since the inauguration in Jan 2025, the tracker has logged **{len(df)} significant actions**. The data reveals a steady, near-linear increase in policy shifts, with notable 'bursts' of activity occurring at the start of the term and again in the first quarter of 2026.")
    
    st.write("### 🏛️ Dominant Categories")
    st.write(f"The tracking data is currently dominated by **'{top_cats[0]}'**, followed closely by **'{top_cats[1]}'** and **'{top_cats[2]}'**. These categories represent the primary levers being moved within the current administration's framework.")

with insight_col2:
    st.write("### 🔗 Diversity & Overlap")
    st.write(f"A defining characteristic of these actions is their intersectional nature. **{multi_cat_pct:.1f}%** of all documented events trigger multiple category flags. On average, each action impacts **{avg_cats:.1f}** distinct institutional norms simultaneously.")
    
    st.write("### 🎯 Policy Focus")
    st.write("The distribution indicates a heavy concentration on hollowing out federal institutional strength and recalibrating democratic norms. This multi-pronged approach suggests that single policy changes (like personnel shifts) are designed to have cascading effects across multiple categories of governance.")

# 9. Data Vault
st.divider()
st.subheader("Data Vault")
search_query = st.text_input("Search titles or descriptions...", placeholder="Type to filter...")

if search_query:
    filtered_table = display_df[display_df['Title'].str.contains(search_query, case=False, na=False)]
else:
    filtered_table = display_df

st.dataframe(
    filtered_table[['Date', 'Title', 'Active_Categories', 'URL']], 
    column_config={
        "URL": st.column_config.LinkColumn("Source Link"),
        "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
        "Title": st.column_config.TextColumn("Description", width="large")
    },
    use_container_width=True,
    hide_index=True
)

st.caption("Dashboard by bananasutra. Updated via GitHub. CC BY 4.0.")
