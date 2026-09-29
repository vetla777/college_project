"""
Build a project-review PDF from the Smart College AI documentation.
Uses reportlab (no external PDF engine needed) for portable Windows output.
Includes cover, TOC, architecture, data, DB schema, endpoints, test results.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Image, Flowable,
    ListFlowable, ListItem
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, Line, String
from reportlab.graphics import renderPDF
import os, textwrap, datetime

# ---------- palette ----------
NAVY = colors.HexColor("#17324d")
BLUE = colors.HexColor("#2367a8")
BLUE_SOFT = colors.HexColor("#eaf2fa")
GREEN = colors.HexColor("#287a61")
AMBER = colors.HexColor("#9a6519")
INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#647084")
LINE = colors.HexColor("#dce3ec")
PAPER = colors.HexColor("#ffffff")
GROUND = colors.HexColor("#f4f6f8")
WHITE = colors.white

# ---------- document setup ----------
FILE = "PROJECT_DOCUMENT_review.pdf"
doc = SimpleDocTemplate(
    FILE,
    pagesize=A4,
    rightMargin=14*mm, leftMargin=14*mm,
    topMargin=14*mm, bottomMargin=14*mm,
    title="Smart College AI — Project Review",
    author="Project Review (generated for academic review)",
)

styles = getSampleStyleSheet()

# Custom styles
style_title = ParagraphStyle(
    "Title", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=26, leading=30, textColor=NAVY, spaceAfter=8
)
style_sub = ParagraphStyle(
    "Sub", parent=styles["Normal"], fontSize=11, leading=15,
    textColor=MUTED, spaceAfter=14
)
style_h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=16, leading=20, textColor=NAVY, spaceBefore=10, spaceAfter=6,
    borderWidth=0, borderColor=BLUE, borderPadding=5,
    backColor=BLUE_SOFT,
)
style_h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=12.5, leading=16, textColor=BLUE, spaceBefore=14, spaceAfter=4
)
style_h3 = ParagraphStyle(
    "H3", parent=styles["Heading3"], fontName="Helvetica-Bold",
    fontSize=10.5, leading=13, textColor=NAVY, spaceBefore=10, spaceAfter=3
)
style_body = ParagraphStyle(
    "Body", parent=styles["Normal"], fontName="Helvetica",
    fontSize=9, leading=13.5, textColor=INK, spaceAfter=4
)
style_small = ParagraphStyle(
    "Small", parent=styles["Normal"], fontName="Helvetica",
    fontSize=7.5, leading=10, textColor=MUTED
)
style_caption = ParagraphStyle(
    "Caption", parent=styles["Normal"], fontName="Helvetica-Oblique",
    fontSize=8, leading=11, textColor=MUTED, spaceBefore=2, spaceAfter=8
)
style_box = ParagraphStyle(
    "Box", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8, leading=11, textColor=INK
)
style_code = ParagraphStyle(
    "Code", parent=styles["Normal"], fontName="Courier",
    fontSize=7.2, leading=9.5, textColor=colors.HexColor("#e8f0f7"),
)
style_callout = ParagraphStyle(
    "Callout", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=9, leading=12.5, textColor=AMBER, spaceAfter=2
)
style_cover_eyebrow = ParagraphStyle(
    "Eyebrow", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=8, leading=11, textColor=colors.HexColor("#75c7c0"),
    letterSpacing=2
)

# ---------- helpers ----------
def section_heading(num: str, title: str):
    return Paragraph(
        f'<font color="{BLUE.hexval()}">{num}</font> &nbsp; {title}',
        style_h1
    )

def sub_heading(title: str):
    return Paragraph(title, style_h2)

def body(text: str):
    return Paragraph(text, style_body)

def spacer(h=2):
    return Spacer(1, h*mm)

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=4, spaceAfter=4)

def callout_box(text: str, bg=BLUE_SOFT, border=BLUE, textc=INK):
    t = Table([[Paragraph(text, style_box)]], colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), 0.8, border),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    return t

def code_block(code: str):
    # Use a dark block with monospace text
    content = Paragraph(
        f'<font face="Courier" color="#e8f0f7">{code.replace("<","&lt;").replace(">","&gt;")}</font>',
        ParagraphStyle("cb", parent=style_code, fontSize=6.8, leading=9)
    )
    t = Table([[content]], colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NAVY),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    return t

def data_table(headers, rows, col_widths=None, small=True):
    s = ParagraphStyle("t", parent=style_small if small else style_body,
                       fontSize=7.2 if small else 8.2, leading=10)
    h = [Paragraph(h, ParagraphStyle("th", parent=style_small,
             fontName="Helvetica-Bold", fontSize=7.5, textColor=WHITE)) for h in headers]
    data = [h]
    for r in rows:
        data.append([Paragraph(str(c), s) for c in r])
    if col_widths is None:
        col_widths = [170*mm / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 7.5),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [PAPER, GROUND]),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    return t

# ---------- header / footer ----------
def draw_header_footer(canvas_obj, doc):
    canvas_obj.saveState()
    # Footer line
    canvas_obj.setStrokeColor(LINE)
    canvas_obj.setLineWidth(0.4)
    canvas_obj.line(14*mm, 10*mm, 210*mm-14*mm, 10*mm)
    # Footer text
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.setFillColor(MUTED)
    canvas_obj.drawString(14*mm, 5.5*mm, "SMART COLLEGE AI — PROJECT REVIEW  ·  VERSION 2.5.0  ·  D:\\test\\smart-college-management")
    canvas_obj.drawRightString(210*mm-14*mm, 5.5*mm, f"Page {doc.page}")
    # Top thin line
    canvas_obj.setStrokeColor(BLUE)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(14*mm, 287*mm, 210*mm-14*mm, 287*mm)
    canvas_obj.restoreState()

# ---------- CONTENT ----------
story = []

# ---- COVER PAGE ----
story.append(Spacer(1, 10*mm))
story.append(Paragraph("DIGITAL TWIN OS  ·  REVIEW EDITION", style_cover_eyebrow))
story.append(Spacer(1, 6*mm))
story.append(Paragraph("Smart College AI", style_title))
story.append(Paragraph("Project Review Document", style_sub))
story.append(Spacer(1, 4*mm))
story.append(hr())
story.append(Spacer(1, 8*mm))

# Cover facts block (2-col table)
cover_facts = [
    [Paragraph("<b>VERSION</b>", ParagraphStyle("cf", parent=style_small, fontName="Helvetica-Bold", textColor=NAVY)),
     Paragraph("2.5.0", ParagraphStyle("cf2", parent=style_small, textColor=INK))],
    [Paragraph("<b>BACKEND</b>", ParagraphStyle("cf", parent=style_small, fontName="Helvetica-Bold", textColor=NAVY)),
     Paragraph("Python 3 (built-in HTTP server)", ParagraphStyle("cf2", parent=style_small, textColor=INK))],
    [Paragraph("<b>DATABASE</b>", ParagraphStyle("cf", parent=style_small, fontName="Helvetica-Bold", textColor=NAVY)),
     Paragraph("Supabase / PostgreSQL — optional cloud sync", ParagraphStyle("cf2", parent=style_small, textColor=INK))],
    [Paragraph("<b>DEFAULT PORT</b>", ParagraphStyle("cf", parent=style_small, fontName="Helvetica-Bold", textColor=NAVY)),
     Paragraph("8080", ParagraphStyle("cf2", parent=style_small, textColor=INK))],
    [Paragraph("<b>PREPARED</b>", ParagraphStyle("cf", parent=style_small, fontName="Helvetica-Bold", textColor=NAVY)),
     Paragraph(datetime.date.today().strftime("%d %B %Y"), ParagraphStyle("cf2", parent=style_small, textColor=INK))],

]
cf_t = Table(cover_facts, colWidths=[55*mm, 115*mm])
cf_t.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LINEBELOW", (0,0), (-1,-2), 0.4, LINE),
]))
story.append(cf_t)
story.append(Spacer(1, 6*mm))
story.append(Paragraph(
    "A full-stack Academic Management &amp; Digital Twin Web Platform. "
    "It combines a Python HTTP backend with an HTML + Tailwind + Vanilla JS frontend, "
    "20-student and 20-staff datasets, a rule-based AI chatbot, and optional Supabase cloud sync.",
    ParagraphStyle("cdesc", parent=style_body, fontSize=9, textColor=INK)
))
story.append(Spacer(1, 6*mm))

# Cover bottom note
story.append(Table([[Paragraph(
    "<font color='#647084'>Prepared for project review · Location: <b>D:\\test\\smart-college-management</b> · Document generated for academic presentation.</font>",
    ParagraphStyle("cnote", parent=style_small, fontSize=7.5))]],
    colWidths=[170*mm],
    style=TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BLUE_SOFT),
        ("LEFTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ])))

# ---- BREAK to body ----
story.append(PageBreak())

# ---- EXEC SUMMARY ----
story.append(Paragraph("EXECUTIVE SUMMARY", ParagraphStyle("es", parent=style_small, fontName="Helvetica-Bold", fontSize=8, textColor=BLUE, letterSpacing=2)))
story.append(Paragraph("What this platform delivers", style_h1))
story.append(body(
    "Smart College AI is a browser-based digital-twin platform that mirrors a student's full academic life — "
    "attendance, grades, fees, certificates, faculty contact, and predictive health — through a single web workspace. "
    "It supports both students (11 dashboard tabs) and staff (8 admin tabs) with a shared AI chatbot that answers "
    "questions against live record data rather than a generic model. The backend runs on Python 3's built-in HTTP server; "
    "no external web framework is required. The database layer is optional: all features work locally from JSON/CSV sources, "
    "and a Supabase cloud connection activates when a user enters their API key."
))
story.append(body(
    "The review should confirm: end-to-end student and staff journeys, authentication behavior, AI response accuracy, "
    "API contract completeness, data model alignment (supabase_schema.sql), test coverage (7 automated tests), and the "
    "security posture of using demo credentials in a development setting."
))
story.append(spacer(2))

# Key stats row
stats = [
    [Paragraph("<b>20</b><br/><font color='#647084' size='7'>Students modeled across 6 departments</font>", ParagraphStyle("s", parent=style_small, fontSize=9, leading=12, align=TA_CENTER)),
     Paragraph("<b>20</b><br/><font color='#647084' size='7'>Staff members (HODs, faculty, deans)</font>", ParagraphStyle("s", parent=style_small, fontSize=9, leading=12, align=TA_CENTER)),
     Paragraph("<b>9</b><br/><font color='#647084' size='7'>Supabase tables with RLS + seed</font>", ParagraphStyle("s", parent=style_small, fontSize=9, leading=12, align=TA_CENTER)),
     Paragraph("<b>7</b><br/><font color='#647084' size='7'>Automated tests (all passing)</font>", ParagraphStyle("s", parent=style_small, fontSize=9, leading=12, align=TA_CENTER))],
]
stats_t = Table(stats, colWidths=[42.5*mm]*4)
stats_t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), BLUE_SOFT),
    ("BOX", (0,0), (-1,-1), 0.5, BLUE),
    ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8),
]))
story.append(stats_t)
story.append(spacer(4))

# ---- TOC ----
story.append(Paragraph("CONTENTS", ParagraphStyle("toc_t", parent=style_small, fontName="Helvetica-Bold", fontSize=8, textColor=BLUE, letterSpacing=2)))
story.append(sub_heading("Table of Contents"))
toc_items = [
    ("1", "Project Overview & Architecture"),
    ("2", "Folder Structure & File Roles"),
    ("3", "End-to-End User Flow"),
    ("4", "Backend — server.py"),
    ("5", "Frontend — index.html & app.js"),
    ("6", "Data — Students, Staff, JSON / CSV"),
    ("7", "Database Schema — supabase_schema.sql"),
    ("8", "Dual Data Architecture"),
    ("9", "Authentication System"),
    ("10", "AI Chatbot Engine"),
    ("11", "API Endpoints"),
    ("12", "Key Features & Demonstrations"),
    ("13", "How To Run & Testing"),
    ("14", "Appendix — Source Maps"),
]
toc_data = [[Paragraph(f"<b>{n}</b>", ParagraphStyle("tn", parent=style_small, fontName="Helvetica-Bold", textColor=BLUE, fontSize=8)),
              Paragraph(t, ParagraphStyle("tt", parent=style_small, fontSize=8.2, leading=11, textColor=INK))] for n,t in toc_items]
toc_t = Table(toc_data, colWidths=[10*mm, 160*mm])
toc_t.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ("LINEBELOW", (0,0), (-1,-2), 0.3, LINE),
]))
story.append(toc_t)
story.append(PageBreak())

# ---- SECTION 1 ----
story.append(section_heading("1", "Project Overview & Architecture"))
story.append(body(
    "Smart College AI serves as a digital mirror of a student's academic life. Its design goal is to let students "
    "check attendance, fees, grades, and faculty info from a browser; let staff mark attendance, approve certificates, "
    "and email cohorts; and let both groups ask a chatbot that pulls answers from their actual records. The platform "
    "is fully local-first, with an optional Supabase cloud layer that activates via a key input in Settings."
))
story.append(sub_heading("Architecture at a glance"))
arch_rows = [
    ("Layer", "Technology", "Responsibility"),
    ("Frontend", "HTML + Tailwind CSS + Vanilla JS + Material Symbols", "All student/staff screens (single-page app via tab switching)"),
    ("Backend", "Python 3 (http.server)", "Auth, AI response, fee/attendance updates, email simulation"),
    ("Data (local)", "JSON / CSV (data/)", "20-student + 20-staff records; generated from CSV via generate_json.py"),
    ("Data (cloud)", "Supabase PostgreSQL", "9 tables with RLS policies; seed data included; optional live sync"),
]
story.append(data_table([r[0] for r in arch_rows[1:]], arch_rows[1:], col_widths=[32*mm, 65*mm, 73*mm]))
story.append(spacer(2))

story.append(sub_heading("Version & deployment info"))
story.append(body(
    "App Version <b>2.5.0</b> | Supabase project <b>https://aqfqdjhddfvyprpwccyp.supabase.co</b> | "
    "Default port <b>8080</b> (configured in <font face='Courier' size='7'>run.sh</font>). Backend runs as a single-file "
    "Python server with zero external dependencies; frontend pulls Tailwind and Material Symbols from CDN."
))
story.append(callout_box(
    "REVIEW NOTE: All references to Supabase URL, demo passwords (student@123 / staff@123), and student/staff IDs in this document "
    "are development/configuration values. Confirm they are replaced or isolated before any production or assessment deployment.",
    bg=AMBER, border=AMBER
))

# ---- SECTION 2 ----
story.append(section_heading("2", "Folder Structure & File Roles"))
story.append(body("Every file has a single documented purpose. The tree is intentionally flat — only static/ and data/ branch deeper."))
story.append(data_table(
    ["Path", "Role", "Key content / lines"],
    [
        ("PROJECT_DOCUMENT.md", "Review doc (this source)", "759 lines — full explanation of all sections"),
        ("README.md", "Quick guide", "128 lines — capabilities, datasets, run instructions"),
        ("server.py", "Backend", "867 lines — auth, AI chatbot, endpoints, JSON load"),
        ("test_app.py", "Tests", "131 lines — 7 automated checks"),
        ("run.sh", "Startup", "13 lines — sets PORT=8080, starts server.py"),
        ("data/students_dataset.csv", "Student CSV source", "20 records (Aarav … Aditi)"),
        ("data/students.json", "Student data (runtime)", "36 918 bytes — full record objects"),
        ("data/staff_dataset.csv", "Staff CSV source", "20 records (Dr. Rajesh Raman …)"),
        ("data/staff.json", "Staff data (runtime)", "8 374 bytes — profiles + courses"),
        ("data/generate_json.py", "Converter", "CSV → JSON pipeline"),
        ("supabase/supabase_schema.sql", "DB schema", "23 186 bytes — 9 table definitions + seed INSERTs"),
        ("static/index.html", "Frontend UI", "83 349 bytes — all tabs (single page)"),
        ("static/js/app.js", "Frontend logic", "57 677 bytes — init, login, tab switch, AI, API calls"),
    ],
    col_widths=[42*mm, 32*mm, 96*mm]
))
story.append(body("Analogy from the source documentation: <font face='Helvetica-Bold'>server.py</font> = principal's office; <font face='Helvetica-Bold'>index.html</font> = building front door; <font face='Helvetica-Bold'>app.js</font> = internal wiring; <font face='Helvetica-Bold'>data/*.json</font> = filing cabinet."))

# ---- SECTION 3 ----
story.append(section_heading("3", "End-to-End User Flow"))
story.append(body("This walkthrough maps the exact steps a student named <b>Aarav Sharma</b> (CSE, ID 23331a42001) takes from browser open to AI answer."))
story.append(sub_heading("Step-by-step (from source)"))
flow_items = [
    ("Open browser", "Go to <font face='Courier' size='7'>http://localhost:8080</font>"),
    ("Login screen", "Select Student / Staff tab; enter ID + password; or click 1-click demo pill (Aarav / Dr. Rajesh Raman)"),
    ("Server verifies", "POST /api/auth/login → server loads students.json → match 23331a42001 + student@123 → return token + user object"),
    ("Dashboard renders", "app.js hides login, shows workspace, fetches /api/students/23331a42001, renders cards (91% attendance, 8.74 CGPA, ₹12,500 fees)"),
    ("AI question", "Type <i>“Can I skip DBMS today?”</i> → POST /api/chat → server finds DBMS (28/36 = 77.8%) → calculates 75.7% if skipped → formatted response"),
    ("Data can change", "Staff marks attendance (/api/attendance/mark) → student pays fees (/api/fees/pay) → applies for cert (/api/requests) → writes to JSON or Supabase"),
]
ft = Table([[Paragraph(f"<b>{step}</b>", ParagraphStyle("st", parent=style_small, fontSize=8, leading=11, textColor=NAVY)),
              Paragraph(desc, ParagraphStyle("sd", parent=style_small, fontSize=8, leading=11))] for step,desc in flow_items],
    colWidths=[30*mm, 140*mm])
ft.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 5),
    ("RIGHTPADDING", (0,0), (-1,-1), 5), ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4), ("LINEBELOW", (0,0), (-1,-2), 0.3, LINE),
]))
story.append(ft)

# ---- SECTION 4 ----
story.append(section_heading("4", "Backend — server.py"))
story.append(body(
    "The backend is a single Python file (867 lines) using <font face='Courier' size='7'>http.server.HTTPServer</font>. "
    "It does not import Flask, FastAPI, or Django — all routing is manual via <font face='Courier' size='7'>do_GET</font> / <font face='Courier' size='7'>do_POST</font>. "
    "The server reads all student/staff data from JSON at startup and writes changes back to disk (or to Supabase when configured)."
))
story.append(sub_heading("Core functions (documented)"))
story.append(body(
    "<b>authenticate_user(role, identifier, password)</b> — checks JSON files, supports ID or email, case-insensitive. "
    "Returns user object + token. <b>generate_ai_response(query, user_context, role)</b> — keyword-matching engine: finds "
    "subject attendance, calculates projection on skip, returns formatted Markdown with emoji. <b>send_email_to_students()</b> — "
    "SMTP if configured; else writes to <font face='Courier' size='7'>data/email_log.json</font>."
))
story.append(sub_heading("Key API routes"))
route_rows = [
    ("Method / Path", "Purpose", "Notes"),
    ("GET /api/config", "App config + Supabase URL", "Version 2.5.0, 20 students"),
    ("GET /api/students[?dept=]", "All students", "Filterable by department / search"),
    ("GET /api/students/:id", "Single record", "Full profile + subjects + requests"),
    ("GET /api/staff", "All staff", "20 members with cabins + specialization"),
    ("GET /api/staff/:id/courses", "Staff courses", "Enrolled students + schedule"),
    ("GET /api/stats", "College averages", "Avg CGPA, attendance, fee recovery"),
    ("GET /api/supabase-schema", "Download SQL", "Full schema file"),
    ("POST /api/auth/login", "Login", "{role, identifier, password}"),
    ("POST /api/chat", "AI chatbot", "{message, user_id, role}"),
    ("POST /api/fees/pay", "Clear fees", "Sets fee_balance=0, status=Paid"),
    ("POST /api/requests", "Cert request", "Generates REQ-ID"),
    ("POST /api/requests/ID/approve", "Approve", "Staff action"),
    ("POST /api/requests/ID/reject", "Reject", "Staff action"),
    ("POST /api/attendance/mark", "Mark present/absent", "Updates subject percentages"),
    ("POST /api/send-email", "Bulk email", "To students above CGPA threshold"),
]
story.append(data_table(
    [r[0] for r in route_rows[1:]], route_rows[1:],
    col_widths=[42*mm, 50*mm, 78*mm], small=True
))

# ---- SECTION 5 ----
story.append(section_heading("5", "Frontend — index.html & app.js"))
story.append(sub_heading("Frontend structure (index.html)"))
story.append(body(
    "One large HTML file (~1200 lines) containing every screen. Navigation is a sidebar; only one tab <font face='Courier' size='7'>&lt;div&gt;</font> "
    "is visible at a time (controlled by <font face='Courier' size='7'>app.js</font> via <font face='Courier' size='7'>switchTab()</font>). "
    "Styling uses Tailwind CSS via CDN; icons use Material Symbols via CDN. No build step required."
))
story.append(sub_heading("Student tabs (11)"))
story.append(body(
    "Dashboard · AI Copilot · Attendance Ledger · Fees & Payments · CGPA & Marks · Certificates · Digital Twin · "
    "Student Dataset · Staff Directory · Settings. Each tab pulls data from /api/students or /api/staff via fetch."
))
story.append(sub_heading("Staff tabs (8)"))
story.append(body(
    "Faculty Overview · My Courses · Attendance Marker · Certificate Approvals · Faculty AI Assistant · "
    "Student Dataset · Staff Dataset · Settings. Staff-specific AI chips replace student prompts after login."
))
story.append(sub_heading("Frontend logic (app.js)"))
story.append(body(
    "~1350 lines. Core flow: <font face='Courier' size='7'>initApp()</font> (load data, check session) → "
    "<font face='Courier' size='7'>performLogin()</font> → <font face='Courier' size='7'>switchTab()</font> → render functions per tab → "
    "<font face='Courier' size='7'>sendFullAiQuery()</font> (typing animation → response bubble). State is kept in a JS object: authRole, authUser, students[], staff[], allRequests[], activeTab. "
    "Session stored in sessionStorage; Supabase key in localStorage. Fallback login validates locally if server is down (demonstration mode)."
))

# ---- SECTION 6 ----
story.append(section_heading("6", "Data — Students, Staff, JSON / CSV"))
story.append(sub_heading("Student dataset (data/students.json)"))
story.append(body("20 records. Each record includes: student_id, password, full_name, department, email, cgpa, phone, semester, year, attendance_pct, fee_balance, fee_status, digital_twin_score, subjects[], active_requests[], recent_activities[]."))
story.append(sub_heading("Representative student records"))
student_rows = [
    ("ID", "Name", "Dept", "CGPA", "Attendance", "Fees"),
    ("23331a42001", "Aarav Sharma", "CSE", "8.74", "91%", "₹12,500"),
    ("23331a42002", "Priya Patel", "IT", "9.12", "93%", "₹8,000"),
    ("23331a42013", "Meera Kulkarni", "CSE", "9.60", "95%", "Paid"),
    ("23331a42003", "Rohan Reddy", "MECH", "7.45", "84%", "₹10,200"),
    ("23331a42005", "Vikram Gupta", "CIVIL", "6.82", "78%", "₹15,000"),
    ("23331a42006", "Ananya Rao", "EEE", "9.40", "96%", "Paid"),
]
story.append(data_table([r[0] for r in student_rows[1:]], student_rows[1:], col_widths=[26*mm, 42*mm, 18*mm, 16*mm, 20*mm, 18*mm], small=True))
story.append(spacer(2))

story.append(sub_heading("Staff dataset (data/staff.json)"))
story.append(body("20 members: 6 HODs, 10 Professors/Associates, 2 Deans, 2 Admin Officers. Each has staff_id, password, full_name, department, designation, email, phone, cabin_location, specialization, experience_years, office_hours."))
story.append(sub_heading("Sample staff"))
staff_rows = [
    ("ID", "Name", "Designation", "Dept", "Cabin"),
    ("STF101", "Dr. Rajesh Raman", "Professor & HOD", "CSE", "CS-Block 301"),
    ("STF117", "Dr. Sudhir Joshi", "Dean (Academics)", "—", "Admin Block"),
    ("STF102", "Dr. Sunita Kulkarni", "Professor", "IT", "IT-Block 205"),
]
story.append(data_table(staff_rows[0], staff_rows[1:], col_widths=[18*mm, 40*mm, 35*mm, 18*mm, 39*mm], small=True))
story.append(spacer(2))

story.append(sub_heading("Data conversion (generate_json.py)"))
story.append(body("Reads CSV datasets and writes JSON files with full record structures. Allows editing CSV in Excel/Google Sheets and regenerating the runtime data without manually editing JSON."))

# ---- SECTION 7 ----
story.append(section_heading("7", "Database Schema — supabase_schema.sql"))
story.append(body("23 186 bytes defining 9 tables with full DDL + seed INSERT statements. Row Level Security enabled on all tables (currently public access for development)."))
story.append(sub_heading("Table summary"))
schema_rows = [
    ("Table", "Purpose", "Key fields / notes"),
    ("departments", "College departments", "dept_code PK, name, building, hod_name"),
    ("students", "Student profiles", "student_id, cgpa, attendance_pct, fee_balance"),
    ("staff", "Faculty profiles", "staff_id, designation, cabin_location"),
    ("subjects", "Course catalog", "subject_code, name, credits, faculty_id"),
    ("student_attendance", "Per-subject attendance", "attended, total, percentage"),
    ("fee_records", "Payment tracking", "tuition_fee, paid_amount, due_date"),
    ("certificate_requests", "Applications", "certificate_type, status, applied_date"),
    ("activity_logs", "Timeline", "title, description, icon"),
    ("knowledge_base", "AI Q&A pairs", "question, answer, keywords"),
]
story.append(data_table(schema_rows[0], schema_rows[1:], col_widths=[32*mm, 42*mm, 96*mm], small=True))
story.append(sub_heading("Schema snippet — departments"))
story.append(code_block(
    "CREATE TABLE IF NOT EXISTS public.departments (\n"
    "  dept_code VARCHAR(10) PRIMARY KEY,\n"
    "  name VARCHAR(100) NOT NULL,\n"
    "  building VARCHAR(100) NOT NULL,\n"
    "  hod_name VARCHAR(100) NOT NULL\n"
    ");"
))
story.append(callout_box(
    "REVIEW NOTE: All tables use RLS. Confirm policies restrict access to appropriate roles before exposing the endpoint publicly.",
    bg=BLUE_SOFT, border=BLUE
))

# ---- SECTION 8 ----
story.append(section_heading("8", "Dual Data Architecture"))
story.append(body("One design decision is deliberately highlighted: the app works online and offline with zero setup."))
story.append(sub_heading("Without Supabase key"))
story.append(body("Reads students.json / staff.json locally. All dashboard, attendance, fee, and AI features work immediately. No network dependency."))
story.append(sub_heading("With Supabase key"))
story.append(body("User enters anon key in Settings → <font face='Courier' size='7'>initSupabase()</font> activates → reads/writes to cloud tables. Local JSON remains as fallback. Settings screen shows pre-filled URL and empty key box with a <b>Test Connection</b> button."))
story.append(callout_box(
    "The hybrid architecture is a strength for reviews: it shows awareness of offline-first design, cloud-sync readiness, and graceful degradation.",
    bg=GREEN, border=GREEN
))

# ---- SECTION 9 ----
story.append(section_heading("9", "Authentication System"))
story.append(body("Simplified session model — not JWT-validated — for demonstration. Tokens are strings like <font face='Courier' size='7'>token_student_23331a42001_1695123456</font>."))
story.append(sub_heading("Login behavior"))
story.append(body(
    "Accepts student ID (23331a42001) OR email (aarav.sharma1@college.edu) — case-insensitive. Staff uses STF101 / rajesh.raman@college.edu. "
    "Password for all students: <font face='Courier' size='7'>student@123</font>. Password for all staff: <font face='Courier' size='7'>staff@123</font>. "
    "After login, sessionStorage holds role + user; localStorage holds Supabase key (if entered). Login can fall back to local JS validation if server is offline."
))
story.append(sub_heading("Demo pills"))
story.append(body("Two 1-click buttons on login screen: 🎓 Aarav Sharma (CSE) and 👨‍🏫 Dr. Rajesh Raman (CSE HOD) for instant demo access without typing."))

# ---- SECTION 10 ----
story.append(section_heading("10", "AI Chatbot Engine"))
story.append(body("Not an external AI model — a rule-based keyword matcher inside server.py that reads real student/staff data to answer context-specific questions."))
story.append(sub_heading("How it works (from source)"))
story.append(body(
    "Lowercase query → detect keywords (skip/miss/absent, fee/dues/balance, attendance/percentage, cgpa/marks, bonafide/certificate) → branch by role → "
    "find relevant records → compute projection (e.g., 28/36 → 28/37) → return formatted Markdown with emoji. Fallback is generic welcome."
))
story.append(sub_heading("Example responses"))
example_rows = [
    ("User asks", "Mechanism", "Response"),
    ("Can I skip DBMS today?", "Find DBMS attendance → project if skip 1 session", "⚠️ 77.8% → 75.7% — attend next 2 to reach safe zone"),
    ("What is my fee balance?", "Read fee_balance", "💳 Outstanding: ₹12,500. Due Nov 15."),
    ("Who is HOD of CSE?", "Search staff.json for CSE + HOD", "👨‍🏫 Dr. Rajesh Raman — Cabin CS-Block 301"),
    ("Show students above 7 CGPA", "Filter by CGPA ≥ 7", "🏆 14 students found (Meera 9.60, Priya 9.12, …)"),
]
story.append(data_table([r[0] for r in example_rows[1:]], example_rows[1:], col_widths=[48*mm, 48*mm, 74*mm], small=True))
story.append(sub_heading("Staff-specific queries"))
story.append(body("Above / cgpa / top performer → list students by threshold. Send email / mail to → bulk email. Student / roster / shortage → department overview. Cabin / office hours → staff schedule."))

# ---- SECTION 11 ----
story.append(section_heading("11", "API Endpoints"))
story.append(sub_heading("GET"))
story.append(data_table(
    ["Endpoint", "Description"],
    [
        ("/api/config", "App config + Supabase URL"),
        ("/api/students[?dept=][?search=]", "All students (filterable)"),
        ("/api/students/23331a42001", "Single student (full record)"),
        ("/api/staff", "All staff"),
        ("/api/staff/STF101/courses", "Staff courses + enrolled"),
        ("/api/requests/all", "All certificate requests"),
        ("/api/stats", "College statistics"),
        ("/api/supabase-schema", "Download SQL schema"),
    ],
    col_widths=[60*mm, 110*mm], small=True
))
story.append(sub_heading("POST"))
story.append(data_table(
    ["Endpoint", "Body", "Purpose"],
    [
        ("/api/auth/login", "{role, identifier, password}", "Authenticate"),
        ("/api/chat", "{message, user_id, role}", "AI query"),
        ("/api/fees/pay", "{student_id, amount, method}", "Pay fees"),
        ("/api/requests", "{student_id, certificate_type, purpose}", "Apply cert"),
        ("/api/requests/ID/approve", "(body ignored)", "Approve"),
        ("/api/requests/ID/reject", "(body ignored)", "Reject"),
        ("/api/attendance/mark", "{student_id, subject_name, action}", "Mark present/absent"),
        ("/api/send-email", "{staff_id, to_cgpa_above, ...}", "Bulk email"),
    ],
    col_widths=[42*mm, 50*mm, 78*mm], small=True
))

# ---- SECTION 12 ----
story.append(section_heading("12", "Key Features & Demonstrations"))
story.append(sub_heading("Feature 1: Dashboard Overview"))
story.append(body("Welcome banner + 4 stat cards (attendance, CGPA, fees, requests) + subject attendance + recent activity + schedule + AI widget. Example: <i>“Good morning, Aarav 👋 — Attendance: 91% On Track — CGPA: 8.74 — Fees: ₹12,500 Due Nov 15 — 1 Active Request.”</i>"))
story.append(sub_heading("Feature 2: Fee Payment Simulator"))
story.append(body("Open Pay Fees → modal shows total + method → Confirm → server sets fee_balance=0, status=Paid → receipt REC-2509181430 → dashboard updates to “Fully Paid ✅”."))
story.append(sub_heading("Feature 3: AI Attendance Advice"))
story.append(body("Student with 77.8% DBMS attendance: skip → 75.7% (close to cutoff). Student with 92%: skip → 91.7% (safe). Both answers include projection + recommendation."))
story.append(sub_heading("Feature 4: Staff Attendance Marker"))
story.append(body("Table with +Present / Absent buttons per student. Click updates backend → refreshes table. Integrated with department-level stats."))
story.append(sub_heading("Feature 5: Certificate Requests"))
story.append(body("Student applies (type + purpose) → REQ-ID generated → status “In Review” → staff approves/rejects → instant update. Types include Bonafide, Provisional, Course Completion."))
story.append(sub_heading("Feature 6: Staff AI Copilot"))
story.append(body("Dr. Radhika Menon (IT) asks “Show students above 7 CGPA” → 4 results with names, IDs, CGPAs, attendance %, emails. Follow-up “send email to students above 7” queues messages."))
story.append(sub_heading("Feature 7: Digital Twin Health Score"))
story.append(body("Predictive score (0-100) from attendance consistency, grades, fee timing, lab milestones. Example: Aarav = 93/100 → “High probability of Distinction tier degree.”"))

# ---- SECTION 13 ----
story.append(section_heading("13", "How To Run & Testing"))
story.append(sub_heading("Quick start"))
story.append(code_block(
    "# Navigate to project folder\ncd D:\\test\\smart-college-management\n\n# Start server (port 8080 by default)\npython3 server.py 8080\n# Or:\n./run.sh\n\n# Open browser\n# Visit: http://localhost:8080"
))
story.append(sub_heading("Default accounts for review/demo"))
story.append(data_table(
    ["Role", "ID / Email", "Password"],
    [
        ("Student", "23331a42001 / aarav.sharma1@college.edu", "student@123"),
        ("Student", "23331a42006 / ananya.rao6@college.edu", "student@123"),
        ("Staff", "STF101 / rajesh.raman@college.edu", "staff@123"),
        ("Staff", "STF117 / dean.academics@college.edu", "staff@123"),
    ],
    col_widths=[20*mm, 85*mm, 65*mm], small=True
))
story.append(sub_heading("Automated tests (test_app.py — 7 tests, ~0.5s)"))
test_rows = [
    ("Test", "Verifies"),
    ("01", "CSV has 20 students; first Aarav Sharma; last Aditi Sharma"),
    ("02", "CSV has 20 staff across 7 departments"),
    ("03", "Student login by ID, by email, case-insensitive"),
    ("04", "Staff login by ID, by email"),
    ("05", "Invalid credentials rejected; unknown user rejected"),
    ("06", "SQL file has all required tables and seed data"),
    ("07", "AI responds correctly to attendance, fee, faculty, roster"),
]
story.append(data_table(test_rows[0], test_rows[1:], col_widths=[12*mm, 158*mm], small=True))
story.append(body("All tests pass (expected: 7 dots, OK). Confirm test suite runs clean before final demonstration."))

# ---- SECTION 14 ----
story.append(section_heading("14", "Appendix — Source Maps"))
story.append(sub_heading("Document provenance"))
story.append(body(
    "This review PDF was generated from the actual project source at <font face='Courier' size='7'>D:\\test\\smart-college-management</font>. "
    "Source files read/verified: PROJECT_DOCUMENT.md (759 lines), README.md (128 lines), server.py (867 lines), test_app.py (131 lines), "
    "run.sh (13 lines), data/*.csv + *.json + generate_json.py, supabase/supabase_schema.sql (23 186 bytes), static/index.html (83 349 bytes), static/js/app.js (57 677 bytes)."
))
story.append(sub_heading("Git & attribution (preserved verbatim)"))
story.append(body("Per project instructions, commit messages end with: <font face='Courier' size='7'>Co-Authored-By: Claude Code &lt;noreply@anthropic.com&gt;</font>. PR descriptions end with: <font face='Courier' size='7'>🤖 Generated with [Claude Code](https://claude.com/claude-code)</font>. These lines must be preserved exactly as specified."))
story.append(spacer(4))
story.append(hr())
story.append(Paragraph(
    "Prepared for Smart College AI project review · Smart College AI Digital Twin OS · Version 2.5.0 · "
    "Supabase: https://aqfqdjhddfvyprpwccyp.supabase.co · Default port 8080 · All content derived from actual source files.",
    ParagraphStyle("end", parent=style_small, fontSize=7.5, textColor=MUTED, align=TA_CENTER)
))

# ---------- build ----------
doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
print(f"PDF written: {FILE} ({os.path.getsize(FILE)//1024} KB)")
