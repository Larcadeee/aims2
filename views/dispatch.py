import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.write("This is the Dispatch Page. Here you can view and manage resources related to your operations.")