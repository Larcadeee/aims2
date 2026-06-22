import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

url = "https://docs.google.com/spreadsheets/d/1dAXks7FBX-LN130hMCEWBz5JcSqM1lijBhxAejuNgco/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def load_data():
    df_incident = conn.read(spreadsheet=url, worksheet="1297922850", header=0)
    return df_incident

df = load_data()


aims_page = st.Page(
    page="views/dispatch.py",
    title="Dispatch Page",
    icon=":material/ambulance:",
    default=True,
)


resource_page = st.Page(
    page="views/resource.py",
    title="Resource Page",
    icon=":material/ambulance:",
)

main_page = st.Page(
    page="views/main.py",
    title="Main Page",
    icon=":material/ambulance:",
)

pg = st.navigation(pages=[aims_page, resource_page, main_page ])

pg.run()