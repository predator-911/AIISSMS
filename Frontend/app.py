import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import time

# API Configuration
API_BASE_URL = "https://aiscms.onrender.com/api"  # Update this with your actual API URL

# Set page configuration
st.set_page_config(
    page_title="Space Cargo Management",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2563EB;
        margin-top: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #F3F4F6;
        margin-bottom: 1rem;
    }
    .status-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    .success-card {
        background-color: #D1FAE5;
        color: #065F46;
    }
    .warning-card {
        background-color: #FEF3C7;
        color: #92400E;
    }
    .error-card {
        background-color: #FEE2E2;
        color: #991B1B;
    }
    .info-text {
        font-size: 0.9rem;
        color: #6B7280;
    }
    .step-card {
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin-bottom: 0.5rem;
        background-color: #EFF6FF;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def call_api(endpoint, method="GET", data=None, files=None):
    """Generic API calling function with error handling"""
    url = f"{API_BASE_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=data)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        else:
            st.error(f"Unsupported method: {method}")
            return None
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def format_position(position):
    """Format position data for display"""
    if not position:
        return "Unknown"
    
    try:
        start = position.get("start", {})
        end = position.get("end", {})
        return f"W: {start.get('width', 0):.1f}-{end.get('width', 0):.1f}, " + \
               f"D: {start.get('depth', 0):.1f}-{end.get('depth', 0):.1f}, " + \
               f"H: {start.get('height', 0):.1f}-{end.get('height', 0):.1f}"
    except (KeyError, AttributeError):
        return "Invalid format"

# Tabs for different functionalities
def main():
    st.markdown("<h1 class='main-header'>Space Cargo Management System</h1>", unsafe_allow_html=True)
    
    tabs = st.tabs([
        "Dashboard", 
        "Add Cargo", 
        "Search & Retrieve",
        "Storage Placement",
        "Waste Management",
        "Simulation",
        "Logs & Reports"
    ])
    
    # Dashboard tab
    with tabs[0]:
        display_dashboard()
    
    # Add Cargo tab
    with tabs[1]:
        add_cargo_form()
    
    # Search & Retrieve tab
    with tabs[2]:
        search_retrieve_tab()
    
    # Storage Placement tab
    with tabs[3]:
        storage_placement_tab()
    
    # Waste Management tab
    with tabs[4]:
        waste_management_tab()
    
    # Simulation tab
    with tabs[5]:
        simulation_tab()
    
    # Logs & Reports tab
    with tabs[6]:
        logs_reports_tab()

def display_dashboard():
    st.markdown("<h2 class='section-header'>Cargo Status Dashboard</h2>", unsafe_allow_html=True)
    
    # Load dashboard data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Placeholder function to simulate getting item counts
        # In production, this would be an API call to a new endpoint that returns counts
        st.markdown("<div class='status-card success-card'><h3>Active Items</h3><h2>235</h2></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='status-card warning-card'><h3>Items Near Expiry</h3><h2>18</h2></div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='status-card error-card'><h3>Waste Items</h3><h2>7</h2></div>", unsafe_allow_html=True)
    
    # Display container utilization (mockup)
    st.markdown("<h3>Container Utilization</h3>", unsafe_allow_html=True)
    
    # Sample data for visualization
    container_data = {
        'Container': ['A-101', 'B-202', 'C-303', 'D-404', 'E-505'],
        'Capacity': [100, 100, 100, 100, 100],
        'Used': [75, 45, 90, 30, 60]
    }
    df = pd.DataFrame(container_data)
    
    # Calculate utilization percentage
    df['Utilization'] = df['Used'] / df['Capacity'] * 100
    
    # Create a horizontal bar chart
    fig = px.bar(df, y='Container', x='Utilization', 
                orientation='h', title='Container Utilization (%)',
                labels={'Utilization': 'Space Used (%)'},
                color='Utilization',
                color_continuous_scale=[(0, 'green'), (0.7, 'yellow'), (1, 'red')])
    
    fig.update_layout(xaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
    
    # Most retrieved items
    st.markdown("<h3>Most Retrieved Items</h3>", unsafe_allow_html=True)
    
    # Sample data
    retrieval_data = {
        'Item': ['Medical Supplies', 'Food Rations', 'Water', 'Tools', 'Batteries'],
        'Retrievals': [42, 35, 28, 22, 15]
    }
    df_retrievals = pd.DataFrame(retrieval_data)
    
    fig2 = px.bar(df_retrievals, x='Item', y='Retrievals', title='Top Retrieved Items')
    st.plotly_chart(fig2, use_container_width=True)

def add_cargo_form():
    st.markdown("<h2 class='section-header'>Add New Cargo</h2>", unsafe_allow_html=True)
    
    with st.form("add_cargo_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            item_id = st.text_input("Item ID", help="Unique identifier for the cargo item")
            name = st.text_input("Item Name", help="Name or description of the cargo item")
            priority = st.slider("Priority (1-100)", min_value=1, max_value=100, value=50, 
                             help="Higher priority items are placed more accessibly")
            preferred_zone = st.selectbox("Preferred Storage Zone", 
                                      ["Crew Quarters", "Laboratory", "Engineering", "Medical", "Food Storage"])
        
        with col2:
            width = st.number_input("Width (cm)", min_value=0.1, max_value=500.0, value=20.0, step=0.1)
            depth = st.number_input("Depth (cm)", min_value=0.1, max_value=500.0, value=20.0, step=0.1)
            height = st.number_input("Height (cm)", min_value=0.1, max_value=500.0, value=20.0, step=0.1)
            mass = st.number_input("Mass (kg)", min_value=0.1, max_value=1000.0, value=5.0, step=0.1)
            usage_limit = st.number_input("Usage Limit (Optional)", min_value=0, value=0, 
                                    help="Number of times the item can be used before becoming waste. Leave 0 for unlimited.")
        
        submit_button = st.form_submit_button("Add Cargo Item")
    
    if submit_button:
        # Prepare payload
        payload = {
            "itemId": item_id,
            "name": name,
            "width": width,
            "depth": depth,
            "height": height,
            "mass": mass,
            "priority": priority,
            "preferredZone": preferred_zone
        }
        
        if usage_limit > 0:
            payload["usageLimit"] = usage_limit
        
        # Call API
        response = call_api("add_cargo", method="POST", data=payload)
        
        if response:
            st.success(f"Cargo item added successfully! Item ID: {response.get('item_id')}")
        else:
            st.error("Failed to add cargo item. Please check the logs.")
    
    # Bulk import section
    st.markdown("<h3>Bulk Import Items</h3>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload CSV file with items", type=["csv"])
    
    if uploaded_file is not None:
        if st.button("Import Items"):
            files = {"file": uploaded_file}
            response = call_api("import/items", method="POST", files=files)
            
            if response and response.get("success"):
                st.success(f"Successfully imported {response.get('inserted')} items!")
            else:
                st.error("Failed to import items. Please check the file format.")

def search_retrieve_tab():
    st.markdown("<h2 class='section-header'>Search & Retrieve Items</h2>", unsafe_allow_html=True)
    
    # Search form
    item_id = st.text_input("Item ID", key="search_item_id")
    search_button = st.button("Search")
    
    if search_button and item_id:
        response = call_api(f"search", method="GET", data={"itemId": item_id})
        
        if response and response.get("success") and response.get("found"):
            item_details = response.get("itemDetails", {})
            st.success(f"Item found: **{item_details.get('name')}**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.write(f"**Container:** {item_details.get('containerId')}")
                st.write(f"**Zone:** {item_details.get('zone')}")
                st.write(f"**Position:** {format_position(item_details.get('position'))}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Display retrieval steps
            steps = response.get("retrievalSteps", [])
            if steps:
                with col2:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.write(f"**Retrieval Steps:** {len(steps)} steps")
                    st.write(f"**Obstructing Items:** {len([s for s in steps if s.get('action') == 'remove'])}")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<h3>Retrieval Plan</h3>", unsafe_allow_html=True)
                for step in steps:
                    step_class = ""
                    if step.get("action") == "remove":
                        step_class = "warning-card"
                    elif step.get("action") == "retrieve":
                        step_class = "success-card"
                    else:
                        step_class = "info-card"
                    
                    st.markdown(f"""
                    <div class='step-card {step_class}'>
                        <b>Step {step.get('step')}:</b> {step.get('action').title()} - 
                        {step.get('itemName')} (ID: {step.get('itemId')})
                    </div>
                    """, unsafe_allow_html=True)
                
                # Add retrieve button
                user_id = st.text_input("Your User ID", value="astronaut1")
                if st.button("Confirm Retrieval"):
                    # Call retrieve API
                    retrieve_data = {
                        "itemId": item_id,
                        "userId": user_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    retrieve_response = call_api("retrieve", method="POST", data=retrieve_data)
                    
                    if retrieve_response and retrieve_response.get("success"):
                        st.success("Item retrieval recorded successfully!")
                    else:
                        st.error("Failed to record item retrieval. Please try again.")
        
        elif response and response.get("found") is False:
            st.error("Item not found in inventory.")
        else:
            st.error("Error occurred during search.")
    
    # Manual placement section
    st.markdown("<h3>Manual Placement</h3>", unsafe_allow_html=True)
    st.markdown("<p class='info-text'>Use this form after retrieving an item to place it back into storage.</p>", unsafe_allow_html=True)
    
    with st.form("place_item_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            place_item_id = st.text_input("Item ID", key="place_item_id")
            place_user_id = st.text_input("Your User ID", value="astronaut1", key="place_user_id")
            place_container_id = st.text_input("Container ID")
        
        with col2:
            x_pos = st.number_input("Start Width (cm)", min_value=0.0, step=0.1)
            y_pos = st.number_input("Start Depth (cm)", min_value=0.0, step=0.1)
            z_pos = st.number_input("Start Height (cm)", min_value=0.0, step=0.1)
            width = st.number_input("Width (cm)", min_value=0.1, step=0.1, value=20.0)
            depth = st.number_input("Depth (cm)", min_value=0.1, step=0.1, value=20.0)
            height = st.number_input("Height (cm)", min_value=0.1, step=0.1, value=20.0)
        
        submit_place = st.form_submit_button("Place Item")
    
    if submit_place:
        place_data = {
            "itemId": place_item_id,
            "userId": place_user_id,
            "timestamp": datetime.now().isoformat(),
            "containerId": place_container_id,
            "position": {
                "start": {"width": x_pos, "depth": y_pos, "height": z_pos},
                "end": {"width": x_pos + width, "depth": y_pos + depth, "height": z_pos + height}
            }
        }
        
        place_response = call_api("place", method="POST", data=place_data)
        
        if place_response and place_response.get("success"):
            st.success("Item placed successfully!")
        else:
            st.error("Failed to place item. Please check the details and try again.")

def storage_placement_tab():
    st.markdown("<h2 class='section-header'>Storage Placement Optimization</h2>", unsafe_allow_html=True)
    
    # Upload containers
    st.markdown("<h3>Step 1: Configure Containers</h3>", unsafe_allow_html=True)
    
    container_upload = st.file_uploader("Upload container configuration CSV", type=["csv"])
    
    if container_upload is not None:
        try:
            container_df = pd.read_csv(container_upload)
            st.dataframe(container_df)
            
            if st.button("Import Containers"):
                files = {"file": container_upload}
                container_response = call_api("import/containers", method="POST", files=files)
                
                if container_response and container_response.get("success"):
                    st.success(f"Successfully imported {container_response.get('inserted')} containers!")
                else:
                    st.error("Failed to import containers.")
        except Exception as e:
            st.error(f"Error reading container file: {str(e)}")
    
    # Manual container entry
    st.markdown("<h3>Or Add Container Manually</h3>", unsafe_allow_html=True)
    
    with st.form("add_container_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            container_id = st.text_input("Container ID")
            zone = st.selectbox("Storage Zone", 
                            ["Crew Quarters", "Laboratory", "Engineering", "Medical", "Food Storage"])
        
        with col2:
            container_width = st.number_input("Width (cm)", min_value=1.0, value=100.0, step=1.0)
            container_depth = st.number_input("Depth (cm)", min_value=1.0, value=100.0, step=1.0)
            container_height = st.number_input("Height (cm)", min_value=1.0, value=100.0, step=1.0)
        
        submit_container = st.form_submit_button("Add Container")
    
    # Placeholder for container submission (would need a new API endpoint to add a single container)
    if submit_container:
        st.info("This feature would require an additional API endpoint in the backend for adding a single container.")
    
    # Placement optimization
    st.markdown("<h3>Step 2: Run Placement Optimization</h3>", unsafe_allow_html=True)
    
    # Placeholder for selecting items for placement
    if st.button("Run Optimal Placement"):
        # This would require an API call that gets all items and containers
        # Then sends them to the placement API
        st.info("In a production environment, this would fetch items and containers from the database and call the placement API.")
        
        # Simulate optimization result
        with st.spinner("Optimizing placement..."):
            time.sleep(2)  # Simulate API call
            
            # Mockup results
            st.success("Placement optimization completed!")
            
            placement_results = {
                "success": True,
                "placements": [
                    {"itemId": "ITEM-001", "containerId": "CONT-A101", "position": {"start": {"width": 0, "depth": 0, "height": 0}, "end": {"width": 20, "depth": 20, "height": 10}}},
                    {"itemId": "ITEM-002", "containerId": "CONT-A101", "position": {"start": {"width": 20, "depth": 0, "height": 0}, "end": {"width": 40, "depth": 20, "height": 15}}},
                ],
                "rearrangements": [
                    {"itemId": "ITEM-003", "action": "relocate", "details": "Placed in non-preferred zone Engineering instead of Medical"}
                ]
            }
            
            # Display results
            st.markdown("<h4>Placement Results</h4>", unsafe_allow_html=True)
            
            if placement_results.get("rearrangements"):
                st.warning(f"{len(placement_results.get('rearrangements'))} items needed rearrangement")
                
                for rearrange in placement_results.get("rearrangements"):
                    st.markdown(f"""
                    <div class='step-card warning-card'>
                        <b>{rearrange.get('itemId')}:</b> {rearrange.get('action').title()} - 
                        {rearrange.get('details')}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Visualization placeholder
            st.markdown("<h4>3D Visualization (Placeholder)</h4>", unsafe_allow_html=True)
            st.info("A 3D visualization of the placement would be displayed here")

def waste_management_tab():
    st.markdown("<h2 class='section-header'>Waste Management</h2>", unsafe_allow_html=True)
    
    # Identify waste
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Identify Waste Items"):
            with st.spinner("Scanning for waste items..."):
                waste_response = call_api("waste/identify", method="GET")
                
                if waste_response:
                    if waste_response:
                        st.success(f"Found {len(waste_response)} waste items")
                        
                        # Display waste items
                        if waste_response:
                            for item in waste_response:
                                reason_class = "error-card" if item.get("reason") == "Expired" else "warning-card"
                                st.markdown(f"""
                                <div class='step-card {reason_class}'>
                                    <b>{item.get('name')} (ID: {item.get('itemId')})</b><br>
                                    Reason: {item.get('reason')}<br>
                                    Container: {item.get('containerId')}
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("No waste items found")
                else:
                    st.error("Failed to identify waste items")
    
    with col2:
        st.markdown("<h3>Return Plan</h3>", unsafe_allow_html=True)
        max_weight = st.number_input("Maximum Return Weight (kg)", min_value=1.0, value=100.0, step=5.0)
        
        if st.button("Generate Return Plan"):
            # Call return plan API
            return_plan_response = call_api("waste/return-plan", method="POST", data={"maxWeight": max_weight})
            
            if return_plan_response and return_plan_response.get("success"):
                st.success(f"Return plan generated!")
                st.write(f"Total Weight: {return_plan_response.get('totalWeight', 0):.2f} kg")
                st.write(f"Total Volume: {return_plan_response.get('totalVolume', 0):.2f} m³")
                
                # Display steps
                steps = return_plan_response.get("steps", [])
                if steps:
                    for step in steps:
                        st.markdown(f"""
                        <div class='step-card'>
                            <b>Step {step.get('step')}:</b> Return {step.get('name')} (ID: {step.get('itemId')})<br>
                            Mass: {step.get('mass', 0):.2f} kg, Container: {step.get('containerId')}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Complete undocking option
                    container_id = st.text_input("Container ID for undocking", value=steps[0].get('containerId', ''))
                    if st.button("Complete Undocking"):
                        undock_response = call_api("waste/complete-undocking", method="POST", data={"containerId": container_id})
                        
                        if undock_response and undock_response.get("success"):
                            st.success(f"Undocking completed! {undock_response.get('itemsRemoved', 0)} items removed.")
                        else:
                            st.error("Failed to complete undocking process.")
                else:
                    st.info("No waste items to return")
            else:
                st.error("Failed to generate return plan")

def simulation_tab():
    st.markdown("<h2 class='section-header'>Time Simulation</h2>", unsafe_allow_html=True)
    st.markdown("<p class='info-text'>Simulate the passage of time to test expiration and usage depletion.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Simple time advancement
        st.markdown("<h3>Advance Time</h3>", unsafe_allow_html=True)
        days = st.number_input("Days to Advance", min_value=1, value=1)
        
        if st.button("Advance Time"):
            simulation_data = {
                "numOfDays": days,
                "itemsToBeUsedPerDay": []  # Empty usage for simple time advancement
            }
            
            sim_response = call_api("simulate/day", method="POST", data=simulation_data)
            
            if sim_response and sim_response.get("success"):
                st.success(f"Time advanced to {sim_response.get('newDate')}")
                
                expired = sim_response.get("expiredItems", [])
                depleted = sim_response.get("depletedItems", [])
                
                if expired:
                    st.warning(f"{len(expired)} items expired")
                    st.write("Expired item IDs:", ", ".join(expired))
                
                if depleted:
                    st.warning(f"{len(depleted)} items depleted")
                    st.write("Depleted item IDs:", ", ".join(depleted))
                
                if not expired and not depleted:
                    st.info("No items expired or depleted during this time period")
            else:
                st.error("Failed to advance time")
    
    with col2:
        # Advanced simulation with usage
        st.markdown("<h3>Simulate Usage</h3>", unsafe_allow_html=True)
        
        # Sample data for item usage simulation
        st.text_area("Item Usage JSON", value="""[
            {"day": 1, "usages": [{"itemId": "ITEM-001"}, {"itemId": "ITEM-002"}]},
            {"day": 2, "usages": [{"itemId": "ITEM-001"}, {"itemId": "ITEM-003"}]}
        ]""", height=200)
        
        if st.button("Simulate Usage"):
            st.info("This would simulate usage of specific items over time")
            # Implementation would parse the JSON and call the simulate API

def logs_reports_tab():
    st.markdown("<h2 class='section-header'>Logs & Reports</h2>", unsafe_allow_html=True)
    
    # Date range selection
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
    
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        item_id_filter = st.text_input("Item ID (Optional)", key="log_item_id")
    
    with col2:
        user_id_filter = st.text_input("User ID (Optional)")
    
    with col3:
        action_type = st.selectbox("Action Type", ["", "retrieval", "placement", "add_cargo"])
    
    if st.button("Get Logs"):
        # API parameters
        log_params = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat()
        }
        
        if item_id_filter:
            log_params["itemId"] = item_id_filter
        
        if user_id_filter:
            log_params["userId"] = user_id_filter
        
        if action_type:
            log_params["actionType"] = action_type
        
        logs_response = call_api("logs", method="GET", data=log_params)
        
        if logs_response:
            # Convert to DataFrame for display
            logs_df = pd.DataFrame(logs_response)
            
            if not logs_df.empty:
                st.success(f"Found {len(logs_df)} log entries")
                st.dataframe(logs_df)
                
                # Download option
                csv = logs_df.to_csv(index=False)
                st.download_button(
                    label="Download Logs CSV",
                    data=csv,
                    file_name=f"cargo_logs_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
                
                # Simple visualization
                if 'actionType' in logs_df.columns:
                    action_counts = logs_df['actionType'].value_counts().reset_index()
                    action_counts.columns = ['Action', 'Count']
                    
                    fig = px.pie(action_counts, values='Count', names='Action', 
                             title='Action Distribution')
                    st.plotly_chart(fig)
            else:
                st.info("No logs found for the selected criteria")
        else:
            st.error("Failed to retrieve logs")
    
    # Export current arrangement
    st.markdown("<h3>Export Current Arrangement</h3>", unsafe_allow_html=True)
    
    if st.button("Export Storage Arrangement"):
        # Link to export endpoint (direct file download)
        st.markdown(f"[Download Current Arrangement CSV]({API_BASE_URL}/export/arrangement)")
        st.info("Click the link above to download the current storage arrangement")

if __name__ == "__main__":
    main()