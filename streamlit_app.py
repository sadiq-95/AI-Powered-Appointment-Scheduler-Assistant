"""Streamlit frontend for AI-Powered Appointment Scheduler."""

import base64
import requests
import streamlit as st
from datetime import datetime

# Configuration
API_BASE_URL = "https://ai-powered-appointment-scheduler-hkbi.onrender.com"

# Page configuration
st.set_page_config(
    page_title="AI Appointment Scheduler",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="collapsed"
)


def check_api_health():
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def schedule_appointment(input_type: str, content: str) -> dict:
    """Call the appointment API endpoint."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/appointment",
            json={"input_type": input_type, "content": content},
            timeout=30
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to the API. Make sure the backend is running."}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        return {"error": str(e)}


def encode_image(uploaded_file) -> str:
    """Encode uploaded image to base64."""
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")


def format_date(date_str: str) -> str:
    """Format ISO date string to human readable format."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%A, %B %d, %Y")
    except:
        return date_str


def format_time(time_str: str) -> str:
    """Format 24-hour time to 12-hour format."""
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        return time_obj.strftime("%I:%M %p")
    except:
        return time_str


def display_result(result: dict):
    """Display the appointment result."""
    if "error" in result:
        st.error(f"❌ Error: {result['error']}")
        return
    
    status = result.get("status", "unknown")
    
    if status == "ok" and result.get("appointment"):
        appt = result["appointment"]
        st.success("✅ Appointment Scheduled!")
        
        # Display appointment details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 Department**")
            st.write(appt['department'].title())
            
            st.markdown("**📅 Date**")
            st.write(format_date(appt['date']))
        
        with col2:
            st.markdown("**⏰ Time**")
            st.write(format_time(appt['time']))
            
            st.markdown("**🌍 Timezone**")
            st.write(appt['tz'])
        
        # Show raw data in expander (filter out null values)
        with st.expander("📊 View Raw Response"):
            display_result_data = {k: v for k, v in result.items() if v is not None}
            st.json(display_result_data)
            
    elif status == "needs_clarification":
        st.warning(f"⚠️ Clarification Needed: {result.get('message', 'Please provide more details.')}")
        st.info("💡 **Tip**: Make sure to include the date, time, and type of appointment in your message.")
        
        # Show raw response for ambiguous inputs
        with st.expander("📊 View Raw Response"):
            display_result_data = {k: v for k, v in result.items() if v is not None}
            st.json(display_result_data)
    else:
        st.error("❓ Unexpected Response")
        st.json(result)


# Header
st.title("📅 AI Appointment Scheduler")
st.caption("Schedule appointments using natural language or images")

# API Health Check
api_healthy = check_api_health()
if not api_healthy:
    st.warning("⚠️ Backend API is not responding. Please make sure the server is running on port 8000.")

# Main input section
st.subheader("How would you like to schedule?")

tab1, tab2 = st.tabs(["📝 Text Input", "🖼️ Image Upload"])

with tab1:
    st.markdown("Enter your appointment details in natural language:")
    
    text_input = st.text_area(
        label="Appointment details",
        placeholder="Example: Schedule me a dentist appointment next Friday at 3pm\n\nOr: Book a doctor visit for tomorrow morning at 9:30",
        height=150,
        label_visibility="collapsed"
    )
    
    # Example prompts
    with st.expander("💡 Example prompts"):
        st.markdown("""
        - "Schedule a dentist appointment for next Monday at 2:30 PM"
        - "Book me a doctor visit on January 25th at 10 AM"
        - "I need to see the cardiologist this Friday at 4pm"
        - "Set up a dermatology appointment for tomorrow at 11:30"
        """)
    
    if st.button("🚀 Schedule Appointment", key="text_btn", disabled=not api_healthy):
        if text_input.strip():
            with st.spinner("🔄 Processing your request..."):
                result = schedule_appointment("text", text_input)
                display_result(result)
        else:
            st.error("Please enter some text to process.")

with tab2:
    st.markdown("Upload an image containing appointment details:")
    
    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["png", "jpg", "jpeg", "gif", "bmp"],
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # Display the uploaded image
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        
        if st.button("🚀 Process Image", key="image_btn", disabled=not api_healthy):
            with st.spinner("🔄 Processing image with OCR..."):
                image_base64 = encode_image(uploaded_file)
                result = schedule_appointment("image", image_base64)
                display_result(result)

# Footer
st.markdown("---")
st.caption("Powered by AI | Built with ❤️ using Streamlit & FastAPI")
