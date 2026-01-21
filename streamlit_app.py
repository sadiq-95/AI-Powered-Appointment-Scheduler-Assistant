"""Streamlit frontend for AI-Powered Appointment Scheduler."""

import base64
import requests
import streamlit as st
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Page configuration
st.set_page_config(
    page_title="AI Appointment Scheduler",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .header-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Card styling */
    .result-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .success-card {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 5px solid #28a745;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        border-left: 5px solid #ffc107;
    }
    
    .error-card {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 5px solid #dc3545;
    }
    
    /* Appointment details styling */
    .appointment-detail {
        display: flex;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(0,0,0,0.1);
    }
    
    .appointment-detail:last-child {
        border-bottom: none;
    }
    
    .detail-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
        width: 40px;
        text-align: center;
    }
    
    .detail-content {
        flex: 1;
    }
    
    .detail-label {
        font-size: 0.85rem;
        color: #666;
        margin: 0;
    }
    
    .detail-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #333;
        margin: 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 30px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    /* Text area styling */
    .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        padding: 1rem;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* File uploader styling */
    .stFileUploader {
        border-radius: 12px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Status indicator */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-ok {
        background-color: #28a745;
        color: white;
    }
    
    .status-clarification {
        background-color: #ffc107;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)


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
        st.markdown(f"""
        <div class="result-card error-card">
            <h3>❌ Error</h3>
            <p>{result['error']}</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    status = result.get("status", "unknown")
    
    if status == "ok" and result.get("appointment"):
        appt = result["appointment"]
        st.markdown("""
        <div class="result-card success-card">
            <h3 style="color: #155724; margin-bottom: 1rem;">✅ Appointment Scheduled!</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Display appointment details in a nice format
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Department")
            st.markdown(f"**{appt['department'].title()}**")
            
            st.markdown("### 📅 Date")
            st.markdown(f"**{format_date(appt['date'])}**")
        
        with col2:
            st.markdown("### ⏰ Time")
            st.markdown(f"**{format_time(appt['time'])}**")
            
            st.markdown("### 🌍 Timezone")
            st.markdown(f"**{appt['tz']}**")
        
        # Show raw data in expander
        with st.expander("📊 View Raw Response"):
            st.json(result)
            
    elif status == "needs_clarification":
        st.markdown(f"""
        <div class="result-card warning-card">
            <h3 style="color: #856404;">⚠️ Clarification Needed</h3>
            <p style="font-size: 1.1rem; margin-top: 0.5rem;">{result.get('message', 'Please provide more details.')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("💡 **Tip**: Make sure to include the date, time, and type of appointment in your message.")
    else:
        st.markdown(f"""
        <div class="result-card error-card">
            <h3>❓ Unexpected Response</h3>
        </div>
        """, unsafe_allow_html=True)
        st.json(result)


# Header
st.markdown("""
<div class="header-container">
    <h1 class="header-title">📅 AI Appointment Scheduler</h1>
    <p class="header-subtitle">Schedule appointments using natural language or images</p>
</div>
""", unsafe_allow_html=True)

# API Health Check
api_healthy = check_api_health()
if not api_healthy:
    st.warning("⚠️ Backend API is not responding. Please make sure the server is running on port 8000.")

# Main input section
st.markdown("### 💬 How would you like to schedule?")

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
        st.image(uploaded_file, caption="Uploaded Image", width="stretch")
        
        if st.button("🚀 Process Image", key="image_btn", disabled=not api_healthy):
            with st.spinner("🔄 Processing image with OCR..."):
                image_base64 = encode_image(uploaded_file)
                result = schedule_appointment("image", image_base64)
                display_result(result)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>Powered by AI | Built with ❤️ using Streamlit & FastAPI</p>
</div>
""", unsafe_allow_html=True)
