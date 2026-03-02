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

# 2. Category Mapping (The "Shorter Names" Fix)
# We keep the long names as keys to match the CSV, and short names as values for the chart.
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

# 3. Load and Clean Data
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
    
    def extract_domain(url):
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '')
        except:
            return "Other"
    df['Source_Domain'] = df['URL'].apply(extract_domain)
    
    return df, cat_cols

df, cat_cols = load_data()

# 4. Sidebar Navigation
st.sidebar.title("Navigation & Filters")
# Use the full names for the filter so users see the official definitions
selected_cat = st.sidebar.selectbox("Filter by Policy Category", ["All Actions"] + cat_cols)

# 5. Filtering Logic
if selected_cat != "All Actions":
    display_df = df[df[selected_cat].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
else:
    display_df = df.copy()

filtered_daily = display_df.groupby('Date')['Index'].nunique().reset_index().sort_values('Date')
filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
display_df = display_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 6. Header
st.title("🙊 U.S. Democracy Gone Bananas: Trump Actions Tracker")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0 License")

# 7. Progression Graph
st.subheader(f"Timeline Progression: {selected_cat}")
is_mobile = st.checkbox("📱 Mobile Mode (Tap for details, prevents accidental link clicks)", value=False)
st.caption("💡 **Hover/Tap** points for details. **Click** point for source (unless Mobile Mode is on).")

line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(
    x=alt.X('Date:T', title='Timeline'),
    y=alt.Y('Cumulative:Q', title='Cumulative Actions')
)

points_base = alt.Chart(display_df).mark_circle(size=120, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
    x='Date:T',
    y='Cumulative:Q',
    tooltip=[
        alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
        alt.Tooltip('Title:N', title='Action'),
        alt.Tooltip('Active_Categories:N', title='Categories')
    ]
)
points = points_base.encode(href='URL:N') if not is_mobile else points_base
st.altair_chart((line + points).interactive(), use_container_width=True)

# 8. Category Bar Graph (The "Short Name" Fix)
st.divider()
st.subheader("Action Volume by Category")

cat_counts = []
for col in cat_cols:
    count = (display_df[col].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    if count > 0:
        # Use the Short Name from the map if it exists, otherwise use original
        short_name = CATEGORY_MAP.get(col, col)
        cat_counts.append({'Category': short_name, 'Count': count})

bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)
# Ensure the height is dynamic based on number of bars (40px each)
dynamic_height = len(bar_df) * 40 + 50

bar_chart = alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
    x=alt.X('Count:Q', title='Number of Actions'),
    y=alt.Y('Category:N', sort='-x', title=None, axis=alt.Axis(labelLimit=300, labelFontSize=12)),
    tooltip=['Category:N', 'Count:Q']
).properties(height=dynamic_height)

st.altair_chart(bar_chart, use_container_width=True)

# 9. Dynamic Insights
st.divider()
st.subheader("📊 Data Insights (Jan 2025 – Feb 2026)")

top_cats = bar_df.head(3)['Category'].tolist() if not bar_df.empty else ["N/A"]*3
avg_cats = df['Cat_Count'].mean()
multi_cat_pct = (len(df[df['Cat_Count'] > 1]) / len(df)) * 100
top_source = df['Source_Domain'].value_counts().idxmax()

insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.write("### 📈 Volume & Progression")
    st.write(f"Since Jan 2025, the tracker has logged **{len(df)} actions**. The progression shows a persistent upward trend with escalations correlating to the 2025 inauguration and early 2026 shifts.")
    st.write(f"### 🏛️ Dominant Categories")
    st.write(f"The data is primarily driven by **'{top_cats[0]}'**, followed by **'{top_cats[1]}'**.")

with insight_col2:
    st.write("### 🔗 Diversity & Multi-Tagging")
    st.write(f"Complexity is high: **{multi_cat_pct:.1f}%** of actions trigger multiple categories. On average, each event impacts **{avg_cats:.1f}** different democratic or institutional norms.")
    st.write("### 📰 Source Analysis")
    st.write(f"Documentation relies on diverse reporting. The most frequent primary source domain in the dataset is **{top_source}**.")

# 10. Data Vault
st.divider()
st.subheader("Data Vault")
search_query = st.text_input("Search description...", placeholder="Type to filter table...")
filtered_table = display_df if not search_query else display_df[display_df['Title'].str.contains(search_query, case=False, na=False)]

st.dataframe(
    filtered_table[['Date', 'Title', 'URL']], 
    column_config={"URL": st.column_config.LinkColumn("Source"), "Date": st.column_config.DateColumn("Date")},
    use_container_width=True, hide_index=True
)

st.caption("Dashboard by bananasutra. Updated via GitHub. CC BY 4.0.")
