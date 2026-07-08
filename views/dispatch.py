import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.write("This is the Dispatch Page. Here you can view and manage resources related to your operations.")

# -----------------------------------------------------------------------------
# 2. DATA FETCHING & PREPARATION
# -----------------------------------------------------------------------------
url = "https://docs.google.com/spreadsheets/d/1jjp2XBOEo3Mmd0BI691GEsQPH4tJsQWmt8w6bFqtvb4/edit?usp=sharing"

# Define the connection first
conn = st.connection("gsheets", type=GSheetsConnection) 

# Place the decorator directly above the function
@st.cache_data(ttl=600)
def load_data():
    df_incident = conn.read(spreadsheet=url, worksheet="0", header=0) 
    df_resources = conn.read(spreadsheet=url, worksheet="1800080155", header=1) 
    df_runtime = conn.read(spreadsheet=url, worksheet="2145305755", header=0) 
    
    if 'DATE' in df_incident.columns:
        df_incident['DATE'] = pd.to_datetime(df_incident['DATE'], errors='coerce')
        
    return df_incident, df_resources, df_runtime

df_incident, df_resources, df_runtime = load_data()