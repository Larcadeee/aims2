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
    title="Dispatch",
    icon=":material/timer:",
)


resource_page = st.Page(
    page="views/resource.py",
    title="Resource",
    icon=":material/ambulance:",
)

main_page = st.Page(
    page="views/main.py",
    title="Main",
    icon=":material/home:",
    default=True,
)

test_page = st.Page(
    page="views/test.py",
    title="Test",
    icon=":material/home:",

)

pg = st.navigation(pages=[ main_page ,aims_page, resource_page, test_page])

pg.run()