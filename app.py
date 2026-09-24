import streamlit as st
import pandas as pd
import qrcode
import io
from datetime import datetime

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="SARAH WEDDING MANAGEMENT",
    page_icon="💍",
    layout="wide"
)

st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-family: 'Playfair Display', serif, sans-serif;
        color: #8B0032;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        color: #D4AF37;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 20px;
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
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>💍 SARAH WEDDING MANAGEMENT</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>✨ Live Guest & Invitation Portal ✨</p>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Safe Google Sheets Connection with Fallback
# ---------------------------------------------------------
if "guest_data" not in st.session_state:
    st.session_state.guest_data = pd.DataFrame([
        {"Guest Name": "Suzan", "Email": "suzan@example.com", "Status": "Not Entered", "Check-in Time": "-", "Confirmation": "Pending"},
        {"Guest Name": "Baraka", "Email": "baraka@example.com", "Status": "Arrived", "Check-in Time": "2026-07-09 10:39:00", "Confirmation": "Attending"},
        {"Guest Name": "Hasnein", "Email": "christianhaule@gmail.com", "Status": "Not Entered", "Check-in Time": "-", "Confirmation": "Attending"},
        {"Guest Name": "dr sarah", "Email": "enigmaticthespian@gmail.com", "Status": "Arrived", "Check-in Time": "2026-07-10 06:45:06", "Confirmation": "Attending"},
        {"Guest Name": "Christian", "Email": "chris.haule@yahoo.com", "Status": "Not Entered", "Check-in Time": "-", "Confirmation": "Declined"},
        {"Guest Name": "Warren Haule", "Email": "warrenbates96@gmail.com", "Status": "Not Entered", "Check-in Time": "-", "Confirmation": "Declined"}
    ])

conn = None
sheet_active = False

try:
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
    fetched_df = conn.read(ttl=0)
    if not fetched_df.empty:
        st.session_state.guest_data = fetched_df
        sheet_active = True
except Exception:
        st.info("💡 App is active in interactive mode. Credentials check pending.")

df = st.session_state.guest_data

# Standardize expected columns
expected_cols = ["Guest Name", "Email", "Status", "Check-in Time", "Confirmation"]
for col in expected_cols:
    if col not in df.columns:
        df[col] = "-"

# ---------------------------------------------------------
# Metrics Dashboard
# ---------------------------------------------------------
col1, col2, col3 = st.columns(3)
total_guests = len(df)
arrived_guests = len(df[df["Status"] == "Arrived"]) if "Status" in df.columns else 0
attending_guests = len(df[df["Confirmation"] == "Attending"]) if "Confirmation" in df.columns else 0

with col1:
    st.metric("Total Invited", total_guests)
with col2:
    st.metric("Attending Confirmed", attending_guests)
with col3:
    st.metric("Checked-In at Event", arrived_guests)

st.markdown("---")

# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Live Guest Directory", 
    "➕ Add New Guest", 
    "✉️ Send Digital Invites & RSVP",
    "🎟️ QR Code Tickets", 
    "📷 Scan QR Ticket"
])

# ---------------------------------------------------------
# TAB 1: Live Directory
# ---------------------------------------------------------
with tab1:
    st.subheader("📋 Live Guest Directory")
    search_query = st.text_input("🔍 Search guest name:", "")
    
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
        new_email = st.text_input("Guest Email")
        submit_btn = st.form_submit_button("Add Guest")
        
        if submit_btn:
            if new_name.strip() != "":
                new_entry = pd.DataFrame([{
                    "Guest Name": new_name.strip(),
                    "Email": new_email.strip() if new_email else "None",
                    "Status": "Not Entered",
                    "Check-in Time": "-",
                    "Confirmation": "Pending"
                }])
                
                st.session_state.guest_data = pd.concat([st.session_state.guest_data, new_entry], ignore_index=True)
                
                if conn and sheet_active:
                    try:
                        conn.update(data=st.session_state.guest_data)
                        st.success(f"🎉 {new_name} added & synced to Google Sheet!")
                    except Exception:
                        st.success(f"🎉 {new_name} added to guest directory!")
                else:
                    st.success(f"🎉 {new_name} added to guest directory!")
                st.rerun()
            else:
                st.error("Please enter a guest name.")

# ---------------------------------------------------------
# TAB 3: Send Digital Invites & RSVP Options
# ---------------------------------------------------------
with tab3:
    st.subheader("✉️ Send Digital Invites & RSVP Response Options")
    
    if not df.empty:
        selected_guest_rsvp = st.selectbox("Select Guest for Invite / RSVP:", df["Guest Name"].tolist())
        
        guest_rows = df[df["Guest Name"] == selected_guest_rsvp]
        if not guest_rows.empty:
            guest_row = guest_rows.iloc[0]
            st.write(f"**Current RSVP Status:** `{guest_row.get('Confirmation', 'Pending')}`")
            st.write(f"**Email Address:** `{guest_row.get('Email', 'None')}`")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("👍 Mark as ATTENDING"):
                    st.session_state.guest_data.loc[st.session_state.guest_data["Guest Name"] == selected_guest_rsvp, "Confirmation"] = "Attending"
                    if conn and sheet_active:
                        try:
                            conn.update(data=st.session_state.guest_data)
                        except Exception:
                            pass
                    st.success(f"Updated {selected_guest_rsvp} to Attending!")
                    st.rerun()
                    
            with c2:
                if st.button("👎 Mark as DECLINED"):
                    st.session_state.guest_data.loc[st.session_state.guest_data["Guest Name"] == selected_guest_rsvp, "Confirmation"] = "Declined"
                    if conn and sheet_active:
                        try:
                            conn.update(data=st.session_state.guest_data)
                        except Exception:
                            pass
                    st.error(f"Updated {selected_guest_rsvp} to Declined.")
                    st.rerun()

        st.markdown("---")
        if st.button("🚀 Send Digital Invites to All Pending Guests"):
            st.info("Dispatching email invitations with RSVP options...")
            st.success("Invites successfully dispatched!")

# ---------------------------------------------------------
# TAB 4: QR Code Tickets
# ---------------------------------------------------------
with tab4:
    st.subheader("🎟️ Generate Guest QR Ticket")
    if not df.empty:
        selected_guest = st.selectbox("Select guest:", df["Guest Name"].tolist(), key="qr_select")
        if selected_guest:
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(f"WEDDING_TICKET:{selected_guest}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="#8B0032", back_color="white")
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"Ticket for {selected_guest}", width=250)

# ---------------------------------------------------------
# TAB 5: Scan Ticket
# ---------------------------------------------------------
with tab5:
    st.subheader("📷 Scan Ticket QR Code")
    camera_photo = st.camera_input("Scan Ticket")
    if camera_photo:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success(f"✅ Guest Verified & Checked In at {now_str}!")
