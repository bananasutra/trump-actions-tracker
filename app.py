import streamlit as st
import pandas as pd
import altair as alt
from urllib.parse import urlparse

# 1. PAGE CONFIG & SEO
st.set_page_config(
    page_title="U.S. Democracy Gone Bananas", 
    page_icon="🍌", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# SEO Workaround for Social Media Previews
st.markdown("""
    <head>
    <meta property="og:title" content="U.S. Democracy Gone Bananas: Trump Actions Tracker" />
    <meta property="og:description" content="A strategic diagnostic of systemic democratic erosion in the U.S. since Jan 2025." />
    <meta name="twitter:card" content="summary_large_image">
    </head>
    """, unsafe_allow_html=True)

# 2. UPDATED GLOSSARY DATA
GLOSSARY_DATA = {
    "Aggressive Foreign Policy & Global Destabilisation": "Threatening allies, using tariffs to extract concessions, withdrawing from international treaties (like the WHO or Paris Climate Treaty), and aligning with anti-democratic rivals.",
    "Anti-immigrant or Militarised Nationalism": "Using language that demonizes immigrants, deploying military-type enforcement (like the National Guard) within the U.S., and expanding domestic surveillance.",
    "Attacking Universities, Schools, Museums, Culture": "Undermining the independence of universities, restricting K-12 education topics, and targeting information within museums and national parks.",
    "Control of Science to Align with State Ideology": "Restricting scientific research (e.g., on climate change), expanding drilling against environmental evidence, and attacking public health through vaccine restrictions or funding cuts.",
    "Controlling Information including Spreading Misinformation": "Manufacturing evidence to support state policy, restricting access to contradicting evidence, and spreading propaganda.",
    "Corruption and Enrichment": "Actions that directly enrich the president, his family, or his cabinet, or that trade political favors for wealth.",
    "Dismantling Social Protections & Rights": "Removing civil rights from marginalized groups like LGBTQ+ communities and immigrants, attacking diversity and inclusion (DEI) initiatives, and contravening due process rights.",
    "Hollowing State / Weakening Federal Institutions": "Dismantling federal institutions, mass firings of staff, or politicizing government roles.",
    "Suppressing Dissent / Weaponising State Power": "Punishing opponents, instituting loyalty tests, and weaponizing executive power or legal action against rivals, critics, and perceived enemy states or cities.",
    "Violating Democratic Norms / Rule of Law": "Actions that weaken checks and balances, restrict press freedom, undermine states' rights, violate court orders or the Constitution, or reduce the independence of oversight bodies."
}

# 3. CATEGORY MAPPING
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

# 4. LOAD DATA
@st.cache_data
def load_data():
    files_to_try = ['trump-actions-3-1-26.csv', 'trump-actions.csv']
    df = None
    for file in files_to_try:
        try:
            df = pd.read_csv(file, skiprows=2)
            break
        except: continue
    if df is None: return None, None

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=True) 
    cat_cols = list(CATEGORY_MAP.keys())
    
    df['Themes_List'] = df.apply(lambda r: ", ".join([CATEGORY_MAP.get(c, c) for c in cat_cols if str(r[c]).strip().lower() == 'yes']), axis=1)
    df['Cat_Count'] = df[cat_cols].apply(lambda x: (x.str.strip().str.lower() == 'yes').sum(), axis=1)
    return df, cat_cols

df, cat_cols = load_data()

# 5. HEADER (REFINED)
st.title("🙊 U.S. Democracy Gone Bananas")
st.markdown("##### Diagnostic of systemic democratic erosion and institutional dismantling since Jan 2025.")
st.info("**Context:** Data Source: [Christina Pagel / Trump Action Tracker Info](https://www.trumpactiontracker.info/) | CC BY 4.0")

# 6. CENTERED HERO STATS (FULL WIDTH & CUSTOM PADDING)
if not df.empty:
    total_actions = len(df)
    days_active = (df['Date'].max() - df['Date'].min()).days
    pace_per_month = (total_actions / max(days_active, 1)) * 30.44
    overlap = (len(df[df['Cat_Count'] > 1]) / total_actions * 100)

    # Custom CSS for Hero Cards
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; gap: 20px; width: 100%; padding: 40px 0; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 250px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">Total Actions Logged</p>
            <h2 style="margin: 0; font-size: 2.5rem; color: #FFFFFF;">{total_actions}</h2>
        </div>
        <div style="flex: 1; min-width: 250px; background: rgba(255, 255, 255, 0.05); border: 1px solid #DE0100; border-radius: 10px; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">Current Velocity</p>
            <h2 style="margin: 0; font-size: 2.5rem; color: #DE0100;">{pace_per_month:.1f} <span style="font-size: 1rem;">/ mo</span></h2>
            <p style="margin: 0; font-size: 0.8rem; color: #DE0100; font-weight: bold;">⚠️ Critical Pace</p>
        </div>
        <div style="flex: 1; min-width: 250px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 25px; text-align: center;">
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">Strategic Overlap</p>
            <h2 style="margin: 0; font-size: 2.5rem; color: #FFFFFF;">{overlap:.1f}%</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 7. STICKY NAVIGATION (SPACED)
st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] > div:has(div.nav-container) {
            position: sticky; top: 2.875rem; z-index: 999; 
            background-color: #0e1117; 
            padding: 20px 0;
        }
    </style>
    <div class="nav-container" style="display: flex; justify-content: space-between; gap: 8px;">
        <a href="#timeline" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Timeline</button></a>
        <a href="#themes" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Themes</button></a>
        <a href="#latest" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Latest</button></a>
        <a href="#insights" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Insights</button></a>
        <a href="#search" style="text-decoration: none; flex: 1;"><button style="width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF; font-weight: bold; cursor: pointer;">Search</button></a>
    </div>
""", unsafe_allow_html=True)

# ... [Sidebar and Data Processing Logic remain unchanged] ...
# [Note: Ensure display_df/chart_df logic from previous stable version is here]

# 9. TIMELINE
st.markdown("<div id='timeline' style='padding-top: 40px;'></div>", unsafe_allow_html=True)
# ... [Graph logic] ...

# 10. THEMES GLOSSARY
st.markdown("<div id='themes' style='padding-top: 40px;'></div>", unsafe_allow_html=True)
st.divider()
st.subheader("Action Volume by Theme")
# ... [Bar chart logic] ...

with st.expander("📖 Themes Glossary"):
    glossary_df = pd.DataFrame(list(GLOSSARY_DATA.items()), columns=["Theme", "Definition"]).sort_values("Theme")
    st.table(glossary_df)

# ... [Rest of Sections: Latest, Insights, Search] ...

# 14. FOOTER
st.caption("Dashboard by Celine Nadeau aka bananasutra. Last updated 03-02-2026. CC BY 4.0.")
