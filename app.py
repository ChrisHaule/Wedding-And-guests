import streamlit as st
import pandas as pd
import qrcode
import io
import requests
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import urllib.parse
import json
import time

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

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxJ2QqjTFLmgm6t4BtV8YJ1O9gAt5ZaZ8f9dTqrtRhizQapHPQz-Zoac8ds7asrU20zYA/exec"
REQUIRED_COLS = ["Guest Name", "Status", "Check-in Time", "Phone Number", "Email", "Confirmation"]

# ---------------------------------------------------------
# Handle Native Streamlit Guest Landing Page (From Email Clicks)
# ---------------------------------------------------------
query_params = st.query_params
if "guest" in query_params and "rsvp" in query_params:
    guest_name_param = query_params["guest"]
    rsvp_param = query_params["rsvp"]
    
    try:
        requests.post(APPS_SCRIPT_URL, json={
            "action": "update_rsvp", 
            "name": guest_name_param, 
            "confirmation": rsvp_param
        }, timeout=5)
    except Exception:
        pass
    
    st.markdown("<h1 style='text-align: center;'>✨ Response Recorded! ✨</h1>", unsafe_allow_html=True)
    st.balloons()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if rsvp_param == "Attending":
            st.success(f"🎉 **Thank you, {guest_name_param}!**\n\nYour response has been recorded as **Attending**.")
            st.markdown("---")
            st.subheader("🎟️ Your Official Entry QR Ticket")
            
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(f"WEDDING_TICKET:{guest_name_param}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="#8B0032", back_color="white")
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"Entry Ticket for {guest_name_param}", width=280)
            st.info("📌 Please screenshot or save this QR code to present at the event entrance.")
        else:
            st.warning(f"Thank you, **{guest_name_param}**. Your response has been recorded as **Not Attending**. We appreciate your warm wishes!")
            
    st.stop()

# ---------------------------------------------------------
# Main Header
# ---------------------------------------------------------
st.markdown("<h1 class='main-title'>💍 SARAH WEDDING MANAGEMENT</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>✨ Live Guest & Invitation Portal ✨</p>", unsafe_allow_html=True)

def fetch_live_data():
    try:
        response = requests.get(APPS_SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 1:
                df_data = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                for col in REQUIRED_COLS:
                    if col not in df_data.columns:
                        df_data[col] = "-"
                return df_data[REQUIRED_COLS]
        return pd.DataFrame(columns=REQUIRED_COLS)
    except Exception:
        return pd.DataFrame(columns=REQUIRED_COLS)

def send_real_email(to_email, guest_name):
    try:
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        smtp_server = st.secrets["email"].get("smtp_server", "smtp.gmail.com")
        smtp_port = int(st.secrets["email"].get("smtp_port", 587))

        encoded_name = urllib.parse.quote(guest_name)
        streamlit_base = "https://wedding-and-guests-qbguhu8allp6ontujnq4ah.streamlit.app/"
        attend_url = f"{streamlit_base}?guest={encoded_name}&rsvp=Attending"
        decline_url = f"{streamlit_base}?guest={encoded_name}&rsvp=Not%20Attending"

        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = "💍 You're Invited: Sarah's Wedding Ceremony!"

        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #2b2b2b; padding: 20px; margin: 0;">
            <div style="max-width: 450px; margin: 0 auto; background: #1e1e1e; padding: 30px; border-radius: 12px; border: 1px solid #333; text-align: center; color: #ffffff;">
              <h1 style="color: #f7a8b8; margin-bottom: 10px;">Sarah's Wedding Ceremony</h1>
              <p style="font-size: 16px; color: #dddddd;">Dear <strong>{guest_name}</strong>,</p>
              <p style="font-size: 14px; color: #bbbbbb; line-height: 1.5;">
                You are cordially invited to celebrate Sarah's Wedding Ceremony with us!<br>
                Please let us know if you will be attending by clicking below:
              </p>
              
              <div style="margin: 25px 0;">
                <a href="{attend_url}" target="_blank" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: block; margin-bottom: 10px;">
                  ✓ Will Attend
                </a>
                <a href="{decline_url}" target="_blank" style="background-color: #e65c65; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: block;">
                  ✗ Won't Attend
                </a>
              </div>
              
              <p style="font-size: 12px; color: #888888;">Clicking "Will Attend" will display your official event QR entry ticket.</p>
              <hr style="border: none; border-top: 1px solid #333333; margin-top: 25px;">
              <p style="font-size: 12px; color: #777777;">Wedding Management Team</p>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(html_content, 'html'))

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            
        return True, "Success"
    except Exception as e:
        return False, str(e)

df = fetch_live_data()

# ---------------------------------------------------------
# Metrics Dashboard
# ---------------------------------------------------------
col1, col2, col3 = st.columns(3)
total_guests = len(df)
arrived_guests = len(df[df["Status"] == "Arrived"]) if not df.empty else 0
attending_guests = len(df[df["Confirmation"] == "Attending"]) if not df.empty else 0

with col1:
    st.metric("Total Invited", total_guests)
with col2:
    st.metric("Attending Confirmed", attending_guests)
with col3:
    st.metric("Checked-In at Event", arrived_guests)

st.markdown("---")

# ---------------------------------------------------------
# Navigation Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Live Guest Directory", 
    "➕ Add New Guest", 
    "✉️ Send Digital Invites & RSVP",
    "🎟️ QR Code Tickets", 
    "📷 Scan QR Ticket"
])

# TAB 1: Live Directory
with tab1:
    st.subheader("📋 Live Guest Directory")
    if st.button("🔄 Refresh Data"):
        st.rerun()

    search_query = st.text_input("🔍 Search guest name:", "")
    filtered_df = df.copy()
    if search_query and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df["Guest Name"].astype(str).str.contains(search_query, case=False, na=False)]
        
    st.dataframe(filtered_df, use_container_width=True)

    st.markdown("---")
    st.subheader("🗑️ Delete Guest from Directory & Sheet")
    guest_list = [g for g in df["Guest Name"].dropna().tolist() if str(g).strip() != ""] if not df.empty else []
    
    if guest_list:
        col_select, col_btn = st.columns([3, 1])
        with col_select:
            guest_to_delete = st.selectbox("Select Guest to Remove:", guest_list, key="delete_select")
        with col_btn:
            st.write("")
            st.write("")
            if st.button("❌ Delete Guest"):
                payload = {"action": "delete_guest", "name": guest_to_delete}
                try:
                    requests.post(APPS_SCRIPT_URL, json=payload)
                    st.success(f"🗑️ Removed {guest_to_delete}!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete guest: {e}")
    else:
        st.info("No guests currently in the directory.")

# TAB 2: Add New Guest
with tab2:
    st.subheader("➕ Add New Guest")
    with st.form("add_guest_form", clear_on_submit=True):
        new_name = st.text_input("Guest Name*")
        new_phone = st.text_input("Phone Number")
        new_email = st.text_input("Guest Email")
        submit_btn = st.form_submit_button("Add Guest to List")
        
        if submit_btn:
            if new_name.strip() != "":
                payload = {
                    "action": "add_guest",
                    "name": new_name.strip(),
                    "phone": new_phone.strip() if new_phone else "-",
                    "email": new_email.strip() if new_email else "-"
                }
                try:
                    requests.post(APPS_SCRIPT_URL, json=payload)
                    st.success(f"🎉 {new_name} added successfully!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save guest: {e}")
            else:
                st.error("Please enter a guest name.")

# TAB 3: Send Invites & Bulk Dispatch
with tab3:
    st.subheader("✉️ Send Digital Invites & RSVP Management")
    
    st.markdown("### 📢 Bulk Email Dispatcher")
    if st.button("📩 Send Invites to ALL Guests At Once"):
        if df.empty:
            st.warning("Guest list is currently empty.")
        else:
            success_count = 0
            fail_count = 0
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            valid_guests = df[df["Email"].str.contains("@", na=False)]
            total_valid = len(valid_guests)
            
            if total_valid == 0:
                st.error("No guests found with valid email addresses.")
            else:
                for idx, row in valid_guests.reset_index().iterrows():
                    g_name = row["Guest Name"]
                    g_email = row["Email"]
                    
                    status_text.text(f"Sending invitation to {g_name} ({g_email})...")
                    ok, msg = send_real_email(g_email, g_name)
                    
                    if ok:
                        success_count += 1
                    else:
                        fail_count += 1
                    
                    progress_bar.progress((idx + 1) / total_valid)
                    time.sleep(0.5)
                
                status_text.empty()
                progress_bar.empty()
                st.success(f"🎉 Batch complete! Sent {success_count} emails successfully.")

    st.markdown("---")
    st.markdown("### 👤 Individual Guest Options")
    guest_names = [g for g in df["Guest Name"].dropna().tolist() if str(g).strip() != ""] if not df.empty else []
    if guest_names:
        selected_guest_rsvp = st.selectbox("Select Guest for Single Invite / RSVP:", guest_names)
        guest_rows = df[df["Guest Name"] == selected_guest_rsvp]
        if not guest_rows.empty:
            guest_row = guest_rows.iloc[0]
            st.write(f"**Confirmation Status:** `{guest_row.get('Confirmation', 'Pending')}`")
            st.write(f"**Phone Number:** `{guest_row.get('Phone Number', '-')}`")
            st.write(f"**Email Address:** `{guest_row.get('Email', '-')}`")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("👍 Mark as Attending"):
                    requests.post(APPS_SCRIPT_URL, json={"action": "update_rsvp", "name": selected_guest_rsvp, "confirmation": "Attending"})
                    st.success("Updated to Attending!")
                    time.sleep(1)
                    st.rerun()
            with c2:
                if st.button("👎 Mark as Not Attending"):
                    requests.post(APPS_SCRIPT_URL, json={"action": "update_rsvp", "name": selected_guest_rsvp, "confirmation": "Not Attending"})
                    st.error("Updated to Not Attending.")
                    time.sleep(1)
                    st.rerun()

            st.markdown("---")
            guest_email = guest_row.get('Email', '-')
            if st.button("🚀 Send Single Email Invitation"):
                if guest_email and guest_email != "-":
                    success, msg = send_real_email(guest_email, selected_guest_rsvp)
                    if success:
                        st.success(f"Invitation sent to {guest_email}!")
                    else:
                        st.error(f"Failed to send: {msg}")
                else:
                    st.error("Please enter a valid email address for this guest.")

# TAB 4: QR Code Tickets
with tab4:
    st.subheader("🎟️ Generate Guest QR Ticket")
    guest_names = [g for g in df["Guest Name"].dropna().tolist() if str(g).strip() != ""] if not df.empty else []
    if guest_names:
        selected_guest = st.selectbox("Select guest:", guest_names, key="qr_select")
        if selected_guest:
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(f"WEDDING_TICKET:{selected_guest}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="#8B0032", back_color="white")
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"Ticket for {selected_guest}", width=250)

# TAB 5: Scan Ticket (Smart Check-in & Duplicate Detection)
with tab5:
    st.subheader("📷 Scan Ticket QR Code")
    st.markdown("Use your camera or enter scanned ticket text to verify guest entry.")
    
    scan_input = st.camera_input("Scan QR Code via Camera")
    
    # Fallback text input option for quick manual testing if camera scanner reads code as text
    manual_qr_text = st.text_input("Or paste/type scanned QR ticket data (e.g. WEDDING_TICKET:chris haule):", "")
    
    raw_data_scanned = ""
    if manual_qr_text:
        raw_data_scanned = manual_qr_text
    
    # If camera captured an image, you can integrate pyzbar/opencv here if needed, 
    # or rely on manual/barcode scanners which input text directly.
    
    if raw_data_scanned:
        if raw_data_scanned.startswith("WEDDING_TICKET:"):
            scanned_name = raw_data_scanned.split(":", 1)[1].strip()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Send to Google Sheets to check-in and verify
            payload = {
                "action": "check_in_guest",
                "name": scanned_name,
                "time": now_str
            }
            try:
                res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
                result_data = res.json()
                
                status_type = result_data.get("status")
                check_time = result_data.get("time")
                
                if status_type == "success":
                    st.success(f"✅ **CHECK-IN SUCCESSFUL!**\n\nWelcome to the wedding, **{scanned_name}**!\n\n🕒 Checked in at: {check_time}")
                    time.sleep(2)
                    st.rerun()
                elif status_type == "already_checked_in":
                    st.warning(f"⚠️ **ALREADY CHECKED IN!**\n\n**{scanned_name}** has already entered the venue.\n\n🕒 Original check-in time: {check_time}")
                else:
                    st.error(f"❌ **GUEST NOT FOUND:** '{scanned_name}' is not in the guest list.")
            except Exception as e:
                st.error(f"Error communicating with Google Sheets: {e}")
        else:
            st.error("❌ **Invalid Ticket:** Scanned QR code does not belong to this wedding system.")
