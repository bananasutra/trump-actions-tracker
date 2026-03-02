import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Trump Action Tracker", layout="wide")

st.title("📈 Trump Action Tracker (2025-2026)")
st.markdown("Interactive progression of executive and legislative actions.")

# Load data
df = pd.read_csv('trump-actions.csv', skiprows=2)
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date')

# Sidebar Filters
st.sidebar.header("Filters")
categories = df.columns[4:].tolist()
selected_cat = st.sidebar.selectbox("Focus on Category", ["All"] + categories)

# Logic to filter and show categories in tooltip
def get_cats(row):
    return ", ".join([c for c in categories if str(row[c]).strip().lower() == 'yes'])
df['All_Categories'] = df.apply(get_cats, axis=1)

# Chart Logic
daily = df.groupby('Date')['Index'].nunique().reset_index()
daily['Cumulative'] = daily['Index'].cumsum()
df = df.merge(daily[['Date', 'Cumulative']], on='Date')

chart = alt.Chart(df).mark_line(color='#e63946', interpolate='step-after').encode(
    x='Date:T',
    y=alt.Y('Cumulative:Q', title='Total Actions'),
    tooltip=['Date:T', 'Title:N', 'All_Categories:N', 'URL:N']
).interactive().properties(height=500)

st.altair_chart(chart, use_container_width=True)

st.dataframe(df[['Date', 'Title', 'All_Categories', 'URL']], use_container_width=True)
