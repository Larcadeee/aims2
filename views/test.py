import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd  # Fixed the syntax error here
import re

# Set up the dashboard layout
st.set_page_config(page_title="OPCEN Dashboard", layout="wide")

# Set up the dashboard layout
st.set_page_config(page_title="OPCEN Dashboard", layout="wide")

# -----------------------------------------------------------------------------
# 1. MAP MODULE DEFINITION
# -----------------------------------------------------------------------------
def render_incident_map(filtered_df, boundary_geojson_path="Boundary.json"):
    st.subheader("Butuan City Incident Heat Map")

    @st.cache_data(ttl=60)
    def load_and_prepare_data(df, geo_path):
        try:
            gdf = gpd.read_file(geo_path, driver="TopoJSON")
            if gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4326")
            else:
                gdf = gdf.to_crs("EPSG:4326")
        except Exception as e:
            st.error(f"Error loading boundary file: {e}")
            return None

        temp_df = df.copy()

        if 'BARANGAY' in temp_df.columns:
            temp_df['MAP_BARANGAY'] = temp_df['BARANGAY'].astype(str).str.upper().str.strip()
            temp_df['MAP_BARANGAY'] = temp_df['MAP_BARANGAY'].str.replace(r'\s*POBLACION\s*\(BARANGAY\s*\d+.*?\)\s*', '', regex=True)
            temp_df['MAP_BARANGAY'] = temp_df['MAP_BARANGAY'].str.replace('PORT POYOHON', 'FORT POYOHON')
            temp_df['MAP_BARANGAY'] = temp_df['MAP_BARANGAY'].str.replace('JOSE RIZAL', 'J.P. RIZAL')

            incident_counts = temp_df['MAP_BARANGAY'].value_counts().reset_index()
            incident_counts.columns = ['MAP_BARANGAY', 'Incident_Count']
        else:
            incident_counts = pd.DataFrame(columns=['MAP_BARANGAY', 'Incident_Count'])

        merged_data = gdf.merge(incident_counts, left_on="BRANGAY", right_on="MAP_BARANGAY", how="left")
        merged_data["Incident_Count"] = merged_data["Incident_Count"].fillna(0)
        return merged_data

    with st.spinner("Syncing map data..."):
        heatmap_data = load_and_prepare_data(filtered_df, boundary_geojson_path)

    if heatmap_data is not None:
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

# -----------------------------------------------------------------------------
# 2. DATA FETCHING & HELPER FUNCTIONS
# -----------------------------------------------------------------------------
SHEET_ID = "1dAXks7FBX-LN130hMCEWBz5JcSqM1lijBhxAejuNgco"
GID = "1297922850" 
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

def get_avg_time_str(time_series):
    td_series = pd.to_timedelta(time_series, errors='coerce')
    avg_td = td_series.mean()
    if pd.isnull(avg_td): return "00:00:00"
    total_seconds = int(avg_td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

@st.cache_data(ttl=600)
def load_live_data(url):
    raw_df = pd.read_csv(url)
    
    # Clean Whitespaces out of headers
    raw_df.columns = raw_df.columns.str.strip()
    return raw_df

# -----------------------------------------------------------------------------
# 3. MAIN DASHBOARD UI
# -----------------------------------------------------------------------------
with st.spinner("Fetching live data from Google Sheets..."):
    try:
        df = load_live_data(CSV_URL) 

        # --- Calculations ---
        total_calls = len(df)
        
        # --- CONDITIONAL EMERGENCY FILTER FOR PRIORITY 1 ---
        if 'PRIORITY DISPATCH' in df.columns:
            # 1. Define high-threat life safety conditions
            p1_keywords = [
                'Priority 1', 
                'ABC', 
                'Cardiac Arrest', 
                'DOB', 
                'Motor Vehicular Accident', 
                'MVA'
            ]
            # 2. Create a joined case-insensitive regex pattern
            p1_pattern = '|'.join(p1_keywords)
            
            # 3. Count rows that match priority terms
            priority_1 = df['PRIORITY DISPATCH'].str.contains(p1_pattern, case=False, na=False).sum()
            priority_2 = df['PRIORITY DISPATCH'].str.contains('Priority 2', case=False, na=False).sum()
            total_disregarded = df['PRIORITY DISPATCH'].str.contains('Not Applicable|Disregarded', case=False, na=False).sum()
        else:
            priority_1 = 0
            priority_2 = 0
            total_disregarded = 0
            
        incident_calls = total_calls - total_disregarded

        avg_dispatch_time = get_avg_time_str(df['COMPUTED DISPATCH TIME']) if 'COMPUTED DISPATCH TIME' in df.columns else "00:00:00"
        avg_run_time = get_avg_time_str(df['COMPUTED RUN TIME']) if 'COMPUTED RUN TIME' in df.columns else "00:00:00"
        avg_response_time = get_avg_time_str(df['COMPUTED RESPONSE TIME']) if 'COMPUTED RESPONSE TIME' in df.columns else "00:00:00"

        # --- Layout ---
        st.title("ALIMAT Dashboard")
        st.subheader("Live Key Metrics")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric(label="Total Calls",  value=f"{total_calls:,}", border=True)
        with col2: st.metric(label="Incident Calls", value=f"{incident_calls:,}", border=True)
        with col3: st.metric(label="Priority 1 Calls", value=f"{priority_1:,}", border=True)
        with col4: st.metric(label="Priority 2 Calls", value=f"{priority_2:,}", border=True)
        with col5: st.metric(label="Disregarded / N/A", value=f"{total_disregarded:,}", border=True)

        st.markdown("<br>", unsafe_allow_html=True) 
        
       

        st.divider()
        
        # --- Split Layout for Chart and Map ---
        chart_col, map_col = st.columns([1, 1])
        
        with chart_col:
            st.subheader("Turn Around Time Trend")
            
            if 'TIMESTAMP' in df.columns and 'AVERAGED TURN AROUND TIME' in df.columns:
                chart_df = df.copy()
                chart_df['TIMESTAMP_CLEAN'] = pd.to_datetime(chart_df['TIMESTAMP'], errors='coerce')
                
                def formula_time_to_minutes(val):
                    if pd.isna(val):
                        return None
                    val_str = str(val).strip()
                    
                    match = re.match(r'^(\d+):(\d{2}):(\d{2})$', val_str)
                    if match:
                        hours = int(match.group(1))
                        minutes = int(match.group(2))
                        seconds = int(match.group(3))
                        return (hours * 60) + minutes + (seconds / 60.0)
                        
                    try:
                        return float(val_str)
                    except ValueError:
                        return None

                chart_df['Plot_Y'] = chart_df['AVERAGED TURN AROUND TIME'].apply(formula_time_to_minutes)
                y_label = "Avg Turn Around Time (Minutes)"
                
                chart_df = chart_df.dropna(subset=['TIMESTAMP_CLEAN', 'Plot_Y'])
                chart_df = chart_df.sort_values('TIMESTAMP_CLEAN')
                
                if not chart_df.empty:
                    fig_line = px.line(
                        chart_df,
                        x='TIMESTAMP_CLEAN',
                        y='Plot_Y',
                        labels={'TIMESTAMP_CLEAN': 'Log Timeline', 'Plot_Y': y_label},
                        markers=True
                    )
                    fig_line.update_layout(margin={"r": 10, "t": 40, "l": 10, "b": 10})
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("No matching numeric records available for timeline plot generation.")
            else:
                st.warning("Required columns ('TIMESTAMP' or 'AVERAGED TURN AROUND TIME') missing.")
                
        with map_col:
            render_incident_map(df, "Boundary.json")

        st.divider()

        col6, col7, col8 = st.columns(3)
        with col6: st.metric(label="Avg Dispatch Time", value=avg_dispatch_time, border=True)
        with col7: st.metric(label="Avg Run Time", value=avg_run_time, border=True)
        with col8: st.metric(label="Avg Response Time", value=avg_response_time, border=True)

        st.subheader("Live Data Table")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")