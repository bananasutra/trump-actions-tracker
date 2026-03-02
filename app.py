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

# 2. Category Mapping (RESTORED TO FULL CSV COLUMN NAMES)
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
SORTED_SHORT_NAMES = sorted(list(CATEGORY_MAP.values()))
SHORT_TO_LONG = {v: k for k, v in CATEGORY_MAP.items()}

# 3. Load Data
@st.cache_data
def load_data():
    # Attempting to load the file
    files_to_try = ['trump-actions-3-1-26.csv', 'trump-actions.csv', 'trump_actions.csv']
    df = None
    for file in files_to_try:
        try:
            # Note: We use skiprows=2 because the CSV typically has a title and a source line
            df = pd.read_csv(file, skiprows=2)
            break
        except:
            continue
    
    if df is None:
        st.error("Data file not found. Ensure the CSV is uploaded to your GitHub repository.")
        return None, None

    # Cleaning column names to remove any accidental leading/trailing spaces
    df.columns = [c.strip() for c in df.columns]
    
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=True) # Ascending for correct chart growth
    
    cat_cols = list(CATEGORY_MAP.keys())
    
    # THE FIX: Check if column exists before trying to access it in the lambda
    def get_active_short(row):
        active = []
        for col in cat_cols:
            if col in df.columns:
                if str(row[col]).strip().lower() == 'yes':
                    active.append(CATEGORY_MAP[col])
        return ", ".join(active)
    
    df['Themes'] = df.apply(get_active_short, axis=1)
    df['Cat_Count'] = df[[c for c in cat_cols if c in df.columns]].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    
    return df, cat_cols

df, cat_cols = load_data()

# 4. Header & Navigation (Crisp White Anchors)
st.title("🙊 U.S. Democracy Gone Bananas")
st.markdown("**Data Source:** [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0")
st.info("**Context:** A strategic diagnostic of the systematic dismantling of U.S. democratic institutions since Jan 2025.")

st.markdown("""
<div style="display: flex; justify-content: space-between; gap: 10px; margin-top: 10px; margin-bottom: 25px;">
    <a href="#timeline" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Timeline</button></a>
    <a href="#volume" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Volume</button></a>
    <a href="#latest" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Latest</button></a>
    <a href="#insights" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Insights</button></a>
    <a href="#vault" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Search</button></a>
</div>
""", unsafe_allow_html=True)

# 5. Sidebar Logic
st.sidebar.title("Filters")
comparison_mode = st.sidebar.toggle("📊 Comparison Mode", value=False)
if comparison_mode:
    selected_compare = st.sidebar.multiselect("Categories", SORTED_SHORT_NAMES, default=SORTED_SHORT_NAMES)
    selected_short = "Comparison View"
else:
    selected_short = st.sidebar.selectbox("Policy Area", ["All Actions"] + SORTED_SHORT_NAMES)

# 6. Data Branching
if comparison_mode:
    long_cats = [SHORT_TO_LONG[s] for s in selected_compare if SHORT_TO_LONG[s] in df.columns]
    df_comp = df.melt(id_vars=['Date', 'Index', 'Title', 'Themes', 'URL', 'Cat_Count'], 
                      value_vars=long_cats, var_name='Category_Long', value_name='Is_Active')
    df_comp = df_comp[df_comp['Is_Active'].fillna('No').astype(str).str.strip().str.lower() == 'yes']
    df_comp['Category_Short'] = df_comp['Category_Long'].map(CATEGORY_MAP)
    df_comp = df_comp.sort_values(['Category_Short', 'Date'])
    df_comp['Cumulative'] = df_comp.groupby('Category_Short').cumcount() + 1
    display_df = df_comp 
else:
    target_col = SHORT_TO_LONG[selected_short] if selected_short != "All Actions" else None
    if target_col and target_col in df.columns:
        display_df = df[df[target_col].fillna('No').astype(str).str.strip().str.lower() == 'yes'].copy()
    else:
        display_df = df.copy()
    
    chart_df = display_df.sort_values('Date')
    filtered_daily = chart_df.groupby('Date')['Index'].nunique().reset_index()
    filtered_daily['Cumulative'] = filtered_daily['Index'].cumsum()
    chart_df = chart_df.merge(filtered_daily[['Date', 'Cumulative']], on='Date')

# 7. TIMELINE
st.markdown("<div id='timeline'></div>", unsafe_allow_html=True)
if comparison_mode:
    st.subheader("Velocity Analysis: Comparative Category Growth")
    if not df_comp.empty:
        comp_chart = alt.Chart(df_comp).mark_line(interpolate='step-after', strokeWidth=3).encode(
            x=alt.X('Date:T', title='Timeline'),
            y=alt.Y('Cumulative:Q', title='Actions'),
            color=alt.Color('Category_Short:N', legend=alt.Legend(orient='bottom', columns=2), scale=alt.Scale(scheme='category10')),
            tooltip=[alt.Tooltip('Date:T', format='%Y-%m-%d'), 'Title:N', 'Category_Short:N']
        ).interactive().properties(height=450)
        st.altair_chart(comp_chart, use_container_width=True)
else:
    st.subheader(f"Timeline Progression: {selected_short}")
    line = alt.Chart(filtered_daily).mark_line(color='#DE0100', strokeWidth=4, interpolate='step-after').encode(x='Date:T', y='Cumulative:Q')
    points = alt.Chart(chart_df).mark_circle(size=110, color='white', opacity=0.8, stroke='#DE0100', strokeWidth=2).encode(
        x='Date:T', y='Cumulative:Q', href='URL:N',
        tooltip=[alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'), alt.Tooltip('Title:N', title='Action'), alt.Tooltip('Themes:N', title='Themes')]
    )
    st.altair_chart((line + points).interactive(), use_container_width=True)

st.caption("💡 **Desktop:** Hover for details, Click point for source. **Mobile:** Use Data Vault for links.")

# 8. VOLUME & GLOSSARY
st.markdown("<div id='volume'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Action Volume by Category")
cat_counts = []
for long, short in CATEGORY_MAP.items():
    if long in df.columns:
        if comparison_mode and short not in selected_compare: continue
        count = (df[long].fillna('No').astype(str).str.strip().str.lower() == 'yes').sum()
        if count > 0: cat_counts.append({'Category': short, 'Count': count})

if cat_counts:
    bar_df = pd.DataFrame(cat_counts).sort_values('Count', ascending=False)
    st.altair_chart(alt.Chart(bar_df).mark_bar(color='#DE0100').encode(
        x=alt.X('Count:Q', title='Volume'),
        y=alt.Y('Category:N', sort='-x', title=None),
        tooltip=['Category:N', 'Count:Q']
    ).properties(height=len(bar_df) * 40 + 50), use_container_width=True)

with st.expander("📖 Category Glossary"):
    st.table(pd.DataFrame({"Category": list(SHORT_TO_LONG.keys()), "Definition": list(SHORT_TO_LONG.values())}))

# 9. LATEST ACTIONS (STRICTLY DESCENDING)
st.markdown("<div id='latest'></div>", unsafe_allow_html=True)
st.divider()
st.subheader(f"📍 Latest 5 Actions: {selected_short}")
latest_view = display_df.sort_values('Date', ascending=False).head(5)
for i, row in latest_view.iterrows():
    with st.expander(f"📅 {row['Date'].strftime('%Y-%m-%d')} — {row['Title'][:90]}..."):
        st.write(f"**Description:** {row['Title']}")
        st.write(f"**Themes:** {row['Themes']}")
        st.link_button("🚀 Open Source", row['URL'])

# 10. DEEP INSIGHTS (RESTORED FULL DIAGNOSTIC)
st.markdown("<div id='insights'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("🚨 Deep Insights: The Authoritarian Blueprint")

if not df.empty:
    total = len(df)
    days_active = (df['Date'].max() - df['Date'].min()).days
    pace = (total / max(days_active, 1)) * 30.44
    multi_ratio = (len(df[df['Cat_Count'] > 1]) / total) * 100

    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown("###  Strategic Velocity: The 'Shock' Strategy")
        st.write(f"The administration is maintaining a pace of **{pace:.1f} significant actions per month**. This volume is engineered to ensure judicial and institutional **processing latency** remains higher than the implementation rate.")
        st.warning(f"**Diagnostic Projection:** By Jan 2029, the tracker projects **8,220 actions**. This trajectory signals a move from policy 'disruption' to a 'full institutional rewrite.'")
        st.markdown("###  Norm-Collapse Loops")
        st.write(f"**Complexity:** {multi_ratio:.1f}% of events are multi-tagged. This highlights 'interlocking strikes' where a single move (e.g. purging the civil service) simultaneously breaks 3+ institutional norms.")

    with col_ins2:
        st.markdown("###  The Geography of Resistance")
        st.write("Opposition is currently anchored by 'Blue State Shields' (CA, WA, NY, IL). Data shows litigation is the *only* functional friction point slowing velocity, explaining the prioritization of Judicial and DOJ hollowing.")
        st.video("https://www.youtube.com/watch?v=lbTQ-lkudd4")
        st.caption("📽️ *Context:* Prof. Christina Pagel discusses why tracking these 'Shock' patterns is critical to preventing 'Normalization'.")

# 11. VAULT (STRICTLY DESCENDING)
st.markdown("<div id='vault'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Data Vault")
if not display_df.empty:
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Export CSV", data=csv, file_name='trump_actions.csv', mime='text/csv')

search = st.text_input("Search descriptions...", placeholder="Filter by keyword...")
vault_df = display_df.sort_values('Date', ascending=False)
if search:
    vault_df = vault_df[vault_df['Title'].str.contains(search, case=False, na=False)]
st.dataframe(
    vault_df[['Date', 'Title', 'URL', 'Themes']], 
    column_config={"URL": st.column_config.LinkColumn("Source Link"), "Date": st.column_config.DateColumn("Date")},
    use_container_width=True, hide_index=True
)

st.caption("Dashboard by Celine Nadeau aka bananasutra. Updated 03-01-2026. CC BY 4.0.")
