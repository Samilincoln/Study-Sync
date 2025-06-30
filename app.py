import streamlit as st
import requests
import json
from datetime import datetime, time
import pandas as pd

# Configure Streamlit page
st.set_page_config(
    page_title="WhatsApp Tutoring Reminder",
    page_icon="📚",
    layout="wide"
)

# API Base URL
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if 'parent_phone' not in st.session_state:
    st.session_state.parent_phone = ""
if 'classes' not in st.session_state:
    st.session_state.classes = []

def make_api_request(endpoint, method="GET", data=None):
    """Make API request to FastAPI backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the FastAPI server is running on localhost:8000")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def load_parent_classes(phone):
    """Load classes for a parent"""
    classes = make_api_request(f"/classes/parent/{phone}")
    if classes:
        st.session_state.classes = classes
    return classes

# Main App
st.title("📚 Study-Sync")
st.markdown("---")

# Sidebar for parent registration
with st.sidebar:
    st.header("👨‍👩‍👧‍👦 Parent Registration")
    
    parent_name = st.text_input("Parent Name")
    parent_phone = st.text_input("Phone Number", placeholder="+1234567890")
    children_input = st.text_area("Children Names (one per line)")
    
    if st.button("Register Parent"):
        if parent_name and parent_phone:
            children_list = [child.strip() for child in children_input.split('\n') if child.strip()]
            parent_data = {
                "phone": parent_phone,
                "name": parent_name,
                "children": children_list,
                "timezone": "UTC"
            }
            
            result = make_api_request("/parents/", method="POST", data=parent_data)
            if result:
                st.success("Parent registered successfully!")
                st.session_state.parent_phone = parent_phone
    
    st.markdown("---")
    
    # Phone number input for existing parents
    st.header("🔍 Load Existing Parent")
    phone_lookup = st.text_input("Enter Phone Number", key="phone_lookup")
    if st.button("Load Classes"):
        if phone_lookup:
            st.session_state.parent_phone = phone_lookup
            load_parent_classes(phone_lookup)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📅 Class Management")
    
    # Display current parent
    if st.session_state.parent_phone:
        st.info(f"Managing classes for: {st.session_state.parent_phone}")
        
        # Add new class form
        with st.expander("➕ Add New Class", expanded=False):
            with st.form("add_class_form"):
                st.subheader("Class Details")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    child_name = st.text_input("Child's Name")
                    subject = st.text_input("Subject")
                with col_b:
                    day_of_week = st.selectbox(
                        "Day of Week",
                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    )
                    class_time = st.time_input("Class Time", value=time(16, 0))
                
                reminder_minutes = st.slider("Reminder (minutes before)", 5, 120, 30, 5)
                
                submit_class = st.form_submit_button("Add Class")
                
                if submit_class and child_name and subject:
                    class_data = {
                        "parent_phone": st.session_state.parent_phone,
                        "child_name": child_name,
                        "subject": subject,
                        "day_of_week": day_of_week,
                        "class_time": class_time.strftime("%H:%M"),
                        "reminder_minutes": reminder_minutes,
                        "is_active": True
                    }
                    
                    result = make_api_request("/classes/", method="POST", data=class_data)
                    if result:
                        st.success("Class added successfully!")
                        load_parent_classes(st.session_state.parent_phone)
                        st.rerun()
        
        # Display existing classes
        if st.session_state.classes:
            st.subheader("📚 Your Classes")
            
            for i, class_info in enumerate(st.session_state.classes):
                with st.expander(f"📖 {class_info['subject']} - {class_info['child_name']}", expanded=False):
                    col_x, col_y, col_z = st.columns([2, 1, 1])
                    
                    with col_x:
                        st.write(f"**Student:** {class_info['child_name']}")
                        st.write(f"**Day:** {class_info['day_of_week']}")
                        st.write(f"**Time:** {class_info['class_time']}")
                        st.write(f"**Reminder:** {class_info['reminder_minutes']} minutes before")
                        st.write(f"**Status:** {'Active' if class_info['is_active'] else 'Inactive'}")
                    
                    with col_y:
                        if st.button(f"Send Reminder", key=f"remind_{i}"):
                            reminder_data = {"class_id": class_info['id']}
                            result = make_api_request(
                                f"/reminders/send/{class_info['id']}", 
                                method="POST", 
                                data=reminder_data
                            )
                            if result:
                                st.success("Reminder sent!")
                    
                    with col_z:
                        if st.button(f"Delete", key=f"delete_{i}", type="secondary"):
                            result = make_api_request(f"/classes/{class_info['id']}", method="DELETE")
                            if result:
                                st.success("Class deleted!")
                                load_parent_classes(st.session_state.parent_phone)
                                st.rerun()
        else:
            st.info("No classes scheduled yet. Add your first class above!")
    
    else:
        st.warning("Please register or load a parent to manage classes.")

with col2:
    st.header("📊 Dashboard")
    
    # API Health Check
    health = make_api_request("/health")
    if health:
        st.metric("API Status", "Healthy ✅")
        st.metric("Total Parents", health.get("total_parents", 0))
        st.metric("Total Classes", health.get("total_classes", 0))
        st.metric("Scheduled Jobs", health.get("scheduled_jobs", 0))
    else:
        st.metric("API Status", "Offline ❌")
    
    st.markdown("---")
    
    # Today's Classes
    if st.session_state.parent_phone:
        st.subheader("📅 Today's Classes")
        today = datetime.now().strftime("%A")
        today_classes = [
            cls for cls in st.session_state.classes 
            if cls.get("day_of_week") == today and cls.get("is_active", True)
        ]
        
        if today_classes:
            for cls in today_classes:
                st.info(f"📚 {cls['subject']} - {cls['child_name']} at {cls['class_time']}")
        else:
            st.write("No classes today!")
    
    st.markdown("---")
    
    # WhatsApp Messages (Simulation)
    if st.session_state.parent_phone:
        st.subheader("💬 Recent Messages")
        messages = make_api_request(f"/messages/{st.session_state.parent_phone}")
        
        if messages:
            for msg in messages[-3:]:  # Show last 3 messages
                timestamp = msg.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime("%H:%M")
                    except:
                        time_str = "Unknown"
                else:
                    time_str = "Unknown"
                
                st.text_area(
                    f"Message at {time_str}:",
                    msg.get("message", ""),
                    height=100,
                    disabled=True,
                    key=f"msg_{msg.get('id', '')}"
                )
        else:
            st.write("No messages yet.")

# Footer
st.markdown("---")
st.markdown("""
### 🚀 Quick Start Guide:
1. **Register a Parent** in the sidebar with phone number and children names
2. **Add Classes** using the form above with subject, time, and reminder settings
3. **View Dashboard** to see today's schedule and system status
4. **Send Manual Reminders** using the buttons next to each class

### 📋 API Features:
- Automatic WhatsApp reminders before each class
- Custom reminder timing (5-120 minutes before)
- Multi-child support for families
- Real-time message tracking
- Webhook support for WhatsApp integration
""")

# Auto-refresh option
if st.checkbox("Auto-refresh every 30 seconds"):
    import time
    time.sleep(30)
    st.rerun()
