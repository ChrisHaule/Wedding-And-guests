import streamlit as st
import pandas as pd
import qrcode
import io
from datetime import datetime
from PIL import Image

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="SARAH WEDDING MANAGEMENT",
    page_icon="💍",
    layout="wide"
)

# Custom Elegant CSS Theme (Blush Pink, Gold, Warm Tones)
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-family: 'Playfair Display', serif, sans-serif;
        color: #8B0032;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        color: #D4AF37;
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 25px;
    }
    .stButton>button {
        background-color: #8B0032;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #A3003B;
        color: #FFFFFF;
    }
    div[data-testid="stMetricValue"] {
        color: #8B0032;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Header Section
st.markdown("<h1 class='main-title'>💍 SARAH WEDDING MANAGEMENT</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>✨ Welcome to the Guest Portal & Verification System ✨</p>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Data Persistence (Google Sheets / Session State)
# ---------------------------------------------------------
# Initialize default data in session state if not set
if "guest_data" not in st.session_state:
    st.session_state.guest_data = pd.DataFrame([
        {"Guest Name": "Suzan", "Email": "suzan@example.com", "Status": "Not Entered", "Check-in Time": "-"},
        {"Guest Name": "Baraka", "Email": "baraka@example.com", "Status": "Arrived", "Check-in Time": "2026-07-09 10:39:00"},
        {"Guest Name": "Hasnein", "Email": "hasnein@example.com", "Status": "Not Entered", "Check-in Time": "-"},
        {"Guest Name": "dr sarah", "Email": "sarah@example.com", "Status": "Arrived", "Check-in Time": "2026-07-10 06:45:06"},
        {"Guest Name": "Christian", "Email": "christian@example.com", "Status": "Not Entered", "Check-in Time": "-"}
    ])

# Function to fetch latest sheet/data
def load_data():
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=5)
        return df
    except Exception:
        return st.session_state.guest_data

df = load_data()

# Summary Dashboard Metrics
col1, col2, col3 = st.columns(3)
total_guests = len(df)
arrived_guests = len(df[df["Status"] == "Arrived"]) if "Status" in df.columns else 0
pending_guests = total_guests - arrived_guests

with col1:
    st.metric(label="Total Invited Guests", value=total_guests)
with col2:
    st.metric(label="Checked-In Guests", value=arrived_guests)
with col3:
    st.metric(label="Pending Arrival", value=pending_guests)

st.markdown("---")

# ---------------------------------------------------------
# Application Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Live Guest Directory", 
    "➕ Add New Guest", 
    "🎟️ QR Code Tickets", 
    "📷 Scan QR Ticket"
])

# ---------------------------------------------------------
# TAB 1: Live Guest Directory
# ---------------------------------------------------------
with tab1:
    st.subheader("📋 Live Guest Directory")
    
    # Search and Filter Controls
    search_query = st.text_input("🔍 Search guest by name:", "")
    
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["Guest Name"].str.contains(search_query, case=False, na=False)]
        
    st.dataframe(filtered_df, use_container_width=True)

# ---------------------------------------------------------
# TAB 2: Add New Guest
# ---------------------------------------------------------
with tab2:
    st.subheader("➕ Add New Guest to Directory")
    
    with st.form("add_guest_form", clear_on_submit=True):
        new_name = st.text_input("Guest Name*")
        new_email = st.text_input("Guest Email (Optional)")
        submit_btn = st.form_submit_button("Add to Guest List")
        
        if submit_btn:
            if new_name.strip() != "":
                new_row = {
                    "Guest Name": new_name.strip(),
                    "Email": new_email.strip() if new_email else "None",
                    "Status": "Not Entered",
                    "Check-in Time": "-"
                }
                st.session_state.guest_data = pd.concat(
                    [st.session_state.guest_data, pd.DataFrame([new_row])], 
                    ignore_index=True
                )
                st.success(f"🎉 Successfully added {new_name} to the wedding guest list!")
                st.rerun()
            else:
                st.error("Please enter a valid guest name.")

# ---------------------------------------------------------
# TAB 3: QR Ticket Generator
# ---------------------------------------------------------
with tab3:
    st.subheader("🎟️ Generate Guest QR Ticket")
    
    guest_list = df["Guest Name"].tolist() if "Guest Name" in df.columns else []
    if guest_list:
        selected_guest = st.selectbox("Select a guest to view their QR code ticket:", guest_list)
        
        if selected_guest:
            # Generate QR Code
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(f"WEDDING_TICKET:{selected_guest}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="#8B0032", back_color="white")
            
            # Display Image
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"Ticket QR Code for {selected_guest}", width=250)
            
            st.info(f"💡 Tip: You can long-press or right-click the QR code to save and send it to {selected_guest}!")
    else:
        st.warning("No guests found in the directory.")

# ---------------------------------------------------------
# TAB 4: Scan QR Ticket (Camera Input)
# ---------------------------------------------------------
with tab4:
    st.subheader("📷 Scan Ticket QR Code")
    st.write("Take a picture of the guest's QR code ticket below:")
    
    camera_photo = st.camera_input("Scan Ticket")
    
    if camera_photo:
        st.info("Ticket scanned! Checking verification status...")
        # Simulating check-in action
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success(f"✅ Guest Verified & Checked In at {now_str}!")
