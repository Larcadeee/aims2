import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

url = "https://docs.google.com/spreadsheets/d/1jjp2XBOEo3Mmd0BI691GEsQPH4tJsQWmt8w6bFqtvb4/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def load_data():
    df_resources = conn.read(spreadsheet=url, worksheet="1800080155", header=1)
    if 'STATUS' in df_resources.columns:
        df_resources['STATUS'] = df_resources['STATUS'].fillna('Unknown')
    return df_resources

st.set_page_config(page_title="Resource Tracker", layout="wide")
st.title("Resource Tracker")

# Load resource data
try:
    df_resources = load_data()
except Exception as e:
    st.error(f"Unable to load resource data: {e}")
    st.stop()

if 'STATUS' in df_resources.columns and 'RESOURCES' in df_resources.columns:
    df_resources = df_resources.dropna(subset=['RESOURCES'])

    available = df_resources[df_resources['STATUS'] == 'Available']
    assigned = df_resources[df_resources['STATUS'] == 'Assigned']
    unavailable = df_resources[df_resources['STATUS'].isin(['Not available', 'Out-of-order'])]

    r_col1, r_col2 = st.columns([1, 1.5])

    with r_col1:
        st.markdown("**Fleet Availability Distribution**")

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
            hole=0.75,
            color='Status',
            color_discrete_map=color_map,
            height=300,
        )
        fig_res_donut.update_traces(textposition='inside', textinfo='percent+label', showlegend=False)
        fig_res_donut.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_res_donut, use_container_width=True)

        st.markdown(
            f"<div style='text-align: center; padding: 10px;'>"
            f"<span style='color:#28a745; font-weight:bold;'>🟢 Available: {len(available)}</span> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<span style='color:#fd7e14; font-weight:bold;'>🟠 Assigned: {len(assigned)}</span> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<span style='color:#dc3545; font-weight:bold;'>🔴 Unavailable: {len(unavailable)}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with r_col2:
        st.markdown("**🟢 Ready for Dispatch (Available Resources)**")
        st.write("Current operational units and their fuel status:")

        if not available.empty:
            for _, row in available.iterrows():
                res_name = row['RESOURCES']
                fuel_lvl = row['FUEL'] if pd.notna(row['FUEL']) else "Unknown"
                base = row['BASE STATION'] if pd.notna(row['BASE STATION']) else "Unknown Base"

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