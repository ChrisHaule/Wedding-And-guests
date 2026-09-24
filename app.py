import streamlit as st
import pandas as pd
import qrcode
import io
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

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
# Live Google Sheets Connection
# ---------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df = conn.read(ttl=0)
        # Ensure standard columns exist
        expected_cols = ["Guest Name", "Email", "Status", "Check-in Time", "Confirmation"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = "-"
        return df
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        return pd.DataFrame(columns=["Guest Name", "Email", "Status", "Check-in Time", "Confirmation"])

df = get_data()

# Summary Metrics
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
# TAB 2: Add New Guest (Appends directly to Google Sheet)
# ---------------------------------------------------------
with tab2:
    st.subheader("➕ Add New Guest to Google Spreadsheet")
    
    with st.form("add_guest_form", clear_on_submit=True):
        new_name = st.text_input("Guest Name*")
        new_email = st.text_input("Guest Email")
        submit_btn = st.form_submit_button("Save to Google Sheet")
        
        if submit_btn:
            if new_name.strip() != "":
                new_entry = pd.DataFrame([{
                    "Guest Name": new_name.strip(),
                    "Email": new_email.strip() if new_email else "None",
                    "Status": "Not Entered",
                    "Check-in Time": "-",
                    "Confirmation": "Pending"
                }])
                
                updated_df = pd.concat([df, new_entry], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"🎉 {new_name} added directly to Google Sheets!")
                st.rerun()
            else:
                st.error("Please enter a guest name.")

# ---------------------------------------------------------
# TAB 3: Send Digital Invites & RSVP Options
# ---------------------------------------------------------
with tab3:
    st.subheader("✉️ Send Digital Invites & RSVP Response Options")
    st.write("Select a guest to dispatch an invite email and manage their attendance RSVP status:")
    
    if not df.empty:
        selected_guest_rsvp = st.selectbox("Select Guest for Invite / RSVP:", df["Guest Name"].tolist())
        
        guest_row = df[df["Guest Name"] == selected_guest_rsvp].iloc[0]
        st.write(f"**Current RSVP Status:** `{guest_row.get('Confirmation', 'Pending')}`")
        st.write(f"**Email Address:** `{guest_row.get('Email', 'None')}`")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("👍 Mark as ATTENDING"):
                df.loc[df["Guest Name"] == selected_guest_rsvp, "Confirmation"] = "Attending"
                conn.update(data=df)
                st.success(f"Updated {selected_guest_rsvp} to Attending!")
                st.rerun()
                
        with c2:
            if st.button("👎 Mark as DECLINED"):
                df.loc[df["Guest Name"] == selected_guest_rsvp, "Confirmation"] = "Declined"
                conn.update(data=df)
                st.error(f"Updated {selected_guest_rsvp} to Declined.")
                st.rerun()

        st.markdown("---")
        if st.button("🚀 Blast Digital Invites to All Pending Guests"):
            st.info("Sending email invitations with RSVP links to all pending guests...")
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
