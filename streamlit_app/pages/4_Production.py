import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient

st.set_page_config(page_title="Production (MongoDB)", layout="wide")

# ---- Mongo connection (from secrets) ----
uri = st.secrets["mongo"]["uri"]
db_name = st.secrets["mongo"]["db"]
col_name = st.secrets["mongo"]["col"]

client = MongoClient(uri)
col = client[db_name][col_name]

# ---- Load data to DataFrame ----
docs = col.find({}, {"_id": 0, "priceArea": 1, "productionGroup": 1, "startTime": 1, "quantityKwh": 1})
df = pd.DataFrame(list(docs))
if df.empty:
    st.warning("No data found in MongoDB collection.")
    st.stop()

# Convert data types
df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
df["quantityKwh"] = pd.to_numeric(df["quantityKwh"], errors="coerce").fillna(0)

# ---- UI Controls ----
st.title("Production Overview (MongoDB Atlas)")
areas = sorted(df["priceArea"].dropna().unique())
area = st.radio("Choose area", areas, horizontal=True)

pie_df = (df[df["priceArea"] == area]
          .groupby("productionGroup", as_index=False)["quantityKwh"].sum())

fig_pie = px.pie(pie_df, names="productionGroup", values="quantityKwh",
                 title=f"Total production — {area}")
st.plotly_chart(fig_pie, use_container_width=True)

months = sorted(df["startTime"].dt.month.unique())
month = st.selectbox("Select month", months)

line_src = df[(df["priceArea"] == area) & (df["startTime"].dt.month == month)]
if line_src.empty:
    st.info("No data for this area and month.")
else:
    line_df = (line_src.groupby(["startTime", "productionGroup"])["quantityKwh"]
               .sum().unstack().fillna(0))
    fig_line = px.line(line_df, title=f"Hourly production — {area}, Month {month:02d}")
    st.plotly_chart(fig_line, use_container_width=True)
