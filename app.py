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
SHORT_TO_LONG = {v: k for k, v in CATEGORY_MAP.items()}

# 3. Load Data
@st.cache_data
def load_data():
    # Try the new file first
    files = ['trump-actions-3-1-26.csv', 'trump-actions.csv']
    df = None
    for f in files:
        try:
            df = pd.read_csv(f, skiprows=2)
            break
        except:
            continue
    
    if df is None: st.error("Data file not found."); return None, None

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=False) # Latest first for the "Highlights"
    cat_cols = df.columns[4:].tolist()
    
    def get_active_short(row):
        return ", ".join([CATEGORY_MAP.get(col, col) for col in cat_cols if str(row[col]).strip().lower() == 'yes'])
    
    df['Themes'] = df.apply(get_active_short, axis=1)
    df['Source_Domain'] = df['URL'].apply(lambda x: urlparse(x).netloc.replace('www.', '') if pd.notnull(x) else "Other")
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    
    return df, cat_cols

df, cat_cols = load_data()

# 4. Sidebar
st.sidebar.title("Navigation")
selected_short = st.sidebar.selectbox("Filter by Policy Area", ["All Actions"] + list(SHORT_TO_LONG.keys()))

# 5. Filter Logic
if selected_short != "All Actions":
    long_name = SHORT_TO_LONG[selected_short]
    display_df = df[df[long_name].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
else:
    display_df = df.copy()

# Sort for chart (needs to be chronological)
chart_df = display_df.sort_values('Date')
filtered_daily = chart_df.groupby('Date')['Index'].nunique().reset_index()
filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
chart_df = chart_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 6. Header
st.title("🙊 U.S. Democracy Gone Bananas")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker](https://www.trumpactiontracker.info/) | CC BY 4.0")

# 7. LATEST ACTIONS HIGHLIGHT (Replaces the confusing 'Lock' section)
st.subheader("📍 Latest Actions in this Category")
top_5 = display_df.head(5)
for i, row in top_5.iterrows():
    with st.expander(f"{row['Date'].strftime('%Y-%m-%d')} - {row['Title'][:80]}..."):
        st.write(f"**Full Action:** {row['Title']}")
        st.write(f"**Themes:** {row['Themes']}")
        st.link_button("View Source", row['URL'])

# 8. Progression Graph
st.subheader(f"Timeline Progression: {selected_short}")
st.caption("💡 **Desktop:** Hover for details, Click for source. **Mobile:** View 'Latest Actions' above or 'Data Vault' below for stable links.")

line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(
    x=alt.X('Date:T', title='Timeline'),
    y=alt.Y('Cumulative:Q', title='Cumulative Actions')
)
points = alt.Chart(chart_df).mark_circle(size=100, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
    x='Date:T',
    y='Cumulative:Q',
    href='URL:N',
    tooltip=[alt.Tooltip('Date:T', title='Date'), alt.Tooltip('Title:N', title='Action'), alt.Tooltip('Themes:N')]
)
st.altair_chart((line + points).interactive(), use_container_width=True)

# 9. Category Bar Chart
st.divider()
st.subheader("Action Volume by Category")
cat_counts = []
for long, short in CATEGORY_MAP.items():
    count = (display_df[long].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
    if count > 0: cat_counts.append({'Category': short, 'Count': count})

bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)
bar_chart = alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
    x=alt.X('Count:Q', title='Actions'),
    y=alt.Y('Category:N', sort='-x', title=None),
    tooltip=['Category:N', 'Count:Q']
).properties(height=len(bar_df) * 40 + 50)
st.altair_chart(bar_chart, use_container_width=True)

# 10. Data Vault
st.divider()
st.subheader("Data Vault")
search = st.text_input("Search descriptions...", placeholder="Type here...")
table_df = display_df if not search else display_df[display_df['Title'].str.contains(search, case=False, na=False)]

st.dataframe(
    table_df[['Date', 'Title', 'Themes', 'URL']], 
    column_config={"URL": st.column_config.LinkColumn("Source"), "Date": st.column_config.DateColumn("Date")},
    use_container_width=True, hide_index=True
)

st.caption("Dashboard by bananasutra. Updated via GitHub. CC BY 4.0.")
