#!/usr/bin/env python3
"""
Smart College AI Management Platform Server
Serves static frontend assets and provides a rich REST API + Authentication + AI Chatbot engine.
Pre-configured for Supabase Project: https://aqfqdjhddfvyprpwccyp.supabase.co
"""

import http.server
import socketserver
import json
import os
import re
import urllib.parse
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DATA_DIR = os.path.join(BASE_DIR, 'data')
SUPABASE_DIR = os.path.join(BASE_DIR, 'supabase')

STUDENTS_FILE = os.path.join(DATA_DIR, 'students.json')
STAFF_FILE = os.path.join(DATA_DIR, 'staff.json')
SCHEMA_FILE = os.path.join(SUPABASE_DIR, 'supabase_schema.sql')

SUPABASE_PROJECT_URL = "https://aqfqdjhddfvyprpwccyp.supabase.co"

# ── SMTP Email Configuration ─────────────────────────────────────────────────
# Set SMTP_ENABLED=True and fill in credentials to send real emails.
# If False, emails are logged to data/email_log.json (simulation mode).
SMTP_ENABLED   = False          # flip to True once you add Gmail App Password
SMTP_HOST      = "smtp.gmail.com"
SMTP_PORT      = 587
SMTP_USER      = ""             # e.g. "your.staff@gmail.com"
SMTP_PASSWORD  = ""             # Gmail App Password (16-char)
EMAIL_LOG_FILE = os.path.join(DATA_DIR, 'email_log.json')

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def send_email_to_students(from_staff, recipients, subject, body):
    """
    Send emails from staff email to a list of student dicts.
    If SMTP_ENABLED is False, logs to data/email_log.json instead.
    Returns (success_count, fail_list, log_entries)
    """
    sent = []
    failed = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for student in recipients:
        entry = {
            'timestamp': timestamp,
            'from': from_staff.get('email', SMTP_USER),
            'from_name': from_staff.get('full_name', 'Staff'),
            'to': student['email'],
            'to_name': student['full_name'],
            'subject': subject,
            'body': body,
            'sent': False
        }

        if SMTP_ENABLED and SMTP_USER and SMTP_PASSWORD:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From']    = f"{from_staff.get('full_name', 'Staff')} <{SMTP_USER}>"
                msg['To']      = student['email']
                msg.attach(MIMEText(body, 'plain'))
                context = ssl.create_default_context()
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_USER, student['email'], msg.as_string())
                entry['sent'] = True
                sent.append(student['email'])
            except Exception as e:
                entry['error'] = str(e)
                failed.append({'email': student['email'], 'error': str(e)})
        else:
            # Simulation mode — just log
            entry['sent'] = True   # treated as "queued"
            sent.append(student['email'])

        # Append to email log
        logs = []
        if os.path.exists(EMAIL_LOG_FILE):
            try:
                with open(EMAIL_LOG_FILE, 'r') as f:
                    logs = json.load(f)
            except Exception:
                logs = []
        logs.append(entry)
        save_json(EMAIL_LOG_FILE, logs)

    return len(sent), failed, sent


def authenticate_user(role, identifier, password):
    """
    Authenticate user via ID or Email + Password.
    Returns (user_obj, error_msg)
    """
    ident = identifier.strip().lower()
    pwd = password.strip()


    if role == 'student':
        students = load_json(STUDENTS_FILE)
        for s in students:
            if s['student_id'].lower() == ident or s['email'].lower() == ident:
                if s['password'] == pwd:
                    return s, None
                else:
                    return None, "Incorrect password for this student account."
        return None, f"No student found with ID or Email '{identifier}'."

    elif role == 'staff':
        staff_members = load_json(STAFF_FILE)
        for st in staff_members:
            if st['staff_id'].lower() == ident or st['email'].lower() == ident:
                if st['password'] == pwd:
                    return st, None
                else:
                    return None, "Incorrect password for this faculty/staff account."
        return None, f"No faculty/staff member found with ID or Email '{identifier}'."

    return None, "Invalid role specified."

def generate_ai_response(query, user_context=None, role='student'):
    """
    Intelligent campus chatbot knowledge engine.
    Matches natural language queries against student context, faculty database,
    and institutional policies.
    """
    q = query.lower().strip()
    students = load_json(STUDENTS_FILE)
    staff_members = load_json(STAFF_FILE)
    
    current_student = None
    current_staff = None

    if role == 'student':
        if isinstance(user_context, dict):
            current_student = user_context
        elif isinstance(user_context, str):
            for s in students:
                if s['student_id'].lower() == user_context.lower():
                    current_student = s
                    break
        if not current_student and students:
            current_student = students[0]
    else:
        if isinstance(user_context, dict):
            current_staff = user_context
        elif isinstance(user_context, str):
            for st in staff_members:
                if st['staff_id'].lower() == user_context.lower():
                    current_staff = st
                    break
        if not current_staff and staff_members:
            current_staff = staff_members[0]

    # STAFF COPILOT QUERIES
    if role == 'staff' and current_staff:
        dept = current_staff['department']
        dept_students = [s for s in students if s['department'] == dept]

        # ── CGPA / PERFORMANCE FILTER (e.g. "students above 7", "top performers") ──
        cgpa_keywords = ['above', 'cgpa', 'high performer', 'top student', 'merit', 'distinction',
                         'topper', 'rank', 'score', 'achiever', 'performance']
        if any(k in q for k in cgpa_keywords):
            # Extract numeric threshold from query; default 7.0
            nums = re.findall(r'\d+\.?\d*', q)
            threshold = float(nums[0]) if nums else 7.0
            scope = students if any(k in q for k in ['all', 'college', 'everyone']) else dept_students
            top = sorted([s for s in scope if s.get('cgpa', 0) >= threshold],
                         key=lambda x: x['cgpa'], reverse=True)
            if not top:
                return (
                    f"🔍 No students with CGPA ≥ {threshold} found in {'all departments' if scope is students else dept} department.\n\n"
                    f"*Try lowering the threshold, e.g. 'students above 6.5'.*"
                )
            rows = []
            for i, s in enumerate(top, 1):
                att_flag = "🔴" if s['attendance_pct'] < 75 else ("🟡" if s['attendance_pct'] < 85 else "🟢")
                rows.append(
                    f"{i}. **{s['full_name']}** (`{s['student_id']}`) — "
                    f"CGPA **{s['cgpa']}** | Attendance {att_flag} **{s['attendance_pct']}%** | "
                    f"📧 {s['email']} | 📱 {s['phone']}"
                )
            table = "\n".join(rows)
            email_hint = f"\n\n💡 *To auto-email these {len(top)} students, type:* **send email to students above {threshold}**"
            return (
                f"🏆 **Top Performers — CGPA ≥ {threshold}**"
                f"{'  (All Departments)' if scope is students else f'  ({dept} Department)'}"
                f" — {len(top)} student(s):\n\n"
                f"{table}"
                f"{email_hint}"
            )

        # ── AUTO EMAIL to students above a CGPA threshold ──────────────────────
        email_trigger = any(k in q for k in ['send email', 'send mail', 'mail to', 'notify', 'send notification', 'email to'])
        if email_trigger:
            nums = re.findall(r'\d+\.?\d*', q)
            threshold = float(nums[0]) if nums else 7.0
            scope = students if any(k in q for k in ['all', 'college', 'everyone']) else dept_students
            targets = [s for s in scope if s.get('cgpa', 0) >= threshold]
            if not targets:
                return f"📭 No students with CGPA ≥ {threshold} found to email."
            subject = f"Academic Performance Notification — CGPA ≥ {threshold}"
            body = (
                f"Dear Student,\n\n"
                f"Congratulations! You have been identified as a top performer with a CGPA of {{cgpa}} or above.\n\n"
                f"We encourage you to continue your excellent academic journey. "
                f"Please visit the college portal for scholarship and internship opportunities.\n\n"
                f"Regards,\n{current_staff['full_name']}\n{current_staff['designation']}, {dept}\n"
                f"{current_staff['email']}"
            )
            # Personalise body per student
            count, failed_list, sent_list = send_email_to_students(
                current_staff,
                targets,
                subject,
                body
            )
            mode_note = "📤 **SMTP Simulation Mode** — Emails logged to `data/email_log.json`." if not SMTP_ENABLED else "✅ **Emails sent via SMTP.**"
            fail_note = f"\n⚠️ Failed: {', '.join([f['email'] for f in failed_list])}" if failed_list else ""
            return (
                f"📧 **Email Dispatch Report** — Students with CGPA ≥ {threshold}:\n\n"
                f"- **Emails Sent**: **{count}** of {len(targets)}\n"
                f"- **Recipients**: {', '.join([s['email'] for s in targets])}\n"
                f"- **Subject**: *{subject}*\n"
                f"- {mode_note}"
                f"{fail_note}\n\n"
                f"💡 *To enable real email delivery, set `SMTP_ENABLED = True` and add your Gmail App Password in `server.py`.*"
            )

        # ── ATTENDANCE ROSTER & AT-RISK STUDENTS ───────────────────────────────
        if any(k in q for k in ['student', 'roster', 'class', 'list', 'shortage', 'at risk', 'attendance']):
            at_risk = [s for s in dept_students if s['attendance_pct'] < 75]
            risk_names = ", ".join([f"{s['full_name']} ({s['attendance_pct']}%)" for s in at_risk]) or "None (all above 75%)"
            return (
                f"👨‍🏫 **Faculty Roster Overview for {current_staff['full_name']}** ({dept}):\n\n"
                f"- **Total Department Students**: {len(dept_students)}\n"
                f"- **Students with Attendance Shortage (<75%)**: **{len(at_risk)}**\n"
                f"- **At-Risk Students**: {risk_names}\n\n"
                f"💡 *You can update attendance records or send attendance notifications directly from the Roster desk.*\n"
                f"💡 *Ask me: 'students above 7' to see top performers, or 'send email to students above 7' to notify them.*"
            )

        if any(k in q for k in ['cabin', 'office hours', 'schedule', 'timing']):
            return (
                f"📍 **Your Registered Academic Schedule**:\n\n"
                f"- **Cabin Location**: `{current_staff['cabin_location']}`\n"
                f"- **Designation**: {current_staff['designation']} ({dept})\n"
                f"- **Specialization**: {current_staff['specialization']}\n"
                f"- **Designated Office Hours**: {current_staff['office_hours']}\n"
                f"- **Official Email**: [{current_staff['email']}](mailto:{current_staff['email']})"
            )

        # ── STAFF COPILOT DEFAULT HELP ──────────────────────────────────────────
        return (
            f"🤖 **Campus AI Copilot** — Hi **{current_staff['full_name']}**!\n\n"
            f"I can help you with:\n"
            f"- 🔹 *'Show students above 7 CGPA'* — list top performers with full details\n"
            f"- 🔹 *'Students above 8.5'* — filter by any CGPA threshold\n"
            f"- 🔹 *'Send email to students above 7'* — auto-email high achievers\n"
            f"- 🔹 *'Show class roster / attendance shortage'* — at-risk students\n"
            f"- 🔹 *'My cabin / office hours / schedule'* — your timetable\n"
            f"- 🔹 *'Who is the HOD of CSE?'* — faculty directory"
        )


    if current_student:
        # 1. ATTENDANCE INQUIRIES & "CAN I SKIP"
        if any(k in q for k in ['skip', 'miss', 'absent', 'bunk', 'can i miss']):
            target_subject = None
            for subj in current_student.get('subjects', []):
                if any(term in q for term in [subj['name'].lower(), subj['code'].lower(), 'dbms' if 'dbms' in subj['name'].lower() or 'database' in subj['name'].lower() else '###']):
                    target_subject = subj
                    break
            
            if target_subject:
                att = target_subject['attended']
                tot = target_subject['total']
                pct = target_subject['pct']
                new_pct = round((att / (tot + 1)) * 100, 1)
                needed_safe = max(0, int((0.8 * tot - att) / 0.2) + 1)
                
                if new_pct < 75.0:
                    return (
                        f"⚠️ **Attendance Alert for {target_subject['name']}**:\n\n"
                        f"- Current Status: **{att}/{tot} sessions ({pct}%)**.\n"
                        f"- If you skip today's lecture, your attendance drops to **{new_pct}%**, which falls **below the 75% examination cutoff**!\n"
                        f"- 💡 **Recommendation**: Attend today. You need **{needed_safe} more consecutive session(s)** to reach the 80% safe zone."
                    )
                else:
                    return (
                        f"ℹ️ **Attendance Forecast for {target_subject['name']}**:\n\n"
                        f"- Current Status: **{att}/{tot} sessions ({pct}%)**.\n"
                        f"- If you miss 1 class, your projected attendance will be **{new_pct}%** (above 75%).\n"
                        f"- 💡 Stay regular to ensure seamless hall ticket clearance."
                    )
            else:
                return (
                    f"📊 **Overall Attendance Summary for {current_student['full_name']}**:\n\n"
                    f"- Cumulative Attendance: **{current_student['attendance_pct']}%**\n"
                    f"- Minimum Cutoff: **75.0%**\n"
                    f"- Mention the subject name (e.g., *'Can I skip DBMS?'*) to get an exact session-by-session forecast."
                )

        # 2. OVERALL ATTENDANCE OR SUBJECT BREAKDOWN
        if any(k in q for k in ['attendance', 'percentage', 'classes missed', 'attendance status']):
            subj_lines = []
            for s in current_student.get('subjects', []):
                flag = "🟢 Safe" if s['pct'] >= 85 else ("🟡 Watchlist" if s['pct'] >= 75 else "🔴 Shortage")
                subj_lines.append(f"- **{s['name']}** (`{s['code']}`): **{s['pct']}%** ({s['attended']}/{s['total']} sessions) — {flag}")
            
            breakdown = "\n".join(subj_lines)
            return (
                f"📋 **Current Attendance Profile for {current_student['full_name']}** (`{current_student['student_id']}`):\n\n"
                f"**Overall Cumulative Attendance**: **{current_student['attendance_pct']}%**\n\n"
                f"**Course Breakdown**:\n{breakdown}\n\n"
                f"📌 *Note: The university requires 75% minimum attendance in every course for final examination hall tickets.*"
            )

        # 3. FEE BALANCE & DUE DATES
        if any(k in q for k in ['fee', 'dues', 'balance', 'tuition', 'pay fee', 'breakup', 'payment']):
            bal = current_student.get('fee_balance', 0)
            status = current_student.get('fee_status', 'Pending')
            if bal == 0:
                return (
                    f"✅ **Fee Status for {current_student['full_name']}**:\n\n"
                    f"- **All Semester 8 fees are completely PAID**!\n"
                    f"- Outstanding Balance: **₹0.00**\n"
                    f"- No academic holds or fee restrictions apply to your registration."
                )
            else:
                return (
                    f"💳 **Semester 8 Fee Breakdown for {current_student['full_name']}**:\n\n"
                    f"- **Outstanding Tuition Balance**: **₹{bal:,.2f}**\n"
                    f"- **Due Date**: **November 15, 2026**\n"
                    f"- **Status**: `{status}`\n"
                    f"- **Payment Methods**: UPI, Net Banking, or Credit/Debit Card.\n\n"
                    f"💡 *Tip: Clear your dues before Nov 15 to avoid late fines (₹500/week) and ensure lab access! Use the 'Pay Fees' button on your dashboard.*"
                )

        # 4. CGPA / MARKS
        if any(k in q for k in ['cgpa', 'sgpa', 'marks', 'grade', 'grading', 'rank', 'distinction']):
            tier = "Distinction Tier 🌟" if current_student['cgpa'] >= 8.5 else ("First Class with Distinction" if current_student['cgpa'] >= 7.5 else "First Class")
            return (
                f"🎓 **Academic Standing for {current_student['full_name']}**:\n\n"
                f"- **Cumulative CGPA**: **{current_student['cgpa']} / 10.0**\n"
                f"- **Academic Tier**: **{tier}**\n"
                f"- **Semester 7 SGPA**: **8.65**\n"
                f"- **Degree Program**: B.Tech {current_student['department']} (Year 4, Semester 8)"
            )

    # 5. FACULTY / HOD / CABIN / OFFICE HOURS INQUIRIES (Accessible to both students & staff)
    if any(k in q for k in ['hod', 'faculty', 'professor', 'cabin', 'office', 'teacher', 'staff', 'contact', 'dean']):
        matches = []
        for st in staff_members:
            terms = [st['full_name'].lower(), st['department'].lower(), st['designation'].lower(), st['specialization'].lower()]
            if any(part in q for term in terms for part in term.split() if len(part) > 2):
                matches.append(st)
        
        if 'cse' in q:
            matches = [st for st in staff_members if st['department'] == 'CSE' and 'HOD' in st['designation']] or matches
        elif 'it' in q:
            matches = [st for st in staff_members if st['department'] == 'IT' and 'HOD' in st['designation']] or matches
        elif 'mech' in q:
            matches = [st for st in staff_members if st['department'] == 'MECH' and 'HOD' in st['designation']] or matches
        elif 'civil' in q:
            matches = [st for st in staff_members if st['department'] == 'CIVIL' and 'HOD' in st['designation']] or matches
        elif 'eee' in q:
            matches = [st for st in staff_members if st['department'] == 'EEE' and 'HOD' in st['designation']] or matches
        elif 'de' in q or 'design' in q:
            matches = [st for st in staff_members if st['department'] == 'DE' and 'HOD' in st['designation']] or matches
        elif 'dean' in q:
            matches = [st for st in staff_members if 'Dean' in st['designation']]

        if matches:
            lead = matches[0]
            extra = f"\n\n*Found {len(matches)} matching faculty members in the directory.*" if len(matches) > 1 else ""
            return (
                f"👨‍🏫 **Faculty Information**: **{lead['full_name']}**\n\n"
                f"- **Designation**: {lead['designation']} ({lead['department']})\n"
                f"- **Specialization**: {lead['specialization']}\n"
                f"- **Office / Cabin**: `{lead['cabin_location']}`\n"
                f"- **Office Hours**: {lead['office_hours']}\n"
                f"- **Email**: [{lead['email']}](mailto:{lead['email']})\n"
                f"- **Contact**: {lead['phone']}{extra}"
            )

    # 6. CERTIFICATES & BONAFIDE
    if any(k in q for k in ['bonafide', 'certificate', 'provisional', 'transcript', 'letter', 'lor', 'apply']):
        return (
            f"📜 **Official Certificate Issuance Process**:\n\n"
            f"1. **Select Type**: Go to the **Certificates** tab or click **'Apply for Certificate'**.\n"
            f"2. **Available Documents**:\n"
            f"   - Bonafide Certificate (Passport, Visa, Bank Loan, Bus Pass)\n"
            f"   - Provisional Degree Certificate\n"
            f"   - Course Completion Letter\n"
            f"   - Semester Grade Cards / Transcripts\n"
            f"3. **Turnaround**: Digitally signed within **24 to 48 hours** by Dean of Academics."
        )

    # DEFAULT FALLBACK
    name = current_student['full_name'] if current_student else (current_staff['full_name'] if current_staff else "there")
    return (
        f"👋 Hi **{name}**! I am your **Smart College AI Assistant**.\n\n"
        f"You can ask me questions such as:\n"
        f"- 🔹 *'Can I skip DBMS today?'*\n"
        f"- 🔹 *'What is my tuition fee balance and deadline?'*\n"
        f"- 🔹 *'Who is the HOD of CSE / IT / MECH?'*\n"
        f"- 🔹 *'Where is Dr. Rajesh Raman's cabin?'*\n"
        f"- 🔹 *'How do I apply for a Bonafide Certificate?'*"
    )


class CollegeAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Supabase-Key')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Supabase-Key')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # 1. API CONFIG & SUPABASE STATUS
        if path == '/api/config':
            self._send_json({
                'supabase_project_url': SUPABASE_PROJECT_URL,
                'status': 'online',
                'app_name': 'Smart College AI Digital Twin OS',
                'version': '2.5.0',
                'total_students': 20,
                'total_staff': 20,
                'departments': ['CSE', 'IT', 'MECH', 'DE', 'CIVIL', 'EEE', 'ADMIN']
            })
            return

        # 2. GET STUDENTS
        if path == '/api/students':
            students = load_json(STUDENTS_FILE)
            dept = params.get('dept', [None])[0]
            search = params.get('search', [None])[0]
            if dept:
                students = [s for s in students if s['department'].upper() == dept.upper()]
            if search:
                s_lower = search.lower()
                students = [
                    s for s in students 
                    if s_lower in s['full_name'].lower() 
                    or s_lower in s['student_id'].lower() 
                    or s_lower in s['email'].lower()
                ]
            self._send_json(students)
            return

        # 2b. GET SINGLE STUDENT
        student_match = re.match(r'^/api/students/([a-zA-Z0-9]+)$', path)
        if student_match:
            sid = student_match.group(1).lower()
            students = load_json(STUDENTS_FILE)
            for s in students:
                if s['student_id'].lower() == sid or s['email'].lower() == sid:
                    self._send_json(s)
                    return
            self._send_json({'error': 'Student not found'}, 404)
            return

        # 3. GET STAFF
        if path == '/api/staff':
            staff = load_json(STAFF_FILE)
            dept = params.get('dept', [None])[0]
            search = params.get('search', [None])[0]
            if dept:
                staff = [st for st in staff if st['department'].upper() == dept.upper()]
            if search:
                s_lower = search.lower()
                staff = [
                    st for st in staff
                    if s_lower in st['full_name'].lower()
                    or s_lower in st['staff_id'].lower()
                    or s_lower in st['designation'].lower()
                    or s_lower in st['specialization'].lower()
                ]
            self._send_json(staff)
            return

        # 3b. GET SINGLE STAFF
        staff_match = re.match(r'^/api/staff/([a-zA-Z0-9]+)$', path)
        if staff_match:
            sid = staff_match.group(1).lower()
            staff = load_json(STAFF_FILE)
            for st in staff:
                if st['staff_id'].lower() == sid or st['email'].lower() == sid:
                    self._send_json(st)
                    return
            self._send_json({'error': 'Staff member not found'}, 404)
            return

        # 3c. GET STAFF COURSES & ROSTER
        staff_courses_match = re.match(r'^/api/staff/([a-zA-Z0-9]+)/courses$', path)
        if staff_courses_match:
            sid = staff_courses_match.group(1).lower()
            staff = load_json(STAFF_FILE)
            st_found = next((st for st in staff if st['staff_id'].lower() == sid), None)
            if not st_found:
                self._send_json({'error': 'Staff member not found'}, 404)
                return

            students = load_json(STUDENTS_FILE)
            dept_students = [s for s in students if s['department'] == st_found['department']]
            
            self._send_json({
                'staff': st_found,
                'department': st_found['department'],
                'courses': [
                    {'code': f"{st_found['department']}801", 'name': st_found['specialization'], 'credits': 4, 'schedule': 'Mon & Wed 10:00 AM', 'room': 'Lab 404'}
                ],
                'enrolled_students': dept_students
            })
            return

        # 4. GET ALL CERTIFICATE REQUESTS (FOR ADMIN / STAFF APPROVAL DESK)
        if path == '/api/requests/all':
            students = load_json(STUDENTS_FILE)
            all_reqs = []
            for s in students:
                for req in s.get('active_requests', []):
                    all_reqs.append({
                        **req,
                        'student_id': s['student_id'],
                        'student_name': s['full_name'],
                        'department': s['department']
                    })
            self._send_json(all_reqs)
            return

        # 5. GET SUPABASE SCHEMA SQL
        if path == '/api/supabase-schema':
            if os.path.exists(SCHEMA_FILE):
                with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="supabase_schema.sql"')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
                return
            self._send_json({'error': 'Schema file not found'}, 404)
            return


        # 3d. SERVE CERTIFICATE PDF FOR DOWNLOAD
        cert_pdf_match = re.match(r'^/certificate_([a-zA-Z0-9_]+_[a-zA-Z0-9_\-]+)\.pdf$', path, re.IGNORECASE)
        if cert_pdf_match:
            req_id = cert_pdf_match.group(1)
            pdf_filename = f"certificate_{req_id}.pdf"
            pdf_path = os.path.join(BASE_DIR, pdf_filename)
            if not os.path.exists(pdf_path):
                cert_pdf_path = f"certificate_{req_id}.pdf"
                try:
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import A4
                    from reportlab.lib.units import mm
                    c = canvas.Canvas(pdf_path, pagesize=A4)
                    w, h = A4
                    c.setFont("Helvetica-Bold", 16)
                    c.drawCentredString(w/2, h-30*mm, "CERTIFICATE")
                    c.setFont("Helvetica", 11)
                    c.drawCentredString(w/2, h-45*mm, "MVGR COLLEGE OF ENGINEERING - AUTONOMOUS")
                    c.setFont("Helvetica", 9)
                    info_lines = [
                        f"Request ID: {req_id}",
                        f"Status: Approved",
                        "This certificate has been issued by the Academic Authority.",
                        "Department of Electronics and Communication Engineering",
                    ]
                    y = h - 65*mm
                    for line in info_lines:
                        c.drawCentredString(w/2, y, line)
                        y -= 6*mm
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(w-90*mm, 35*mm, "Dean of Academics / HOD")
                    c.setStrokeColorRGB(0.1, 0.2, 0.3)
                    c.line(w-90*mm, 32*mm, w-40*mm, 32*mm)
                    c.setFont("Helvetica", 6)
                    footer_text = "VIJAYARAM NAGAR CAMPUS, CHINTALAVALASA, VIZIANAGARAM - 535005 | Ph: 08922-241037 | E-mail: hod.ece@mvgrce.edu.in | Web: www.mvgrce.edu.in"
                    c.drawCentredString(w/2, 15*mm, footer_text)
                    c.save()
                except Exception:
                    pass
            if os.path.exists(pdf_path):
                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Disposition', f'attachment; filename="Certificate_{req_id}.pdf"')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.end_headers()
                with open(pdf_path, 'rb') as f_file:
                    self.wfile.write(f_file.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error":"Certificate file not found"}')
                return

        # 6. OVERALL STATS
        if path == '/api/stats':
            students = load_json(STUDENTS_FILE)
            staff = load_json(STAFF_FILE)
            total_cgpa = sum(s['cgpa'] for s in students) if students else 0
            avg_cgpa = round(total_cgpa / len(students), 2) if students else 0
            avg_att = round(sum(s['attendance_pct'] for s in students) / len(students), 1) if students else 0
            paid_count = sum(1 for s in students if s['fee_balance'] == 0)
            
            self._send_json({
                'total_students': len(students),
                'total_staff': len(staff),
                'avg_cgpa': avg_cgpa,
                'avg_attendance': avg_att,
                'fees_cleared_ratio': f"{paid_count}/{len(students)}",
                'active_requests_count': 12,
                'server_time': datetime.now().isoformat()
            })
            return

        # Fallback to static files
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')
        if not path:
            path = '/'

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        try:
            body = json.loads(post_data)
        except Exception:
            body = {}

        # 1. AUTHENTICATION LOGIN ENDPOINT (Supports /api/auth/login, /api/login, /login)
        if path in ['/api/auth/login', '/api/login', '/api/auth', '/login']:
            role = body.get('role', 'student')
            identifier = body.get('identifier', '').strip()
            password = body.get('password', '').strip()

            if not identifier or not password:
                self._send_json({'success': False, 'error': 'Identifier and password are required.'}, 400)
                return

            user, err = authenticate_user(role, identifier, password)
            if err:
                self._send_json({'success': False, 'error': err}, 401)
                return

            token = f"token_{role}_{user.get('student_id') or user.get('staff_id')}_{int(datetime.now().timestamp())}"
            self._send_json({
                'success': True,
                'token': token,
                'role': role,
                'user': user,
                'message': f"Welcome back, {user['full_name']}!"
            })
            return

        # 2. AI CHATBOT ENDPOINT (Supports /api/chat, /api/ai/chat, /chat)
        if path in ['/api/chat', '/api/ai/chat', '/chat']:
            user_message = body.get('message', '').strip()
            user_id = body.get('user_id') or body.get('student_id', '23331a42001')
            role = body.get('role', 'student')

            if not user_message:
                self._send_json({'error': 'No message provided'}, 400)
                return
            
            reply = generate_ai_response(user_message, user_id, role)
            self._send_json({
                'query': user_message,
                'response': reply,
                'timestamp': datetime.now().strftime('%I:%M %p')
            })
            return

        # 3. FEE PAYMENT SIMULATION (Supports /api/fees/pay, /api/fee/pay, /api/pay)
        if path in ['/api/fees/pay', '/api/fee/pay', '/api/pay']:
            student_id = body.get('student_id', '23331a42001')
            amount = float(body.get('amount', 12500.0))
            method = body.get('method', 'UPI / Net Banking')
            
            students = load_json(STUDENTS_FILE)
            target = None
            for s in students:
                if s['student_id'].lower() == student_id.lower():
                    s['fee_balance'] = 0.0
                    s['fee_status'] = 'Paid'
                    s['recent_activities'].insert(0, {
                        'title': f'Fee Payment Cleared (₹{amount:,.2f})',
                        'description': f'Transaction via {method} verified • Receipt #REC-{datetime.now().strftime("%y%m%d%H%M")}',
                        'time_label': 'Just now',
                        'icon': 'receipt_long',
                        'color': 'blue'
                    })
                    target = s
                    break
            
            if target:
                save_json(STUDENTS_FILE, students)
                self._send_json({
                    'success': True,
                    'message': f'Payment of ₹{amount:,.2f} recorded successfully!',
                    'receipt_id': f'REC-{datetime.now().strftime("%y%m%d%H%M")}',
                    'updated_student': target
                })
                return
            self._send_json({'error': 'Student not found'}, 404)
            return

        # 4. APPLY FOR CERTIFICATE (Supports /api/requests, /api/request)
        if path in ['/api/requests', '/api/request']:
            student_id = body.get('student_id', '23331a42001')
            cert_type = body.get('certificate_type', 'Bonafide Certificate')
            purpose = body.get('purpose', 'Academic / Official')
            
            req_id = f'REQ-{datetime.now().strftime("%m%d%H%M")}'
            new_req = {
                'request_id': req_id,
                'certificate_type': cert_type,
                'status': 'In Review',
                'applied_date': datetime.now().strftime('%Y-%m-%d'),
                'purpose': purpose,
                'remarks': 'Dean academic clearance in progress'
            }

            students = load_json(STUDENTS_FILE)
            for s in students:
                if s['student_id'].lower() == student_id.lower():
                    s.setdefault('active_requests', []).insert(0, new_req)
                    s['recent_activities'].insert(0, {
                        'title': f'Applied for {cert_type}',
                        'description': f'Request #{req_id} submitted for review',
                        'time_label': 'Just now',
                        'icon': 'assignment_turned_in',
                        'color': 'purple'
                    })
                    save_json(STUDENTS_FILE, students)
                    self._send_json({
                        'success': True,
                        'request_id': req_id,
                        'message': f'Application for {cert_type} submitted successfully!',
                        'request': new_req
                    })
                    return
            self._send_json({'error': 'Student not found'}, 404)
            return

        # 5. STAFF APPROVAL / REJECTION OF REQUESTS
        action_match = re.match(r'^/api/requests/([a-zA-Z0-9\-_]+)/(approve|reject)$', path, re.IGNORECASE)
        if action_match:
            req_id = action_match.group(1).upper()
            action = action_match.group(2).lower()
            new_status = 'Approved' if action == 'approve' else 'Rejected'

            students = load_json(STUDENTS_FILE)
            found = False
            for s in students:
                for req in s.get('active_requests', []):
                    if req['request_id'].upper() == req_id:
                        req['status'] = new_status
                        req['remarks'] = f"Actioned by Academic Authority: {new_status} on {datetime.now().strftime('%Y-%m-%d')}"
                        found = True
                        break
                if found:
                    break

            if found:
                save_json(STUDENTS_FILE, students)
                self._send_json({
                    'success': True,
                    'request_id': req_id,
                    'status': new_status,
                    'message': f'Request {req_id} has been {new_status} successfully.'
                })
                return
            self._send_json({'error': 'Request ID not found'}, 404)
            return

        # 6. STAFF ATTENDANCE UPDATE / MARKING
        if path in ['/api/attendance/mark', '/api/attendance']:
            student_id = body.get('student_id')
            subject_name = body.get('subject_name')
            action = body.get('action', 'present') # 'present' or 'absent'

            students = load_json(STUDENTS_FILE)
            for s in students:
                if s['student_id'].lower() == student_id.lower():
                    for subj in s.get('subjects', []):
                        if subject_name.lower() in subj['name'].lower() or subj['code'].lower() in subject_name.lower():
                            subj['total'] += 1
                            if action == 'present':
                                subj['attended'] += 1
                            subj['pct'] = round((subj['attended'] / subj['total']) * 100, 1)
                            
                            all_pcts = [sub['pct'] for sub in s['subjects']]
                            s['attendance_pct'] = round(sum(all_pcts) / len(all_pcts), 1)
                            
                            save_json(STUDENTS_FILE, students)
                            self._send_json({
                                'success': True,
                                'subject': subj,
                                'overall_attendance': s['attendance_pct'],
                                'message': f"Marked {action} for {s['full_name']} in {subj['name']}."
                            })
                            return
            self._send_json({'error': 'Student or subject not found'}, 404)
            return

        # 7. MANUAL SEND EMAIL ENDPOINT (POST /api/send-email)
        # Body: { staff_id, to_cgpa_above (float), subject (optional), body_text (optional) }
        if path in ['/api/send-email', '/api/email', '/api/notify']:
            staff_id   = body.get('staff_id', '')
            threshold  = float(body.get('to_cgpa_above', 7.0))
            subject    = body.get('subject') or f"Academic Performance Notification — CGPA ≥ {threshold}"
            body_text  = body.get('body_text') or (
                f"Dear Student,\n\n"
                f"Congratulations on maintaining a CGPA of {threshold} or above!\n"
                f"Please visit the college portal for latest scholarship and internship opportunities.\n\n"
                f"Best Regards,\nSmartCollege Academic Team"
            )
            scope_all  = body.get('scope', 'dept') == 'all'
            students   = load_json(STUDENTS_FILE)
            staff_list = load_json(STAFF_FILE)

            from_staff = next((st for st in staff_list if st['staff_id'].lower() == staff_id.lower()), {})
            scope      = students if scope_all else [s for s in students if s['department'] == from_staff.get('department', '')]
            targets    = [s for s in scope if s.get('cgpa', 0) >= threshold]

            if not targets:
                self._send_json({'success': False, 'message': f'No students with CGPA ≥ {threshold} found.'}, 200)
                return

            count, failed, sent = send_email_to_students(from_staff, targets, subject, body_text)
            self._send_json({
                'success': True,
                'emails_sent': count,
                'recipients': sent,
                'failed': failed,
                'mode': 'smtp' if SMTP_ENABLED else 'simulation',
                'log_file': EMAIL_LOG_FILE,
                'message': f"{'Sent' if SMTP_ENABLED else 'Simulated'} {count} email(s) to students with CGPA ≥ {threshold}."
            })
            return

        print(f"[404 POST] Unrecognized endpoint requested: '{path}'")
        self._send_json({
            'error': f"Unknown POST endpoint '{path}'",
            'supported_endpoints': [
                '/api/auth/login',
                '/api/chat',
                '/api/fees/pay',
                '/api/requests',
                '/api/requests/<id>/approve',
                '/api/requests/<id>/reject',
                '/api/attendance/mark',
                '/api/send-email'
            ]
        }, 404)



def run_server(port=PORT):
    handler = CollegeAPIHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"==================================================")
        print("Smart College AI Digital Twin OS Running")
        print(f"Local URL: http://localhost:{port}")
        print(f"Supabase Project URL: {SUPABASE_PROJECT_URL}")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port)
