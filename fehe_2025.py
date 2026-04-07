
#!/usr/bin/env python
# coding: utf-8
# !pip install twilio
import pandas as pd
import sys
import streamlit as st
import os
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
import time

# ------------------------
# Config / Input paths
# ------------------------
csv_path = "comp_tt_040426.csv"
# csv_path = "fehe_final_26.csv"
 # ------------------------
# AUTO-DETECT FILE UPDATE
 # ------------------------
file_modified_time = os.path.getmtime(csv_path)
last_updated = datetime.fromtimestamp(file_modified_time)
aamusted_logo = "AAMUSTED-LOGO.jpg"
nsorhwebere_logo = "nsorhwebere_logo.png"
developer_info = "Note there may be errors(confirm with FEHE official timetable)👨‍💻 Developed by: Patrick Nii Lante Lamptey | 📞 +233-208 426 593"

# Load timetable
# timetable = pd.read_csv(csv_path, encoding="windows-1252")
def load_csv_safely(path):
    encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252"]

    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue

    raise ValueError("❌ Could not read the CSV file with known encodings")

timetable = load_csv_safely(csv_path)
# timetable = pd.read_csv(csv_path, encoding="utf-8-sig")
# Clean DAY & DATE column
timetable['DAY & DATE'] = timetable['DAY & DATE'].astype(str)

# Remove extra spaces everywhere
timetable['DAY & DATE'] = timetable['DAY & DATE'].str.replace(r'\s+', ' ', regex=True)

# Remove spaces after commas
timetable['DAY & DATE'] = timetable['DAY & DATE'].str.replace(r',\s+', ', ', regex=True)

# Final trim
timetable['DAY & DATE'] = timetable['DAY & DATE'].str.strip()
timetable['DATE_ONLY'] = timetable['DAY & DATE'].str.extract(r'([A-Za-z]+ \d{1,2}, \d{4})')[0]
timetable['DATE_ONLY'] = pd.to_datetime(timetable['DATE_ONLY'], format='%B %d, %Y', errors='coerce')

timetable.columns = timetable.columns.str.strip()
timetable = timetable.loc[:, ~timetable.columns.str.contains('^Unnamed')]

# ------------------------
# Convert DAY & DATE and TIME to proper sortable types
# ------------------------
# Extract start time
timetable['START_TIME'] = timetable['TIME'].str.extract(r'(\d{1,2}[:.]\d{2})')[0]
timetable['START_TIME'] = pd.to_datetime(timetable['START_TIME'], format='%H:%M', errors='coerce').dt.time

# Sort timetable
timetable_sorted = timetable.sort_values(by=['DATE_ONLY', 'START_TIME']).reset_index(drop=True)
# ------------------------
# Group colors
# ------------------------
GROUP_COLORS = ["#FFF2CC", "#D9EAD3", "#F4CCCC", "#CFE2F3", "#EAD1DC", "#FDEBD0"]

def compute_group_row_colors(df, key_cols=None):
    if key_cols is None:
        key_cols = ['DAY & DATE', 'TIME', 'COURSE CODE', 'FACULTY','DEPARTMENT']

    key_cols = [c for c in key_cols if c in df.columns]
    if not key_cols:
        return {}

    group_colors = {}
    color_idx = 0
    grouped = df.groupby(key_cols, sort=False)
    for _, group in grouped:
        if len(group) > 1:
            color = GROUP_COLORS[color_idx % len(GROUP_COLORS)]
            color_idx += 1
            for idx in group.index:
                group_colors[idx] = color
    return group_colors

# ------------------------
# Jupyter mode
# ------------------------
def run_jupyter_mode():
    from IPython.display import display, Image
    # try:
    #     display(Image(filename=logo_path, width=180))
    # except Exception:
    #     pass

    df_sorted = timetable_sorted.copy()
    row_colors = compute_group_row_colors(df_sorted)

    styles = pd.DataFrame("", index=df_sorted.index, columns=df_sorted.columns)
    for idx, color in row_colors.items():
        styles.loc[idx, :] = f"background-color: {color}"

    # Display logos side by side
    col1, col2 = st.columns([1, 5])
    with col1:
        try:
            st.image("Nsorhwebere_logo.png", width=120)
        except Exception:
            st.warning("Nsorhwebere logo not found.")
    with col2:
        try:
            st.image("AAMUSTED-LOGO.jpg", width=120)
        except Exception:
            st.warning("USTEDlogo not found.")

    st.title("Nsorhwebere - FEHE USTED-M 2nd Semester 2025 Examination Timetable")

    # df_display = df_sorted.copy()
    df_display = timetable_sorted.copy()
    # if "DAY & DATE" in df_display.columns:
    #     df_display["DAY & DATE"] = df_display["DAY & DATE"].mask(df_display["DAY & DATE"].duplicated())

    header_style = [{
        'selector': 'thead th',
        'props': [('background-color', '#4CAF50'),
                  ('color', 'white'),
                  ('font-weight', 'bold'),
                  ('text-align', 'center')]
    }]

    styler = df_display.style.set_table_styles(header_style)
    styler = styler.apply(lambda _: styles, axis=None)

    display(styler)
    print("\n" + developer_info)
def save_subscriber(email):
    try:
        with open("subscribers.txt", "a") as f:
                f.write(email + "\n")
    except:
        pass
   
# def send_update_notifications():
#     try:
#         with open("subscribers.txt", "r") as f:
#             emails = list(set([line.strip() for line in f.readlines()]))

#         email_sender = st.secrets["mail"]["email"]
#         email_pass = st.secrets["mail"]["password"]

#         msg = MIMEText("📢 The FEHE timetable has been updated. Check the app for latest schedule.")
#         msg["Subject"] = "📅 Timetable Updated"
#         msg["From"] = email_sender

#         with smtplib.SMTP("smtp.gmail.com", 587) as server:
#             server.starttls()
#             server.login(email_sender, email_pass)

#             for email in emails:
#                 msg["To"] = email
#                 server.sendmail(email_sender, email, msg.as_string())

#     except Exception as e:
#         print("Email error:", e)
# from twilio.rest import Client

# def send_whatsapp_notifications():
#     try:
#         with open("subscribers.txt", "r") as f:
#             numbers = list(set([line.strip() for line in f.readlines()]))

#         client = Client(st.secrets["twilio"]["account_sid"],
#                         st.secrets["twilio"]["auth_token"])

#         for number in numbers:
#             client.messages.create(
#                 body="📢 FEHE Timetable Updated!\nCheck the app now.",
#                 from_="whatsapp:+14155238886",  # Twilio sandbox number
#                 to=f"whatsapp:{number}"
#             )

#     except Exception as e:
#         print("WhatsApp error:", e)
import requests

# def send_whatsapp_notifications():
#     with open("subscribers.txt", "r") as f:
#         numbers = list(set([line.strip() for line in f.readlines()]))

#     for number in numbers:
#         url = f"https://api.callmebot.com/whatsapp.php?phone={number}&text=📢 Timetable Updated! Check app&apikey=1234567"
#         requests.get(url)
def send_whatsapp_notifications():
    if not os.path.exists("subscribers.txt"):
        return  # No subscribers yet → do nothing

    with open("subscribers.txt", "r") as f:
        numbers = list(set([line.strip() for line in f.readlines()]))

    for number in numbers:
        url = f"https://api.callmebot.com/whatsapp.php?phone={number}&text=📢 Timetable Updated! Check app&apikey=YOUR_API_KEY"
        requests.get(url)
def get_last_sent_time():
    try:
        with open("last_update.txt", "r") as f:
            return float(f.read().strip())
    except:
        return None

def save_last_sent_time(timestamp):
    with open("last_update.txt", "w") as f:
        f.write(str(timestamp))
# ------------------------
# Streamlit mode
# ------------------------
def run_streamlit_mode():
    import streamlit as st
    import smtplib
    from email.mime.text import MIMEText

    st.set_page_config(page_title="DEMO FEHE USTED-M Exam Timetable", layout="wide")
    st.toast("🚀 New timetable update available!", icon="🔥")

    # ------------------------
    # UPDATE ALERT SYSTEM ✅
    # ------------------------
    APP_VERSION = "1.1.0"

    WHATS_NEW = """
    ### 🚀 New Updates
      """

    # ------------------------
    # UPDATE ALERT (SAFE VERSION)
    # ------------------------
    def show_update_alert():
        if "last_seen_update" not in st.session_state:
            st.session_state["last_seen_update"] = None

        if st.session_state["last_seen_update"] != file_modified_time:

            st.toast("🚀 New timetable update available!", icon="🔥")

            st.warning("⚠️ A new timetable update has been detected.")
            st.info(f"🕒 Last Updated: {last_updated.strftime('%A, %d %B %Y %I:%M %p')}")

            st.markdown(WHATS_NEW)

            if st.button("Dismiss Update", key="dismiss_update_btn"):
                st.session_state["last_seen_update"] = file_modified_time
    show_update_alert()

    # Display two logos at opposite ends
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        try:
            st.image(nsorhwebere_logo, width=150)
        except Exception:
                st.warning("Nsorhwebere logo not found.")
    with col3:
        try:
            st.image(aamusted_logo, width=120)
        except Exception:
            st.warning("USTED logo not found.")

    st.title("Nsorhwebere - FEHE USTED-M 1st Semester 2026 Examination Timetable")

    # ------------------------
    # Clean TIME BEFORE sorting
    # ------------------------
    timetable['TIME'] = timetable['TIME'].astype(str)
    timetable['TIME'] = timetable['TIME'].str.replace('.', ':', regex=False)
    timetable['TIME'] = timetable['TIME'].str.replace(r'[–—−]', '-', regex=True)
    timetable['TIME'] = timetable['TIME'].str.replace(r'\s*-\s*', '-', regex=True)
    timetable['TIME'] = timetable['TIME'].str.strip()
    # ------------------------
    # Sidebar filters
    # ------------------------
    st.sidebar.header("🔎 Filter Timetable")

    faculties = ["All"] + sorted(timetable["FACULTY"].dropna().unique().tolist())
    departments = ["All"] + sorted(timetable["DEPARTMENT"].dropna().unique().tolist())
    levels = ["All"] + sorted(timetable["LEVEL"].dropna().unique().tolist())
    days = ["All"] + timetable_sorted["DAY & DATE"].dropna().unique().tolist()
    times = ["All"] + sorted(timetable["TIME"].dropna().unique().tolist())
    invigilators = ["All"]
    if "INVIG" in timetable.columns:
        invigilators += sorted(timetable["INVIG"].dropna().unique().tolist())

    faculty_filter = st.sidebar.selectbox("Select Faculty", faculties)
    dept_filter = st.sidebar.selectbox("Select Department", departments)
    level_filter = st.sidebar.selectbox("Select Level/Class", levels)
    day_filter = st.sidebar.selectbox("Select Day", days)
    time_filter = st.sidebar.selectbox(
        "Select Time (note: not all times appear by default)", times
    )
    inv_filter = st.sidebar.selectbox("Select Invigilator", invigilators)

    # ------------------------
    # Apply filters
    # ------------------------
    # filtered = timetable_sorted.copy()
    filtered = timetable.copy()

    if faculty_filter != "All":
        filtered = filtered[filtered["FACULTY"] == faculty_filter]
    if dept_filter != "All":
        filtered = filtered[filtered["DEPARTMENT"] == dept_filter]
    if level_filter != "All":
        filtered = filtered[filtered["LEVEL"] == level_filter]
    if day_filter != "All":
        filtered = filtered[filtered["DAY & DATE"] == day_filter]
    if time_filter != "All":
        filtered = filtered[filtered["TIME"] == time_filter]
    if "INVIG" in filtered.columns and inv_filter != "All":
        filtered = filtered[filtered["INVIG"] == inv_filter]

    # ------------------------
    # Sort chronologically by DATE and START_TIME
    # ------------------------
    filtered = filtered.sort_values(by=['DATE_ONLY', 'START_TIME']).reset_index(drop=True)
    # Drop internal sorting columns
    display_df = filtered.drop(columns=['DATE_ONLY', 'START_TIME'], errors='ignore')

    # ------------------------
    # Render table with group colors
    # ------------------------
    def render_table_html_for_streamlit(df):
        possible_cols = ["DAY & DATE", "TIME", "LEVEL", "COURSE CODE", "COURSE TITLE",
                         "TOTAL STDS", "NO. OF STDS", "VENUE", "INVIG.", "FACULTY", "DEPARTMENT"]
        display_cols = [c for c in possible_cols if c in df.columns]

        row_colors = compute_group_row_colors(df)

        df_display = df.copy()
        if "DAY & DATE" in df_display.columns:
            # Mask only consecutive duplicates
            df_display["DAY & DATE"] = df_display["DAY & DATE"].mask(
                df_display["DAY & DATE"].shift() == df_display["DAY & DATE"]
            )

        th_style = "background:#4CAF50;color:white;padding:8px;text-align:center;"
        td_style = "padding:8px;border-bottom:1px solid #ddd;vertical-align:top;"

        html = "<div style='overflow-x:auto;'><table style='border-collapse:collapse;width:100%;'>"
        html += "<thead><tr>"
        for col in display_cols:
            html += f"<th style='{th_style}'>{col}</th>"
        html += "</tr></thead><tbody>"

        for idx, row in df_display.iterrows():
            row_color = row_colors.get(idx, "")
            tr_style = f"background:{row_color};" if row_color else ""
            html += f"<tr style='{tr_style}'>"
            for col in display_cols:
                val = row.get(col, "")
                cell = "" if pd.isna(val) else str(val)
                html += f"<td style='{td_style}'>{cell}</td>"
            html += "</tr>"
        html += "</tbody></table></div>"
        return html

    html_table = render_table_html_for_streamlit(display_df)
    st.markdown("### 📅 Filtered Timetable", unsafe_allow_html=True)
    st.markdown(html_table, unsafe_allow_html=True)

    # ------------------------
    # Subscription form
    # ------------------------
    st.sidebar.header("🔔 Subscribe for Time Table Updates & Exam Alerts")
    # student_email = st.sidebar.text_input("Enter your email")
    student_phone = st.sidebar.text_input("Enter WhatsApp number (e.g. +233XXXXXXXXX)")
    subscribe = st.sidebar.button("Subscribe")
    if subscribe:
        if student_phone:
            save_subscriber(student_phone)
            st.sidebar.success("✅ Subscribed for WhatsApp alerts!")
        else:
            st.sidebar.warning("⚠️ Enter a valid phone number")
# def save_subscriber(phone):
#     try:
#         with open("subscribers.txt", "a") as f:
#             f.write(phone + "\n")
#     except:
#         pass
def save_subscriber(phone):
    with open("subscribers.txt", "a") as f:
        f.write(phone + "\n")
  
# ------------------------
# SMART EMAIL ALERT SYSTEM ✅
# ------------------------
MIN_INTERVAL = 300  # 5 minutes

if "last_sent_time" not in st.session_state:
    st.session_state["last_sent_time"] = 0

# Only send if file updated AND enough time passed
if file_modified_time > st.session_state["last_sent_time"]:
    if (time.time() - st.session_state["last_sent_time"]) > MIN_INTERVAL:
        # send_update_notifications()
        send_whatsapp_notifications()

        st.session_state["last_sent_time"] = time.time()
        st.success("📧 Update notification sent!")

st.markdown("---")
st.markdown(f"<div style='text-align:center;color:gray'>{developer_info}</div>", unsafe_allow_html=True)

# ------------------------
# Auto-detect environment
# ------------------------
if "streamlit" in sys.modules:
    run_streamlit_mode()
else:
    run_jupyter_mode()

