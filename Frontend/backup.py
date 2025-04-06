import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import datetime
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
import base64
from matplotlib import cm
from typing import List, Dict, Optional, Tuple

# App configuration
st.set_page_config(
    page_title="Space Cargo Management",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global variables
API_URL = "https://aiscms.onrender.com/api"  # Adjust based on backend deployment

# Helper functions
def api_call(endpoint, method="GET", data=None, files=None):
    """Make API calls to the backend"""
    url = f"{API_URL}/{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=data)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def create_3d_layout(placements, containers):
    """Create a 3D visualization of container contents"""
    fig = go.Figure()
    
    # Add containers as transparent boxes
    for container in containers:
        fig.add_trace(go.Mesh3d(
            x=[0, container['width'], container['width'], 0, 0, container['width'], container['width'], 0],
            y=[0, 0, container['depth'], container['depth'], 0, 0, container['depth'], container['depth']],
            z=[0, 0, 0, 0, container['height'], container['height'], container['height'], container['height']],
            i=[0, 0, 0, 1, 4, 4, 4, 5],
            j=[1, 2, 4, 2, 5, 6, 7, 6],
            k=[2, 3, 7, 3, 6, 7, 3, 7],
            opacity=0.4,
            color='rgba(200, 200, 200, 0.5)',
            hoverinfo='text',
            text=f"Container: {container['containerId']}<br>Zone: {container['zone']}",
            showscale=False
        ))
    
    # Color mapping for items based on priority
    colors = px.colors.sequential.Viridis
    
    # Add items as solid boxes
    for i, item in enumerate(placements):
        if 'position' not in item:
            continue
            
        start = item['position'].get('start', {})
        end = item['position'].get('end', {})
        
        if not all(key in start for key in ['width', 'depth', 'height']) or \
           not all(key in end for key in ['width', 'depth', 'height']):
            continue
        
        # Get color based on priority (fallback to index-based if no priority)
        priority = item.get('priority', i % len(colors))
        color_idx = int((priority / 100) * (len(colors) - 1))
        color = colors[color_idx]
        
        fig.add_trace(go.Mesh3d(
            x=[start['width'], end['width'], end['width'], start['width'], 
               start['width'], end['width'], end['width'], start['width']],
            y=[start['depth'], start['depth'], end['depth'], end['depth'], 
               start['depth'], start['depth'], end['depth'], end['depth']],
            z=[start['height'], start['height'], start['height'], start['height'], 
               end['height'], end['height'], end['height'], end['height']],
            i=[0, 0, 0, 1, 4, 4, 4, 5],
            j=[1, 2, 4, 2, 5, 6, 7, 6],
            k=[2, 3, 7, 3, 6, 7, 3, 7],
            color=color,
            opacity=0.7,
            hoverinfo='text',
            text=f"Item: {item.get('name', item['itemId'])}<br>Priority: {priority}"
        ))
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Width',
            yaxis_title='Depth',
            zaxis_title='Height',
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

# App component functions
def render_dashboard():
    """Render mission dashboard with key metrics"""
    st.header("Mission Dashboard 🛰️")
    
    # Get data for dashboard
    waste_stats = api_call("waste/identify")
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Total Items", value="Loading...", delta=None)
    
    with col2:
        st.metric(label="Storage Utilization", value="Loading...", delta=None)
    
    with col3:
        waste_count = len(waste_stats) if waste_stats else 0
        st.metric(label="Waste Items", value=waste_count, delta=None)
    
    with col4:
        current_time = api_call("simulate/day", method="GET", data={"action": "get_current_time"})
        if current_time:
            mission_time = current_time.get("currentTime", "Unknown")
        else:
            mission_time = datetime.datetime.now().strftime("%Y-%m-%d")
        st.metric(label="Mission Time", value=mission_time, delta=None)
    
    # Add charts
    st.subheader("Storage Distribution")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Placeholder chart for storage by zone
        data = {'Zone': ['Science', 'Food', 'Medical', 'Equipment', 'Personal'],
                'Count': [24, 18, 12, 30, 15]}
        
        fig = px.pie(data, values='Count', names='Zone', title='Items by Zone')
        st.plotly_chart(fig)
    
    with chart_col2:
        # Placeholder chart for priority distribution
        priority_data = {'Priority': ['Critical (80-100)', 'High (60-79)', 'Medium (40-59)', 'Low (20-39)', 'Optional (1-19)'],
                        'Count': [10, 15, 25, 30, 20]}
        
        fig = px.bar(priority_data, x='Priority', y='Count', title='Items by Priority Level')
        st.plotly_chart(fig)
    
    # Expiry timeline
    st.subheader("Upcoming Expirations")
    expiry_data = {
        'Item': ['Food Pack A', 'Medicine Kit', 'Science Sample', 'Water Container', 'Air Filter'],
        'Days Left': [5, 12, 8, 30, 45]
    }
    expiry_df = pd.DataFrame(expiry_data)
    expiry_df = expiry_df.sort_values('Days Left')
    
    fig = px.bar(expiry_df, x='Item', y='Days Left', title='Days Until Expiry',
                color='Days Left', color_continuous_scale='RdYlGn')
    st.plotly_chart(fig)

def render_item_management():
    """Render item management interface"""
    st.header("Item Management 📦")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Add New Item", "Search Item", "Browse Items", "Import Items"])
    
    with tab1:
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                item_id = st.text_input("Item ID", key="new_item_id")
                item_name = st.text_input("Item Name", key="new_item_name")
                priority = st.slider("Priority", 1, 100, 50, key="new_priority")
                zone = st.selectbox("Preferred Zone", 
                                   ["Science", "Food", "Medical", "Equipment", "Personal", "Other"], 
                                   key="new_zone")
            
            with col2:
                width = st.number_input("Width (cm)", min_value=0.1, value=30.0, key="new_width")
                depth = st.number_input("Depth (cm)", min_value=0.1, value=30.0, key="new_depth")
                height = st.number_input("Height (cm)", min_value=0.1, value=30.0, key="new_height")
                mass = st.number_input("Mass (kg)", min_value=0.1, value=1.0, key="new_mass")
                usage_limit = st.number_input("Usage Limit (optional)", min_value=0, value=0, key="new_usage_limit")
            
            submit_button = st.form_submit_button("Add Item")
            
            if submit_button:
                if not all([item_id, item_name, zone]):
                    st.error("Please fill out all required fields")
                else:
                    new_item = {
                        "itemId": item_id,
                        "name": item_name,
                        "width": width,
                        "depth": depth,
                        "height": height,
                        "mass": mass,
                        "priority": priority,
                        "preferredZone": zone
                    }
                    
                    if usage_limit > 0:
                        new_item["usageLimit"] = usage_limit
                    
                    response = api_call("add_cargo", method="POST", data=new_item)
                    
                    if response:
                        st.success(f"Added item {item_name} with ID {item_id}")
    
    with tab2:
        search_col1, search_col2 = st.columns([3, 1])
        
        with search_col1:
            search_query = st.text_input("Enter Item ID to search", key="search_query")
        
        with search_col2:
            search_button = st.button("Search")
        
        if search_button and search_query:
            search_results = api_call(f"search?itemId={search_query}")
            
            if search_results and search_results.get("found"):
                st.success("Item found!")
                
                item_details = search_results.get("itemDetails", {})
                st.subheader("Item Details")
                
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.write(f"**Name:** {item_details.get('name', 'Unknown')}")
                    st.write(f"**Container:** {item_details.get('containerId', 'Unknown')}")
                    st.write(f"**Zone:** {item_details.get('zone', 'Unknown')}")
                
                with detail_col2:
                    position = item_details.get("position", {})
                    if position:
                        st.write("**Position:**")
                        st.write(f"- Start: W{position.get('start', {}).get('width', 0)}, "
                                f"D{position.get('start', {}).get('depth', 0)}, "
                                f"H{position.get('start', {}).get('height', 0)}")
                        st.write(f"- End: W{position.get('end', {}).get('width', 0)}, "
                                f"D{position.get('end', {}).get('depth', 0)}, "
                                f"H{position.get('end', {}).get('height', 0)}")
                
                st.subheader("Retrieval Steps")
                steps = search_results.get("retrievalSteps", [])
                
                if steps:
                    steps_df = pd.DataFrame(steps)
                    st.table(steps_df)
                else:
                    st.info("No retrieval steps needed - item is directly accessible")
                
                # Action buttons
                retrieve_col1, retrieve_col2 = st.columns(2)
                
                with retrieve_col1:
                    retrieve_button = st.button("Retrieve Item")
                    if retrieve_button:
                        retrieve_data = {
                            "itemId": search_query,
                            "userId": "user_001",  # Would use actual user ID in production
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                        retrieve_response = api_call("retrieve", method="POST", data=retrieve_data)
                        if retrieve_response and retrieve_response.get("success"):
                            st.success("Item retrieval logged successfully")
                
                with retrieve_col2:
                    place_button = st.button("Return Item to Storage")
                    if place_button:
                        st.session_state["return_item_id"] = search_query
                        st.session_state["return_item_name"] = item_details.get('name', 'Unknown')
                        st.session_state["show_placement_form"] = True
                
                if st.session_state.get("show_placement_form", False) and st.session_state.get("return_item_id") == search_query:
                    st.subheader(f"Place {st.session_state.get('return_item_name')} in Storage")
                    
                    with st.form("place_item_form"):
                        place_col1, place_col2 = st.columns(2)
                        
                        with place_col1:
                            container_id = st.text_input("Container ID", key="place_container")
                        
                        with place_col2:
                            x = st.number_input("Position X", min_value=0.0, key="place_x")
                            y = st.number_input("Position Y", min_value=0.0, key="place_y")
                            z = st.number_input("Position Z", min_value=0.0, key="place_z")
                        
                        place_submit = st.form_submit_button("Confirm Placement")
                        
                        if place_submit:
                            # Calculate end position (simplified, would use actual dimensions)
                            place_data = {
                                "itemId": search_query,
                                "userId": "user_001",  # Would use actual user ID in production
                                "timestamp": datetime.datetime.now().isoformat(),
                                "containerId": container_id,
                                "position": {
                                    "start": {"width": x, "depth": y, "height": z},
                                    "end": {"width": x+30, "depth": y+30, "height": z+30}  # Placeholder dimensions
                                }
                            }
                            
                            place_response = api_call("place", method="POST", data=place_data)
                            if place_response and place_response.get("success"):
                                st.success("Item placement recorded successfully")
                                st.session_state["show_placement_form"] = False
            elif search_results:
                st.error("Item not found")
            else:
                st.error("Error searching for item")
    
    with tab3:
        st.subheader("Browse Items")
        
        # Filters
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            zone_filter = st.selectbox("Filter by Zone", 
                               ["All", "Science", "Food", "Medical", "Equipment", "Personal", "Other"], 
                               key="browse_zone")
        
        with filter_col2:
            priority_range = st.slider("Priority Range", 1, 100, (1, 100), key="browse_priority")
        
        with filter_col3:
            waste_filter = st.selectbox("Waste Status", ["All", "Non-Waste Only", "Waste Only"], key="browse_waste")
        
        # Display items (placeholder - would call API with filters)
        items_df = pd.DataFrame({
            "itemId": ["item001", "item002", "item003", "item004", "item005"],
            "name": ["Food Pack", "Tool Kit", "Medicine Box", "Water Jug", "Science Sample"],
            "priority": [90, 75, 85, 70, 50],
            "zone": ["Food", "Equipment", "Medical", "Food", "Science"],
            "mass": [1.2, 3.5, 0.8, 2.0, 0.5],
            "isWaste": [False, False, True, False, False],
            "container": ["container1", "container2", "container3", "container1", "container4"]
        })
        
        # Apply filters (would be done in API)
        if zone_filter != "All":
            items_df = items_df[items_df["zone"] == zone_filter]
        
        items_df = items_df[(items_df["priority"] >= priority_range[0]) & 
                           (items_df["priority"] <= priority_range[1])]
        
        if waste_filter == "Non-Waste Only":
            items_df = items_df[~items_df["isWaste"]]
        elif waste_filter == "Waste Only":
            items_df = items_df[items_df["isWaste"]]
        
        st.dataframe(items_df)
    
    with tab4:
        st.subheader("Import Items from CSV")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.write("Preview of data:")
            st.dataframe(df.head())
            
            if st.button("Import Data"):
                files = {"file": uploaded_file}
                import_response = api_call("import/items", method="POST", files=files)
                
                if import_response and import_response.get("success"):
                    st.success(f"Successfully imported {import_response.get('inserted', 0)} items")
                else:
                    st.error("Import failed")

def render_container_management():
    """Render container management interface"""
    st.header("Container Management 🗄️")
    
    tab1, tab2 = st.tabs(["View Containers", "Import Containers"])
    
    with tab1:
        st.subheader("Browse Containers")
        
        # Placeholder container data
        containers_df = pd.DataFrame({
            "containerId": ["container1", "container2", "container3", "container4"],
            "zone": ["Food", "Equipment", "Medical", "Science"],
            "width": [100, 120, 80, 90],
            "depth": [80, 100, 60, 70],
            "height": [60, 80, 50, 60],
            "itemCount": [15, 22, 8, 12],
            "spaceUtilization": ["75%", "82%", "45%", "60%"]
        })
        
        st.dataframe(containers_df)
        
        # Container visualization
        st.subheader("Container Visualization")
        container_select = st.selectbox("Select Container", containers_df["containerId"])
        
        # Placeholder container data
        selected_container = {
            "containerId": container_select,
            "zone": "Food",
            "width": 100,
            "depth": 80,
            "height": 60
        }
        
        # Placeholder item placements
        placements = [
            {
                "itemId": "item001", 
                "name": "Food Pack A", 
                "position": {
                    "start": {"width": 0, "depth": 0, "height": 0},
                    "end": {"width": 30, "depth": 20, "height": 10}
                },
                "priority": 90
            },
            {
                "itemId": "item002", 
                "name": "Food Pack B", 
                "position": {
                    "start": {"width": 40, "depth": 0, "height": 0},
                    "end": {"width": 70, "depth": 20, "height": 10}
                },
                "priority": 75
            },
            {
                "itemId": "item003", 
                "name": "Water Jug", 
                "position": {
                    "start": {"width": 0, "depth": 30, "height": 0},
                    "end": {"width": 20, "depth": 50, "height": 30}
                },
                "priority": 85
            }
        ]
        
        # Create 3D visualization
        fig = create_3d_layout(placements, [selected_container])
        st.plotly_chart(fig)
    
    with tab2:
        st.subheader("Import Containers from CSV")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv", key="container_upload")
        
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.write("Preview of data:")
            st.dataframe(df.head())
            
            if st.button("Import Containers"):
                files = {"file": uploaded_file}
                import_response = api_call("import/containers", method="POST", files=files)
                
                if import_response and import_response.get("success"):
                    st.success(f"Successfully imported {import_response.get('inserted', 0)} containers")
                else:
                    st.error("Import failed")

def render_waste_management():
    """Render waste management interface"""
    st.header("Waste Management ♻️")
    
    # Get waste data
    waste_data = api_call("waste/identify")
    if not waste_data:
        waste_data = []  # Fallback if API fails
    
    tab1, tab2 = st.tabs(["Waste Items", "Return Planning"])
    
    with tab1:
        st.subheader("Identified Waste Items")
        
        if not waste_data:
            st.info("No waste items currently identified")
        else:
            waste_df = pd.DataFrame(waste_data)
            
            # Summary metrics
            waste_by_reason = waste_df.groupby("reason").size().reset_index(name="count")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(waste_by_reason, values="count", names="reason", 
                         title="Waste by Reason", color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig)
            
            with col2:
                st.metric("Total Waste Items", len(waste_data))
                
                if "Expired" in waste_by_reason["reason"].values:
                    expired_count = waste_by_reason[waste_by_reason["reason"] == "Expired"]["count"].values[0]
                    st.metric("Expired Items", expired_count)
                else:
                    st.metric("Expired Items", 0)
                    
                if "Depleted" in waste_by_reason["reason"].values:
                    depleted_count = waste_by_reason[waste_by_reason["reason"] == "Depleted"]["count"].values[0]
                    st.metric("Depleted Items", depleted_count)
                else:
                    st.metric("Depleted Items", 0)
            
            # Waste items table
            st.subheader("Waste Items List")
            st.dataframe(waste_df)
    
    with tab2:
        st.subheader("Return Planning")
        
        # Enter return capacity
        max_weight = st.number_input("Maximum Return Weight Capacity (kg)", 
                                    min_value=1.0, max_value=1000.0, value=100.0)
        
        if st.button("Generate Return Plan"):
            # Call return plan API
            return_plan = api_call("waste/return-plan", method="POST", 
                                   data={"maxWeight": max_weight})
            
            if return_plan and return_plan.get("success"):
                st.success(f"Return plan generated with {len(return_plan.get('steps', []))} items")
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Weight", f"{return_plan.get('totalWeight', 0):.2f} kg")
                
                with col2:
                    weight_pct = (return_plan.get('totalWeight', 0) / max_weight) * 100
                    st.metric("Capacity Utilization", f"{weight_pct:.1f}%")
                
                with col3:
                    st.metric("Total Volume", f"{return_plan.get('totalVolume', 0):.2f} m³")
                
                # Steps table
                if return_plan.get("steps"):
                    steps_df = pd.DataFrame(return_plan["steps"])
                    st.subheader("Return Steps")
                    st.dataframe(steps_df)
                    
                    # Export option
                    if st.button("Export Return Plan"):
                        st.download_button(
                            label="Download Return Plan CSV",
                            data=steps_df.to_csv(index=False).encode('utf-8'),
                            file_name='return_plan.csv',
                            mime='text/csv',
                        )
                else:
                    st.info("No items in return plan")
            else:
                st.error("Error generating return plan")

def render_placement_planner():
    """Render placement planning interface"""
    st.header("Placement Planner 📐")
    
    tab1, tab2 = st.tabs(["Manual Placement", "AI Recommendations"])
    
    with tab1:
        st.subheader("Manual Placement")
        
        col1, col2 = st.columns(2)
        
        with col1:
            item_id = st.text_input("Item ID", key="place_item_id")
            container_id = st.text_input("Container ID", key="place_container_id")
        
        with col2:
            x = st.number_input("X Position", min_value=0.0, value=0.0)
            y = st.number_input("Y Position", min_value=0.0, value=0.0)
            z = st.number_input("Z Position", min_value=0.0, value=0.0)
        
        if st.button("Save Placement"):
            if not all([item_id, container_id]):
                st.error("Please provide both Item ID and Container ID")
            else:
                place_data = {
                    "itemId": item_id,
                    "userId": "user_001",  # Would use actual user ID in production
                    "timestamp": datetime.datetime.now().isoformat(),
                    "containerId": container_id,
                    "position": {
                        "start": {"width": x, "depth": y, "height": z},
                        "end": {"width": x+30, "depth": y+30, "height": z+30}  # Placeholder dimensions
                    }
                }
                
                place_response = api_call("place", method="POST", data=place_data)
                if place_response and place_response.get("success"):
                    st.success("Item placement recorded successfully")
    
    with tab2:
        st.subheader("AI Placement Recommendations")
        
        # Placeholder for items and containers
        items = [
            {
                "itemId": "item001",
                "name": "Food Pack A",
                "width": 30.0,
                "depth": 20.0,
                "height": 10.0,
                "mass": 1.2,
                "priority": 90,
                "preferredZone": "Food"
            },
            {
                "itemId": "item002",
                "name": "Tool Kit",
                "width": 40.0,
                "depth": 30.0,
                "height": 15.0,
                "mass": 3.5,
                "priority": 75,
                "preferredZone": "Equipment"
            }
        ]
        
        containers = [
            {
                "containerId": "container1",
                "zone": "Food",
                "width": 100.0,
                "depth": 80.0,
                "height": 60.0
            },
            {
                "containerId": "container2",
                "zone": "Equipment",
                "width": 120.0,
                "depth": 100.0,
                "height": 80.0
            }
        ]
        
        st.write("Select items to place:")
        selected_items = []
        for i, item in enumerate(items):
            if st.checkbox(f"{item['name']} (ID: {item['itemId']})", key=f"place_item_{i}"):
                selected_items.append(item)
        
        st.write("Select containers to use:")
        selected_containers = []
        for i, container in enumerate(containers):
            if st.checkbox(f"{container['containerId']} (Zone: {container['zone']})", key=f"place_container_{i}"):
                selected_containers.append(container)
        
        if st.button("Generate Placement Plan") and selected_items and selected_containers:
            st.info("Generating optimal placement plan...")
            
            # Call placement API
            placement_data = {
                "items": selected_items,
                "containers": selected_containers
            }
            
            placement_response = api_call("placement", method="POST", data=placement_data)
            
            if placement_response and placement_response.get("success"):
                placements = placement_response.get("placements", [])
                rearrangements = placement_response.get("rearrangements", [])
                
                if placements:
                    st.success(f"Generated placement plan for {len(placements)} items")
                    
                    # Show placements
                    st.subheader("Placement Results")
                    placements_df = pd.DataFrame([{
                        "itemId": p["itemId"],
                        "containerId": p["containerId"],
                        "position": f"({p['position']['start']['width']}, {p['position']['start']['depth']}, {p['position']['start']['height']})",
                        "rotation": p.get("rotation", "unknown")
                    } for p in placements])
                    
                    st.dataframe(placements_df)
                    
                    # Show 3D visualization
                    st.subheader("Visual Placement")
                    fig = create_3d_layout(placements, selected_containers)
                    st.plotly_chart(fig)
                
                if rearrangements:
                    st.warning(f"{len(rearrangements)} items need special handling")
                    rearrange_df = pd.DataFrame(rearrangements)
                    st.dataframe(rearrange_df)
            else:
                st.error("Failed to generate placement plan")

def render_mission_simulator():
    """Render mission simulator interface"""
    st.header("Mission Simulator ⏱️")
    
    tab1, tab2 = st.tabs(["Time Controls", "Usage Simulation"])
    
    with tab1:
        st.subheader("Time Simulation Controls")
        
        current_time = api_call("simulate/day", method="GET", data={"action": "get_current_time"})
        if current_time:
            mission_time = current_time.get("currentTime", "Unknown")
            st.write(f"Current Mission Time: **{mission_time}**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Advance 1 Day"):
                sim_response = api_call("simulate/day", method="POST", 
                                        data={"action": "advance", "days": 1})
                if sim_response and sim_response.get("success"):
                    st.success(f"Advanced to {sim_response.get('newTime')}")
                    st.experimental_rerun()
        
        with col2:
            if st.button("Advance 1 Week"):
                sim_response = api_call("simulate/day", method="POST", 
                                        data={"action": "advance", "days": 7})
                if sim_response and sim_response.get("success"):
                    st.success(f"Advanced to {sim_response.get('newTime')}")
                    st.experimental_rerun()
        
        with col3:
            custom_days = st.number_input("Custom Days", min_value=1, max_value=90, value=14)
            if st.button("Advance Custom"):
                sim_response = api_call("simulate/day", method="POST", 
                                        data={"action": "advance", "days": custom_days})
                if sim_response and sim_response.get("success"):
                    st.success(f"Advanced to {sim_response.get('newTime')}")
                    st.experimental_rerun()
        
        # Expiration preview
        st.subheader("Expiration Preview")
        
        preview_days = st.slider("Preview Expirations Within Days", 1, 90, 30)
        if st.button("Check Upcoming Expirations"):
            expiry_preview = api_call("simulate/expiry-preview", method="GET", 
                                     data={"days": preview_days})
            
            if expiry_preview:
                expiry_items = expiry_preview.get("expiringItems", [])
                if expiry_items:
                    st.warning(f"{len(expiry_items)} items will expire within {preview_days} days")
                    
                    # Convert to DataFrame for display
                    expiry_df = pd.DataFrame([{
                        "itemId": item["itemId"],
                        "name": item.get("name", "Unknown"),
                        "expiryDate": item["expiryDate"],
                        "daysRemaining": item["daysRemaining"]
                    } for item in expiry_items])
                    
                    st.dataframe(expiry_df.sort_values("daysRemaining"))
                else:
                    st.success(f"No items will expire within {preview_days} days")
    
    with tab2:
        st.subheader("Item Usage Simulation")
        
        usage_col1, usage_col2 = st.columns(2)
        
        with usage_col1:
            item_id = st.text_input("Item ID", key="usage_item_id")
        
        with usage_col2:
            usage_count = st.number_input("Usage Count", min_value=1, value=1)
        
        if st.button("Record Usage"):
            if not item_id:
                st.error("Please provide an Item ID")
            else:
                usage_data = {
                    "itemId": item_id,
                    "usageCount": usage_count,
                    "userId": "user_001",  # Would use actual user ID in production
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                usage_response = api_call("simulate/use-item", method="POST", data=usage_data)
                if usage_response and usage_response.get("success"):
                    remaining = usage_response.get("remainingUses")
                    if remaining is not None:
                        st.success(f"Usage recorded. {remaining} uses remaining.")
                    else:
                        st.success("Usage recorded successfully")
                        
                    # Check if item became waste
                    if usage_response.get("becameWaste", False):
                        st.warning("This item is now classified as waste due to depletion")
                else:
                    st.error("Failed to record usage")

def render_settings():
    """Render application settings"""
    st.header("System Settings ⚙️")
    
    tab1, tab2 = st.tabs(["General Settings", "System Status"])
    
    with tab1:
        st.subheader("API Configuration")
        
        current_api = st.text_input("API URL", API_URL)
        if st.button("Update API URL"):
            # Would implement logic to update the API URL
            st.success(f"API URL updated to {current_api}")
        
        st.subheader("Mission Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            mission_name = st.text_input("Mission Name", "Mars Expedition 2025")
            mission_duration = st.number_input("Mission Duration (days)", min_value=30, value=365)
        
        with col2:
            crew_size = st.number_input("Crew Size", min_value=1, value=6)
            location = st.text_input("Mission Location", "Mars Base Alpha")
        
        if st.button("Save Mission Parameters"):
            mission_data = {
                "name": mission_name,
                "duration": mission_duration,
                "crewSize": crew_size,
                "location": location
            }
            
            # Would implement API call to save parameters
            st.success("Mission parameters saved successfully")
    
    with tab2:
        st.subheader("System Status")
        
        # Check API connectivity
        connection_status = api_call("health")
        
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            if connection_status and connection_status.get("status") == "ok":
                st.markdown("**API Status:** 🟢 Connected")
            else:
                st.markdown("**API Status:** 🔴 Disconnected")
        
        with status_col2:
            # Simplified database metrics
            st.markdown("**Database Status:** 🟢 Connected")
            st.markdown("**Items in Database:** 234")
            st.markdown("**Containers in Database:** 12")
        
        # System logs
        st.subheader("Recent System Logs")
        
        logs = [
            {"timestamp": "2025-04-05 09:25:12", "level": "INFO", "message": "Automatic backup completed"},
            {"timestamp": "2025-04-05 08:42:05", "level": "INFO", "message": "Item retrieval: item003"},
            {"timestamp": "2025-04-04 18:15:33", "level": "WARNING", "message": "Low storage space in container2"},
            {"timestamp": "2025-04-04 14:22:18", "level": "ERROR", "message": "Failed to connect to inventory database"}
        ]
        
        logs_df = pd.DataFrame(logs)
        st.dataframe(logs_df)
        
        if st.button("Clear Logs"):
            st.success("System logs cleared")
        
        # Backup & restore
        st.subheader("Backup & Restore")
        
        backup_col1, backup_col2 = st.columns(2)
        
        with backup_col1:
            if st.button("Create Backup"):
                st.success("Backup created successfully: cargo_system_20250405.bak")
        
        with backup_col2:
            uploaded_backup = st.file_uploader("Restore from Backup", type="bak")
            if uploaded_backup is not None and st.button("Restore System"):
                st.warning("System restore in progress...")
                # Would implement actual restore logic
                st.success("System restored successfully")

# Main app
def main():
    """Main application entry point"""
    # App title and sidebar
    st.sidebar.title("Space Cargo Management")
    st.sidebar.image("https://via.placeholder.com/150x150.png?text=SCM", width=150)
    
    # Navigation
    page = st.sidebar.radio("Navigation", 
                           ["Dashboard", 
                            "Item Management", 
                            "Container Management",
                            "Waste Management",
                            "Placement Planner",
                            "Mission Simulator",
                            "Settings"])
    
    # Render appropriate page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Item Management":
        render_item_management()
    elif page == "Container Management":
        render_container_management()
    elif page == "Waste Management":
        render_waste_management()
    elif page == "Placement Planner":
        render_placement_planner()
    elif page == "Mission Simulator":
        render_mission_simulator()
    elif page == "Settings":
        render_settings()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 Space Cargo Management")
    st.sidebar.markdown("Version 1.0.0")

if __name__ == "__main__":
    main()

