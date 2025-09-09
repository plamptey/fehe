#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import sys

# ------------------------
# Config / Input paths
# ------------------------
csv_path = "fehe_final.csv"
logo_path = "AAMUSTED-LOGO.jpg"
developer_info = "Note there may be errors(confirm with FEHE official timetable)👨‍💻 Developed by: Patrick Nii Lante Lamptey | 📞 +233-208 426 593"

# Load timetable
timetable = pd.read_csv(csv_path, encoding="windows-1252")

# Normalize TIME column (replace dots with colon, strip spaces)
# timetable['TIME'] = timetable['TIME'].str.replace('.', ':', regex=False).str.strip()
# # Normalize TIME column: remove spaces, replace different dash characters with standard dash
# timetable['TIME'] = timetable['TIME'].str.strip()
# timetable['TIME'] = timetable['TIME'].str.replace(r'[–—−]', '-', regex=True)  # replace en-dash/em-dash/minus
# timetable['TIME'] = timetable['TIME'].str.replace(r'\s*-\s*', '-', regex=True)  # remove spaces around dash

# ------------------------
# Convert DAY & DATE and TIME to proper sortable types
# ------------------------
# Extract date part (remove weekday name)
timetable['DATE_ONLY'] = timetable['DAY & DATE'].str.extract(r'(\d{1,2}\w{2} \w+, \d{4})')[0]
timetable['DATE_ONLY'] = pd.to_datetime(timetable['DATE_ONLY'], format='%d%b, %Y', errors='coerce')

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
    try:
        display(Image(filename=logo_path, width=180))
    except Exception:
        pass

    df_sorted = timetable_sorted.copy()
    row_colors = compute_group_row_colors(df_sorted)

    styles = pd.DataFrame("", index=df_sorted.index, columns=df_sorted.columns)
    for idx, color in row_colors.items():
        styles.loc[idx, :] = f"background-color: {color}"

    df_display = df_sorted.copy()
    if "DAY & DATE" in df_display.columns:
        df_display["DAY & DATE"] = df_display["DAY & DATE"].mask(df_display["DAY & DATE"].duplicated())

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

def run_streamlit_mode():
    import streamlit as st
    import smtplib
    from email.mime.text import MIMEText

    st.set_page_config(page_title="DEMO FEHE AAMUSTED-M Exam Timetable", layout="wide")

    # Display logo
    try:
        st.image(logo_path, width=140)
    except Exception:
        st.warning("Logo not found (check logo_path).")

    st.title("DEMO FEHE AAMUSTED-M 2nd Semester 2025 Examination Timetable")

    # ------------------------
    # Normalize TIME for consistent filtering
    # ------------------------
    timetable['TIME'] = timetable['TIME'].str.replace('.', ':', regex=False).str.strip()
    timetable['TIME'] = timetable['TIME'].str.replace(r'\s*-\s*', '-', regex=True)

    # ------------------------
    # Sidebar filters
    # ------------------------
    st.sidebar.header("🔎 Filter Timetable")

    faculties = ["All"] + sorted(timetable["FACULTY"].dropna().unique().tolist())
    departments = ["All"] + sorted(timetable["DEPARTMENT"].dropna().unique().tolist())
    levels = ["All"] + sorted(timetable["CLASS"].dropna().unique().tolist())
    days = ["All"] + sorted(timetable["DAY & DATE"].dropna().unique().tolist())
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
    filtered = timetable_sorted.copy()

    if faculty_filter != "All":
        filtered = filtered[filtered["FACULTY"] == faculty_filter]
    if dept_filter != "All":
        filtered = filtered[filtered["DEPARTMENT"] == dept_filter]
    if level_filter != "All":
        filtered = filtered[filtered["CLASS"] == level_filter]
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
        possible_cols = ["DAY & DATE", "TIME", "CLASS", "COURSE CODE", "COURSE TITLE",
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

