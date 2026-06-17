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
    fig_map = px.scatter_mapbox(lat=[8.9475], lon=[125.5406], zoom=10, height=450)
    fig_map.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
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
# 6. RESOURCE TRACKER (Live Status & Availability)
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("<h4 style='color: #0056b3;'>🚑 RESOURCE TRACKER</h4>", unsafe_allow_html=True)

if 'STATUS' in df_resources.columns and 'RESOURCES' in df_resources.columns:
    df_resources['STATUS'] = df_resources['STATUS'].fillna('Unknown')
    df_resources = df_resources.dropna(subset=['RESOURCES']) 
    
    available = df_resources[df_resources['STATUS'] == 'Available']
    assigned = df_resources[df_resources['STATUS'] == 'Assigned']
    unavailable = df_resources[df_resources['STATUS'].isin(['Not available', 'Out-of-order'])]
    
    r_col1, r_col2 = st.columns([1, 1.5])
    
    with r_col1:
        st.markdown("**Fleet Availability Distribution**")
        
        # New distinct donut chart design (Thinner ring, labels inside)
        status_counts = df_resources['STATUS'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        color_map = {
            'Available': '#28a745', 
            'Assigned': '#fd7e14', 
            'Not available': '#dc3545', 
            'Out-of-order': '#6c757d',
            'Unknown': '#adb5bd'
        }
        
        fig_res_donut = px.pie(
            status_counts, 
            values='Count', 
            names='Status', 
            hole=0.75, # Different thickness from the priority charts
            color='Status',
            color_discrete_map=color_map,
            height=300
        )
        fig_res_donut.update_traces(textposition='inside', textinfo='percent+label', showlegend=False)
        fig_res_donut.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_res_donut, use_container_width=True)
        
        # KPI Summary row under the chart
        st.markdown(
            f"<div style='text-align: center; padding: 10px;'>"
            f"<span style='color:#28a745; font-weight:bold;'>🟢 Available: {len(available)}</span> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<span style='color:#fd7e14; font-weight:bold;'>🟠 Assigned: {len(assigned)}</span> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<span style='color:#dc3545; font-weight:bold;'>🔴 Unavailable: {len(unavailable)}</span>"
            f"</div>", 
            unsafe_allow_html=True
        )

    with r_col2:
        st.markdown("**🟢 Ready for Dispatch (Available Resources)**")
        st.write("Current operational units and their fuel status:")
        
        if not available.empty:
            for _, row in available.iterrows():
                res_name = row['RESOURCES']
                fuel_lvl = row['FUEL'] if pd.notna(row['FUEL']) else "Unknown"
                base = row['BASE STATION'] if pd.notna(row['BASE STATION']) else "Unknown Base"
                
                # Custom HTML layout for the elaborate tracker
                st.markdown(f"""
                <div style="border-left: 5px solid #28a745; margin-bottom: 12px; background-color: #f8f9fa; padding: 12px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <b style="font-size: 16px; color: #333;">{res_name}</b>
                        <span style="background-color: #e6f4ea; color: #1e8e3e; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">AVAILABLE</span>
                    </div>
                    <div style="margin-top: 5px; color: #555; font-size: 14px;">
                        ⛽ <b>Fuel Level:</b> {fuel_lvl} &nbsp;&nbsp; | &nbsp;&nbsp; 📍 <b>Base:</b> {base}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No resources currently available.")
else:
    st.info("Resource Tracking data is currently unavailable. Please check spreadsheet headers.")

# -----------------------------------------------------------------------------
# 7. TIME METRICS (Bottom Row)
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