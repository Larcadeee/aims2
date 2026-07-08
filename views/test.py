import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd # Added missing import

# Set up the dashboard layout
st.set_page_config(page_title="OPCEN Dashboard", layout="wide")

# -----------------------------------------------------------------------------
# 1. MAP MODULE DEFINITION (Defined first so it can be called later)
# -----------------------------------------------------------------------------
def render_incident_map(filtered_df, boundary_geojson_path="Boundary.json"):
    st.subheader("Butuan City Incident Heat Map")

    @st.cache_data(ttl=60)
    def load_and_prepare_data(df, geo_path):
        try:
            # Fixed variable name to gpd
            gdf = gpd.read_file(geo_path, driver="TopoJSON")
            if gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4326")
            else:
                gdf = gdf.to_crs("EPSG:4326")
        except Exception as e:
            st.error(f"Error loading boundary file: {e}")
            return None

        temp_df = df.copy()

        # UPDATED: Using 'BARANGAY' column based on your provided DATASHEET.csv
        if 'BARANGAY' in temp_df.columns:
            # Clean and format barangay names
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
    return pd.read_csv(url)

# -----------------------------------------------------------------------------
# 3. MAIN DASHBOARD UI
# -----------------------------------------------------------------------------
with st.spinner("Fetching live data from Google Sheets..."):
    try:
        df = load_live_data(CSV_URL) 

        # --- Calculations ---
        total_calls = len(df)
        priority_1 = df['PRIORITY DISPATCH'].str.contains('Priority 1', na=False).sum()
        priority_2 = df['PRIORITY DISPATCH'].str.contains('Priority 2', na=False).sum()
        total_disregarded = df['PRIORITY DISPATCH'].str.contains('Not Applicable|Disregarded', na=False).sum()
        incident_calls = total_calls - total_disregarded

        avg_dispatch_time = get_avg_time_str(df['COMPUTED DISPATCH TIME'])
        avg_run_time = get_avg_time_str(df['COMPUTED RUN TIME'])
        avg_response_time = get_avg_time_str(df['COMPUTED RESPONSE TIME'])

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
        
        col6, col7, col8, col9, col10 = st.columns(5)
        with col6: st.metric(label="Avg Dispatch Time", value=avg_dispatch_time, border=True)
        with col7: st.metric(label="Avg Run Time", value=avg_run_time, border=True)
        with col8: st.metric(label="Avg Response Time", value=avg_response_time, border=True)

        st.divider()
        
        # --- Split Layout for Chart and Map ---
        chart_col, map_col = st.columns([1, 2])
        
        with chart_col:
            st.subheader("Total Calls per Month")
            if 'MONTH' in df.columns:
                monthly_counts = df['MONTH'].value_counts()
                months_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                                'July', 'August', 'September', 'October', 'November', 'December']
                present_months = [m for m in months_order if m in monthly_counts.index]
                monthly_counts = monthly_counts.reindex(present_months)
                st.bar_chart(monthly_counts, color="#1f77b4")
            else:
                st.warning("Could not find the 'MONTH' column.")
                
        with map_col:
            # ACTUALLY CALLING THE MAP FUNCTION HERE
            render_incident_map(df, "Boundary.json")

        st.divider()

        st.subheader("Live Data Table")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")