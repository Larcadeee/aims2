import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CSS LOADING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="ALIMAT Dashboard", layout="wide", initial_sidebar_state="expanded")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Ensure you have your style.css in the same directory!
local_css("style.css")

# -----------------------------------------------------------------------------
# 2. DATA FETCHING & PREPARATION
# -----------------------------------------------------------------------------
url = "https://docs.google.com/spreadsheets/d/1jjp2XBOEo3Mmd0BI691GEsQPH4tJsQWmt8w6bFqtvb4/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def load_data():
    df_incident = conn.read(spreadsheet=url, worksheet="0", header=0) 
    df_resources = conn.read(spreadsheet=url, worksheet="1800080155", header=1) 
    df_runtime = conn.read(spreadsheet=url, worksheet="2145305755", header=0) 
    
    if 'DATE' in df_incident.columns:
        df_incident['DATE'] = pd.to_datetime(df_incident['DATE'], errors='coerce')
        
    return df_incident, df_resources, df_runtime

df_incident, df_resources, df_runtime = load_data()

# -----------------------------------------------------------------------------
# 3. SIDEBAR (Filters)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://via.placeholder.com/200x100.png?text=CDRRMD+Logo", use_column_width=True)
    st.markdown("### FILTERS")
    
    date_filter = st.date_input("Date", value=None)
    time_filter = st.time_input("Time", value=None)
    
    if 'LOCATION/DESTINATION' in df_incident.columns:
        barangays = df_incident['LOCATION/DESTINATION'].dropna().unique().tolist()
        barangay_list = ["All"] + sorted(barangays)
    else:
        barangay_list = ["All"]
        
    barangay_filter = st.selectbox("Barangay", barangay_list)
    
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=POWERED+BY:+HAZARDS+MONITORING", use_column_width=True)

# --- Apply Filters ---
if date_filter:
    df_incident = df_incident[df_incident['DATE'].dt.date == date_filter]
if barangay_filter != "All":
    df_incident = df_incident[df_incident['LOCATION/DESTINATION'] == barangay_filter]

# -----------------------------------------------------------------------------
# 4. HEADER
# -----------------------------------------------------------------------------
head_col1, head_col2 = st.columns([4, 1])
with head_col1:
    st.markdown("<h2 style='color: #0056b3; margin-bottom: 0px;'>ALIMAT</h2>", unsafe_allow_html=True)
    st.markdown("<h6 style='color: #63a4ff; margin-top: 0px;'>INCIDENT MANAGEMENT SYSTEM DASHBOARD</h6>", unsafe_allow_html=True)
with head_col2:
    current_time = datetime.now().strftime("%a %b %d %I:%M%p").upper()
    st.markdown(f"<p style='text-align: right; font-weight: bold; padding-top: 20px;'>{current_time}</p>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. MAIN DASHBOARD LAYOUT
# -----------------------------------------------------------------------------

# --- KPI Calculations ---
total_calls = len(df_incident)
disregarded = len(df_incident[df_incident['CALL STATUS'].astype(str).str.contains('Disregard', case=False, na=False)]) if 'CALL STATUS' in df_incident.columns else 0
incident_calls = total_calls - disregarded

if 'TYPE OF CALL' in df_incident.columns:
    priority_1 = len(df_incident[df_incident['TYPE OF CALL'].astype(str).str.contains('Priority 1|P1', case=False, na=False)])
    priority_2 = len(df_incident[df_incident['TYPE OF CALL'].astype(str).str.contains('Priority 2|P2', case=False, na=False)])
else:
    priority_1, priority_2 = 0, 0

# --- Top Row: KPIs | Map | Donut Charts ---
col_kpi, col_map, col_donuts = st.columns([1.5, 4, 2])

with col_kpi:
    st.metric(label="Total Calls", value=total_calls)
    st.metric(label="Incident Calls", value=incident_calls)
    st.metric(label="Priority 1 Calls", value=priority_1)
    st.metric(label="Priority 2 Calls", value=priority_2)
    st.metric(label="Disregarded", value=disregarded)

with col_map:
    st.markdown("**Butuan City Incident Heat Map**")

    @st.cache_data(ttl=60)
    def load_and_prepare_data():
        import geopandas as gpd

        gdf = gpd.read_file("Boundary.json", driver="TopoJSON")
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
        else:
            gdf = gdf.to_crs("EPSG:4326")

        sheet_url = (
            "https://docs.google.com/spreadsheets/d/"
            "1dAXks7FBX-LN130hMCEWBz5JcSqM1lijBhxAejuNgco/"
            "export?format=csv&gid=1297922850"
        )
        df = pd.read_csv(sheet_url)

        if 'BARANGAY' in df.columns:
            df['BARANGAY'] = df['BARANGAY'].astype(str).str.upper().str.strip()
            df['BARANGAY'] = df['BARANGAY'].str.replace(r'\s*POBLACION\s*\(BARANGAY\s*\d+.*?\)\s*', '', regex=True)
            df['BARANGAY'] = df['BARANGAY'].str.replace('PORT POYOHON', 'FORT POYOHON')
            df['BARANGAY'] = df['BARANGAY'].str.replace('JOSE RIZAL', 'J.P. RIZAL')

        incident_counts = df['BARANGAY'].value_counts().reset_index()
        incident_counts.columns = ['BARANGAY', 'Incident_Count']

        merged_data = gdf.merge(incident_counts, left_on="BRANGAY", right_on="BARANGAY", how="left")
        merged_data["Incident_Count"] = merged_data["Incident_Count"].fillna(0)

        return merged_data, df

    with st.spinner("Syncing with live ALIMAT OPCEN Database..."):
        heatmap_data, raw_df = load_and_prepare_data()

    fig_map = px.choropleth_mapbox(
        heatmap_data,
        geojson=heatmap_data.geometry,
        locations=heatmap_data.index,
        color="Incident_Count",
        hover_name="BRANGAY",
        hover_data={"Incident_Count": True},
        color_continuous_scale="Reds",
        mapbox_style="carto-positron",
        center={"lat": 8.94, "lon": 125.54},
        zoom=11,
        opacity=0.75,
        labels={"Incident_Count": "Total Incidents"},
    )
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig_map, use_container_width=True)

    

with col_donuts:
    if 'NATURE OF CALL' in df_incident.columns:
        p1_data = df_incident[df_incident['TYPE OF CALL'].astype(str).str.contains('Priority 1', case=False, na=False)]['NATURE OF CALL'].value_counts().reset_index()
        p2_data = df_incident[df_incident['TYPE OF CALL'].astype(str).str.contains('Priority 2', case=False, na=False)]['NATURE OF CALL'].value_counts().reset_index()
    else:
        p1_data, p2_data = pd.DataFrame(), pd.DataFrame()

    st.markdown("<p style='font-size: 14px;'>Priority 1 Breakdown</p>", unsafe_allow_html=True)
    if not p1_data.empty:
        fig_donut1 = px.pie(p1_data, values='count', names='NATURE OF CALL', hole=0.6, height=200)
        fig_donut1.update_traces(textinfo='none', hoverinfo='label+percent')
        fig_donut1.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
        st.plotly_chart(fig_donut1, use_container_width=True)
    else:
        st.caption("No Priority 1 data")

    st.markdown("<p style='font-size: 14px;'>Priority 2 Breakdown</p>", unsafe_allow_html=True)
    if not p2_data.empty:
        fig_donut2 = px.pie(p2_data, values='count', names='NATURE OF CALL', hole=0.6, height=200)
        fig_donut2.update_traces(textinfo='none', hoverinfo='label+percent')
        fig_donut2.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
        st.plotly_chart(fig_donut2, use_container_width=True)
    else:
        st.caption("No Priority 2 data")

# --- Middle Row: Area Chart | Bar Chart ---
col_area, col_bar = st.columns([1, 1])

with col_area:
    st.markdown("**Average Turnaround Time (Per Month)**")
    if 'MONTH' in df_runtime.columns and 'TURNAROUND TIME' in df_runtime.columns:
        df_runtime['TURNAROUND_NUM'] = pd.to_numeric(df_runtime['TURNAROUND TIME'], errors='coerce')
        df_trend = df_runtime.groupby('MONTH')['TURNAROUND_NUM'].mean().reset_index()
        fig_area = px.area(df_trend, x="MONTH", y="TURNAROUND_NUM", height=250)
        fig_area.update_layout(margin=dict(t=10, b=10, l=0, r=0), plot_bgcolor="rgba(0,0,0,0)", yaxis=(dict(showgrid=False)))
        st.plotly_chart(fig_area, use_container_width=True)
    else:
        st.info("Insufficient data for Trend Line")

with col_bar:
    st.markdown("**TOP 10 BARANGAY WITH INCIDENT REPORT**")
    if 'LOCATION/DESTINATION' in df_incident.columns:
        df_bar = df_incident['LOCATION/DESTINATION'].value_counts().head(10).reset_index()
        df_bar.columns = ['Barangay', 'Incident Count']
        df_bar = df_bar.sort_values(by='Incident Count', ascending=True) 
        
        fig_bar = px.bar(df_bar, x="Incident Count", y="Barangay", orientation='h', height=250, color_discrete_sequence=['#63a4ff'])
        fig_bar.update_layout(margin=dict(t=10, b=10, l=0, r=0), plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No Location Data Available")

# -----------------------------------------------------------------------------
# 6. TIME METRICS (Bottom Row)
# -----------------------------------------------------------------------------
st.write("") 
foot_col1, foot_col2, foot_col3 = st.columns(3)

def get_average_metric(col_name, default="0:00"):
    if col_name in df_runtime.columns:
        val = df_runtime[col_name].dropna().values
        return str(val[0]) if len(val) > 0 else default
    return default

avg_run = get_average_metric('TOTAL AVERAGE RUN TIME', '2:02')
avg_res = get_average_metric('TOTAL AVERAGE', '6:18') 
avg_dis = get_average_metric('TOTAL AVERAGE DISPATCH TIME', '1:30')

with foot_col1:
    st.markdown(f"<div class='footer-metric'><b>Avg Run time</b> <span class='footer-value'>{avg_run}</span></div>", unsafe_allow_html=True)
with foot_col2:
    st.markdown(f"<div class='footer-metric'><b>Avg Response Time</b> <span class='footer-value'>{avg_res}</span></div>", unsafe_allow_html=True)
with foot_col3:
    st.markdown(f"<div class='footer-metric'><b>Avg Dispatch Time</b> <span class='footer-value'>{avg_dis}</span></div>", unsafe_allow_html=True)