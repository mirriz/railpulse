import streamlit as st
import requests
import pandas as pd

# --- Configuration ---
API_URL = "https://railpulse-w5g2.onrender.com"
st.set_page_config(page_title="RailPulse Dashboard", page_icon="🚆", layout="wide")

# --- Session State Management ---
if "token" not in st.session_state:
    st.session_state["token"] = None
if "view" not in st.session_state:
    st.session_state["view"] = "Dashboard"

# --- Helper Functions ---
def login(email, password):
    # FastAPI's OAuth2 expects form data with 'username' and 'password'
    res = requests.post(f"{API_URL}/users/login", data={"username": email, "password": password})
    if res.status_code == 200:
        st.session_state["token"] = res.json().get("access_token")
        st.success("Logged in successfully!")
    else:
        st.error("Invalid credentials.")

def register(email, password):
    res = requests.post(f"{API_URL}/users/register", json={"email": email, "password": password})
    if res.status_code == 201:
        st.success("Account created! You can now log in.")
    else:
        st.error(f"Registration failed: {res.json().get('detail', 'Unknown error')}")

def logout():
    st.session_state["token"] = None
    st.success("Logged out.")

# --- Sidebar Navigation & Auth ---
with st.sidebar:
    st.title("🚆 RailPulse")
    
    # Navigation
    st.session_state["view"] = st.radio("Navigation", ["Dashboard", "My Incidents"])
    
    st.divider()
    
    # Authentication
    if st.session_state["token"] is None:
        st.subheader("Account")
        auth_mode = st.selectbox("Choose Action", ["Login", "Register"])
        auth_email = st.text_input("Email")
        auth_password = st.text_input("Password", type="password")
        
        if st.button("Submit"):
            if auth_mode == "Login":
                login(auth_email, auth_password)
            else:
                register(auth_email, auth_password)
    else:
        st.success("Authenticated ✅")
        if st.button("Logout"):
            logout()

# --- Page: Dashboard (Public) ---
if st.session_state["view"] == "Dashboard":
    st.title("Hub Health & Live Telemetry")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        station_code = st.text_input("Enter Station Code (e.g., LDS, MAN, KGX)", value="LDS").upper()
        check_btn = st.button("Analyze Hub", use_container_width=True)
        
    if check_btn:
        with st.spinner("Fetching telemetry and computing Stress Index..."):
            # Fetch Health Analytics
            health_res = requests.get(f"{API_URL}/analytics/{station_code}/health")
            
            if health_res.status_code == 200:
                data = health_res.json()
                metrics = data["metrics"]
                
                # Top Level Metrics
                st.subheader(f"Status: {data['station']} ({data['station_code']})")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Hub Status", data["hub_status"])
                m2.metric("Stress Index", data["stress_index"])
                m3.metric("Avg Delay (mins)", metrics["avg_delay"])
                m4.metric("Active Reports", metrics["passenger_reports"])
                
                if data["hub_status"] == "RED":
                    st.error("WARNING: Hub is currently experiencing severe disruption.")
                elif data["hub_status"] == "AMBER":
                    st.warning("NOTICE: Hub is experiencing moderate friction.")
                else:
                    st.success("Hub operating normally.")
                    
                st.divider()
                
                # Fetch Live Departures
                st.subheader("Live Departures & Arrivals")
                deps_res = requests.get(f"{API_URL}/live/departures/{station_code}")
                if deps_res.status_code == 200:
                    trains = deps_res.json()
                    if trains:
                        df = pd.DataFrame(trains)
                        # Reorder and filter columns for cleaner display
                        display_df = df[["operator", "scheduled", "estimated", "from_name", "status", "platform", "delay_reason"]]
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No active trains found for this station.")
            else:
                st.error("Could not fetch data for this station. Check the station code.")

# --- Page: My Incidents (Protected) ---
elif st.session_state["view"] == "My Incidents":
    st.title("My Passenger Reports")
    
    if st.session_state["token"] is None:
        st.warning("You must be logged in to view and submit reports.")
    else:
        headers = {"Authorization": f"Bearer {st.session_state['token']}"}
        
        # Create New Incident Form
        with st.expander("📝 Report New Incident", expanded=True):
            with st.form("new_incident_form"):
                st.write("Submit crowdsourced data for the Hub Health algorithm.")
                c1, c2 = st.columns(2)
                with c1:
                    i_station = st.text_input("Station Code", value="LDS").upper()
                    i_type = st.selectbox("Issue Type", ["Crowding", "Antisocial Behaviour", "Maintenance", "Safety Hazard", "Other"])
                with c2:
                    i_severity = st.slider("Severity (1=Low, 5=Severe)", 1, 5, 3)
                    i_train = st.text_input("Train ID (Optional)")
                
                i_desc = st.text_area("Description")
                
                if st.form_submit_button("Submit Report"):
                    payload = {
                        "station_code": i_station,
                        "type": i_type,
                        "severity": i_severity,
                        "description": i_desc,
                        "train_id": i_train if i_train else None
                    }
                    res = requests.post(f"{API_URL}/incidents/", headers=headers, json=payload)
                    if res.status_code == 201:
                        st.success("Report submitted successfully!")
                    else:
                        st.error("Failed to submit report.")

        st.divider()
        
        # View Existing Incidents
        st.subheader("Your Active Reports")
        res = requests.get(f"{API_URL}/incidents/my-reports", headers=headers)
        if res.status_code == 200:
            reports = res.json()
            if not reports:
                st.info("You haven't submitted any reports yet.")
            else:
                for r in reports:
                    with st.container(border=True):
                        col_a, col_b = st.columns([4, 1])
                        with col_a:
                            st.markdown(f"**{r['station_code']}** - {r['type']} (Severity: {r['severity']}/5)")
                            st.caption(f"Reported at: {r['created_at']} | Desc: {r['description']}")
                        with col_b:
                            # Add a delete button for each report
                            if st.button("Delete", key=r['id']):
                                del_res = requests.delete(f"{API_URL}/incidents/{r['id']}", headers=headers)
                                if del_res.status_code == 204:
                                    st.success("Deleted! Refreshing...")
                                    st.rerun()
                                else:
                                    st.error("Error deleting.")