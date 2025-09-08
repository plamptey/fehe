#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import sys

# ------------------------
# Config / Input paths
# ------------------------
csv_path = "fehe_final.csv"
logo_path = "AAMUSTED-LOGO.jpg"
developer_info = "Note there may be errors (confirm with FEHE official timetable) 👨‍💻 Developed by: Patrick Nii Lante Lamptey | 📞 +233-208 426 593"

# Load timetable
timetable = pd.read_csv(csv_path, encoding="windows-1252")

# ------------------------
# Preprocess dates and times
# ------------------------
# Remove ST, ND, RD, TH from day numbers
timetable['DATE_ONLY'] = pd.to_datetime(
    timetable['DAY & DATE'].str.replace(r'(\d+)(ST|ND|RD|TH)', r'\1', regex=True),
    format='%A %d %B, %Y',
    errors='coerce'
)

# Extract start time from TIME column
timetable['START_TIME'] = pd.to_datetime(
    timetable['TIME'].str.split('-').str[0].str.replace('.', ':'),
    format='%H:%M',
    errors='coerce'
).dt.time


    # Row colors
    row_colors = compute_group_row_colors(filtered)

    # Render HTML table
    def render_table_html_for_streamlit(df):
        possible_cols = ["DAY & DATE", "TIME", "CLASS", "COURSE CODE", "COURSE TITLE",
                         "TOTAL STDS", "NO. OF STDS", "VENUE", "INVIG.", "FACULTY", "DEPARTMENT"]
        display_cols = [c for c in possible_cols if c in df.columns]

        df_display = df.copy()
        if "DAY & DATE" in df_display.columns:
            df_display["DAY & DATE"] = df_display["DAY & DATE"].mask(df_display["DAY & DATE"].duplicated())

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
                cell = "" if (pd.isna(val)) else str(val)
                html += f"<td style='{td_style}'>{cell}</td>"
            html += "</tr>"
        html += "</tbody></table></div>"

        return html

    html_table = render_table_html_for_streamlit(filtered)
    st.markdown("### 📅 Filtered Timetable", unsafe_allow_html=True)
    st.markdown(html_table, unsafe_allow_html=True)

    # Subscription form
    st.sidebar.header("🔔 Subscribe for Exam Alerts")
    student_email = st.sidebar.text_input("Enter your email")
    subscribe = st.sidebar.button("Subscribe")

    if subscribe and student_email:
        try:
            email_sender = st.secrets["mail"]["email"]
            email_pass = st.secrets["mail"]["password"]

            msg = MIMEText("✅ You are now subscribed to AAMUSTED exam alerts. Stay tuned!")
            msg["Subject"] = "Exam Timetable Subscription"
            msg["From"] = email_sender
            msg["To"] = student_email

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(email_sender, email_pass)
                server.sendmail(email_sender, [student_email], msg.as_string())

            st.sidebar.success("Subscribed! Confirmation email sent.")
        except Exception as e:
            st.sidebar.error(f"Failed to send confirmation: {e}")

    st.markdown("---")
    st.markdown(f"<div style='text-align:center;color:gray'>{developer_info}</div>", unsafe_allow_html=True)

# ------------------------
# Auto-detect environment
# ------------------------
if "streamlit" in sys.modules:
    run_streamlit_mode()
else:
    run_jupyter_mode()
