# 📘 Smart College AI — Project Document

> **Full explanation of the Smart College AI Digital Twin OS & Management Platform**
> Location: `D:\test\smart-college-management`

---

## Table of Contents

1. [What Is This Project?](#1-what-is-this-project)
2. [Project Folder Structure](#2-project-folder-structure)
3. [How The System Works (End-to-End Flow)](#3-how-the-system-works-end-to-end-flow)
4. [The Backend — `server.py`](#4-the-backend--serverpy)
5. [The Frontend — `static/index.html`](#5-the-frontend--staticindexhtml)
6. [Frontend Logic — `static/js/app.js`](#6-frontend-logic--staticjsappjs)
7. [Student Data — `data/students.json`](#7-student-data--datastudentsjson)
8. [Staff Data — `data/staff.json`](#8-staff-data--datastaffjson)
9. [Database Schema — `supabase/supabase_schema.sql`](#9-database-schema--supabasesupabase_schemasql)
10. [Dual Data Architecture](#10-dual-data-architecture)
11. [Authentication System](#11-authentication-system)
12. [AI Chatbot Engine](#12-ai-chatbot-engine)
13. [Key Features With Examples](#13-key-features-with-examples)
14. [API Endpoints](#14-api-endpoints)
15. [How To Run](#15-how-to-run)
16. [Testing](#16-testing)
17. [Summary Diagram](#17-summary-diagram)

---

## 1. What Is This Project?

**Smart College AI** is a **full-stack Academic Management & Digital Twin Web Platform**. It is essentially a smart university portal that gives:

- **Students** a personal dashboard to track attendance, CGPA, fees, and certificates.
- **Faculty/Staff** an admin hub to mark attendance, approve certificates, and view department stats.
- **Everyone** an AI Chatbot that answers questions using their real academic data (attendance, fees, faculty info, etc.).
- **Admins** a connection to a Supabase cloud database for live syncing.

Think of it as a **digital mirror (twin)** of a student's entire academic life — attendance, grades, money owed, requests — all accessible through a web browser.

### Real-World Analogy

Imagine a college where:
- Instead of going to the admin office to check your fee balance, you open a website and see ₹12,500 due with a **Pay Now** button.
- Instead of asking your professor "Am I safe to miss class?", you text an AI bot and it checks your attendance and says: *"If you skip today, you drop to 72% — below exam cutoff! Attend next 2 lectures."*
- Instead of manually checking attendance sheets, a faculty member clicks **"+ Present"** next to each student's name.

That is what this platform does.

---

## 2. Project Folder Structure

```
D:\test\smart-college-management\
│
├── server.py                          # 🧠 Backend server (Python)
├── test_app.py                        # 🧪 Automated test suite
├── run.sh                             # ⚡ Startup script
├── README.md                          # 📖 Project guide
│
├── data/                              # 📦 Data files
│   ├── students.json                  # 20 student records
│   ├── staff.json                     # 20 staff records
│   ├── students_dataset.csv           # CSV version of students
│   ├── staff_dataset.csv              # CSV version of staff
│   └── generate_json.py               # Script to generate JSON from CSV
│
├── supabase/                          # ☁️ Cloud database
│   └── supabase_schema.sql            # Database table definitions + seed data
│
└── static/                            # 🌐 Website files
    ├── index.html                     # Main web page (all screens)
    └── js/
        └── app.js                     # Frontend logic (clicks, tabs, API calls)
```

### What Each Folder Does

| Path | Role | Analogy |
|---|---|---|
| `server.py` | The **brain** — processes logins, answers AI questions, handles payments. | The college principal's office that processes everything. |
| `static/index.html` | The **storefront** — what students and staff see on screen. | The college building's front door and hallways. |
| `static/js/app.js` | The **nervous system** — makes buttons work, switches tabs, fetches data. | The wiring inside the walls that connects switches to lights. |
| `data/*.json` | The **filing cabinet** — stored student/staff records. | Paper records in the registrar's office. |
| `supabase/*.sql` | The **blueprint** — how cloud database tables should be created. | The architect's plan before building a new wing. |

---

## 3. How The System Works (End-to-End Flow)

Here is what happens when a student named **Aarav Sharma** uses the system:

```
Step 1: OPEN BROWSER
        → Goes to http://localhost:8080
        
Step 2: LOGIN SCREEN
        → Sees "Student Sign In" / "Faculty Sign In" tabs
        → Enters ID: 23331a42001, Password: student@123
        → Clicks "Sign In to Campus OS"
        
Step 3: SERVER VERIFIES (server.py)
        → server.py receives POST /api/auth/login
        → Loads students.json
        → Finds student_id "23331a42001"
        → Password matches "student@123" ✓
        → Returns: { success: true, user: { ...Aarav's data... } }
        
Step 4: FRONTEND RENDERS DASHBOARD (app.js)
        → Hides login screen, shows app workspace
        → Fetches /api/students/23331a42001 for full details
        → Fetches /api/staff for staff directory
        → Displays: "Good morning, Aarav 👋"
        → Shows: Attendance 91%, CGPA 8.74, Fees ₹12,500
        
Step 5: STUDENT ASKS A QUESTION (AI Chatbot)
        → Types: "Can I skip DBMS today?"
        → Frontend sends POST /api/chat { message: "Can I skip DBMS today?" }
        → server.py's generate_ai_response() runs:
            a. Finds Aarav's DBMS subject (28/36 = 77.8%)
            b. Calculates: if skip → 28/37 = 75.7% (still above 75% but close)
            c. Returns formatted answer with warning
        → Frontend displays the AI response in chat bubble
        
Step 6: DATA CAN CHANGE
        → If staff marks attendance via /api/attendance/mark
        → If student pays fees via /api/fees/pay
        → If student applies for certificate via /api/requests
        → All changes are saved to students.json (local) or Supabase (cloud)
```

---

## 4. The Backend — `server.py`

This is the **main Python file** that runs a mini web server on port **8080**. It does everything behind the scenes.

### Key Functions

#### `authenticate_user(role, identifier, password)`
Logs someone in. Checks their ID or email and password against the JSON data files.

**Example:**
```
Input:  role="student", identifier="23331a42001", password="student@123"
Output: Found Aarav Sharma ✅

Input:  role="student", identifier="23331a42001", password="wrong"
Output: "Incorrect password for this student account." ❌
```

#### `generate_ai_response(query, user_context, role)`
The **chatbot brain**. Uses keyword matching to figure out what the user is asking and gives a smart answer using real data.

**Example conversations:**

| User Asks | How It Works | What It Returns |
|---|---|---|
| *"Can I skip DBMS today?"* | Finds DBMS subject → calculates projected attendance if one session missed | "⚠️ If you skip, attendance drops to 75.7% — still above cutoff but attend next 2 to reach safe zone." |
| *"What is my fee balance?"* | Reads fee_balance field for the student | "💳 Outstanding Tuition: ₹12,500. Due Nov 15." |
| *"Who is HOD of CSE?"* | Searches staff.json for CSE + HOD | "👨‍🏫 Dr. Rajesh Raman, Cabin CS-Block Room 301" |
| *"Show students above 7 CGPA"* (staff only) | Filters students by CGPA threshold | "🏆 14 students found. 1. Meera Kulkarni (9.60)..." |
| *"Send email to students above 8"* (staff) | Finds students, calls email function | "📧 7 emails queued/sent." |

#### `send_email_to_students(from_staff, recipients, subject, body)`
Sends emails using Gmail SMTP (if configured), otherwise logs them to `data/email_log.json` as simulation.

#### API Route Handlers (`do_GET`, `do_POST`)
The server listens for HTTP requests and routes them:

- `GET  /api/students` → returns all 20 students (with optional `?dept=CSE` filter)
- `GET  /api/students/23331a42001` → returns Aarav's full record
- `GET  /api/staff` → returns all 20 staff
- `GET  /api/staff/STF101/courses` → returns Dr. Rajesh Raman's courses + his students
- `GET  /api/stats` → returns college-wide averages
- `GET  /api/config` → returns Supabase URL and version info
- `POST /api/auth/login` → verify credentials, return token
- `POST /api/chat` → submit a question, get AI answer
- `POST /api/fees/pay` → clear a student's fee balance
- `POST /api/requests` → apply for a certificate
- `POST /api/requests/REQ-xxxx/approve` → staff approves a request
- `POST /api/requests/REQ-xxxx/reject` → staff rejects a request
- `POST /api/attendance/mark` → staff marks a student present/absent
- `POST /api/send-email` → staff sends email to students above a CGPA

---

## 5. The Frontend — `static/index.html`

This is a **single large HTML page** (~1200 lines) containing every screen the user sees. It uses **Tailwind CSS** (via CDN) for styling and **Material Symbols** for icons.

### Screens (Tabs) In The Application

The page has a **sidebar navigation** with different tabs. Each tab is a `<div>` with an id like `tab-dashboard`, `tab-attendance`, etc. Only one tab is visible at a time (controlled by `app.js`).

#### For Students (11 tabs):

| Tab | What It Shows | Example |
|---|---|---|
| **Dashboard** | Welcome banner, 4 stat cards (attendance, CGPA, fees, requests), subject attendance, recent activity, schedule, AI widget | "Good morning, Aarav 👋" + "Attendance: 91% On Track" |
| **AI Copilot** | Full chat interface with suggested prompt chips | Type "Explain fee breakup" → get answer |
| **Attendance Ledger** | Subject-by-subject with 75% cutoff and safe-miss calculation | "DBMS: 77.8% — ⚠️ Must attend next 2" |
| **Fees & Payments** | Fee breakup (Tuition ₹12,500, Lab ₹5,000, Exam ₹2,500), Pay button | "Total Outstanding: ₹12,500" |
| **CGPA & Marks** | CGPA score, credits earned, backlogs | "CGPA: 8.74 / Distinction Division" |
| **Certificates** | List of submitted certificate requests | "Bonafide — Under Review" |
| **Digital Twin** | Health score, exam readiness, risk flags | "Health: 94/100 — Optimal Pace" |
| **Student Dataset** | Searchable table of all 20 students | Filter by department, search by name |
| **Staff Directory** | Cards of all 20 faculty members | "Dr. Rajesh Raman — Professor & HOD" |
| **Settings** | Supabase URL, API key input, SQL schema download | Paste key → click "Test Connection" |

#### For Staff (8 tabs):

| Tab | What It Shows |
|---|---|
| **Faculty Overview** | Cabin location, student count, office hours, pending approvals |
| **My Courses** | Course code, specialization, enrolled students, schedule |
| **Attendance Marker** | Table with "+ Present" / "Absent" buttons per student |
| **Certificate Approvals** | Review table with Approve/Reject buttons |
| **Faculty AI Assistant** | Chatbot with staff-specific prompts ("Show top performers") |
| **Student Dataset**, **Staff Dataset**, **Settings** | Same as student view |

### Login Screen
The first thing you see. Has:
- Two tabs: **Student Sign In** and **Faculty / Staff Sign In**
- Input fields for ID/Email and Password
- **1-Click Demo Pills** — pre-filled quick login buttons:
  - 🎓 Aarav Sharma (CSE) — click to instantly log in as student
  - 👨‍🏫 Dr. Rajesh Raman (CSE HOD) — click to instantly log in as staff

---

## 6. Frontend Logic — `static/js/app.js`

This JavaScript file (~1350 lines) is the **engine** that makes the website interactive. Here's what it does:

### Core Responsibilities

| Function | What It Does | Example |
|---|---|---|
| `initApp()` | On page load: fetches students, staff, requests from server; checks for saved login session | "Welcome back, Aarav!" |
| `performLogin()` | Sends login credentials to server; on success, saves session and shows app | Fetches `/api/auth/login` |
| `fallbackLocalLogin()` | If server isn't running, validates credentials using local JS data | Instant demo login |
| `switchTab(tabId)` | Shows the selected tab, hides others, updates sidebar highlight | Click "Fees" → Fees tab appears |
| `renderStudentDashboard()` | Fills in all dashboard cards with logged-in student's data | Sets "91%" in attendance card |
| `renderStaffRoster()` | Shows staff's department students with Present/Absent buttons | Table with 4 CSE students |
| `sendFullAiQuery()` | Sends user message to `/api/chat`, displays typing animation, then AI response | Chat bubble appears |
| `markStudentAttendance()` | Calls `/api/attendance/mark` to update attendance | Click "+ Present" → attendance goes up |
| `renderStudentDirectory()` | Renders the 20-student table with filtering/search | Filter "CSE" → shows only CSE students |
| `injectStaffCopilotChips()` | After staff login, replaces prompt chips with staff-specific ones | "Show students above 7 CGPA" |

### State Management

```javascript
let state = {
  authRole: 'student',      // 'student' or 'staff'
  authUser: null,            // The logged-in person's data object
  students: [],              // All 20 students loaded from server
  staff: [],                 // All 20 staff loaded from server
  allRequests: [],           // All certificate requests
  activeTab: 'dashboard'     // Currently visible tab
};
```

### Session Storage
- Login info is saved in `sessionStorage` (browser memory, lasts until tab closes).
- Supabase API key is saved in `localStorage` (persists across sessions).

---

## 7. Student Data — `data/students.json`

A JSON file containing **20 student records**, each with:

```json
{
  "student_id": "23331a42001",
  "password": "student@123",
  "full_name": "Aarav Sharma",
  "department": "CSE",
  "email": "aarav.sharma1@college.edu",
  "cgpa": 8.74,
  "phone": "+91-9874523101",
  "semester": 8,
  "year": 4,
  "attendance_pct": 91.0,
  "fee_balance": 12500.0,
  "fee_status": "Pending",
  "digital_twin_score": 93,
  "subjects": [
    {
      "code": "CS801",
      "name": "Deep Learning Architecture",
      "attended": 38,
      "total": 41,
      "pct": 92.6
    }
  ],
  "active_requests": [...],
  "recent_activities": [...]
}
```

### 6 Departments Represented

| Department | Code | Example Student | CGPA |
|---|---|---|---|
| Computer Science | CSE | Aarav Sharma | 8.74 |
| Information Technology | IT | Priya Patel | 9.12 |
| Mechanical | MECH | Rohan Reddy | 7.45 |
| Design Engineering | DE | Sneha Nair | 8.89 |
| Civil | CIVIL | Vikram Gupta | 6.82 |
| Electrical | EEE | Ananya Rao | 9.40 |

### Default Login Credentials
All students use password: **`student@123`**
All staff use password: **`staff@123`**

---

## 8. Staff Data — `data/staff.json`

A JSON file containing **20 staff members** — professors, HODs, deans, and officers:

```json
{
  "staff_id": "STF101",
  "password": "staff@123",
  "full_name": "Dr. Rajesh Raman",
  "department": "CSE",
  "designation": "Professor & HOD",
  "email": "rajesh.raman@college.edu",
  "phone": "+91-9840112233",
  "cabin_location": "CS-Block Room 301",
  "specialization": "Deep Learning & AI",
  "experience_years": 18,
  "office_hours": "02:00 PM - 04:00 PM (Mon-Wed)"
}
```

### Staff Categories

| Role | Examples | Count |
|---|---|---|
| **HODs** (Head of Department) | Dr. Rajesh Raman (CSE), Prof. Amitav Sen (IT) | 6 |
| **Professors & Associates** | Dr. Sunita Kulkarni, Dr. Radhika Menon | 10 |
| **Deans** | Dr. Sudhir Joshi (Academics), Prof. Anita Roy (Students) | 2 |
| **Administrative Officers** | Mr. C.K. Narayanan (Exams), Mrs. Sumathi (Finance) | 2 |

---

## 9. Database Schema — `supabase/supabase_schema.sql`

This SQL file defines **9 tables** for the Supabase cloud database. It allows the app to switch from local JSON files to a live cloud database.

### Tables

| Table | Purpose | Key Fields |
|---|---|---|
| `departments` | College departments | dept_code, name, building, hod_name |
| `students` | Student profiles | student_id, cgpa, attendance_pct, fee_balance |
| `staff` | Faculty & staff profiles | staff_id, designation, cabin_location |
| `subjects` | Course catalog | subject_code, name, credits, faculty_id |
| `student_attendance` | Per-student attendance per subject | attended_sessions, total_sessions, percentage |
| `fee_records` | Fee payment tracking | tuition_fee, paid_amount, due_date |
| `certificate_requests` | Certificate applications | certificate_type, status, applied_date |
| `activity_logs` | Student activity timeline | title, description, icon |
| `knowledge_base` | AI chatbot Q&A pairs | question, answer, keywords |

### Key Concept: Row Level Security (RLS)
All tables have RLS enabled — meaning access can be controlled at the row level using policies. Currently all policies allow public access (for development).

### Seed Data
The schema file includes `INSERT` statements that pre-populate the database with real data (students, staff, subjects, sample attendance, fee records, chatbot knowledge).

---

## 10. Dual Data Architecture

One of the most important design decisions: **the app works both online and offline**.

```
┌─────────────────────────────────────────────────┐
│              HYBRID DATA ARCHITECTURE            │
├─────────────────────────────────────────────────┤
│                                                  │
│   WITHOUT Supabase Key          WITH Supabase    │
│   ───────────────────           ──────────────   │
│   Uses local JSON files         Connects to      │
│   (students.json,               cloud database   │
│    staff.json)                  (Supabase)       │
│   All features work             All features     │
│   immediately                   + live sync      │
│   Zero setup needed             Need API key     │
│                                                  │
│   Default mode: ✅               Premium mode: ✅ │
└─────────────────────────────────────────────────┘
```

**How it works in code:**
```javascript
// app.js line 68-71
const storedSupabaseKey = localStorage.getItem('supabase_anon_key');
if (storedSupabaseKey && window.supabase) {
    initSupabase(storedSupabaseKey);  // Connect to cloud
}
```

In **Settings**, the user sees:
- Supabase URL (pre-filled): `https://aqfqdjhddfvyprpwccyp.supabase.co`
- API Key input box (empty by default)
- **Test Connection** button
- Note: *"If no remote key is entered, it uses the local REST API seamlessly!"*

---

## 11. Authentication System

### How Login Works

```
Browser                          server.py
  │                                │
  │ POST /api/auth/login           │
  │ { role: "student",             │
  │   identifier: "23331a42001",   │
  │   password: "student@123" }    │
  │───────────────────────────────►│
  │                                │
  │  authenticate_user()           │
  │  → Load students.json          │
  │  → Find matching ID/email      │
  │  → Check password              │
  │                                │
  │  Returns user object ──────────│
  │  { success: true,              │
  │    token: "token_student_...", │
  │    user: { ...Aarav data... } }│
```

### Supports Both:
- **Student ID** (e.g., `23331a42001`) OR **Email** (e.g., `aarav.sharma1@college.edu`)
- **Staff ID** (e.g., `STF101`) OR **Email** (e.g., `rajesh.raman@college.edu`)

### Case-Insensitive
`23331A42001` and `23331a42001` are treated the same.

### Login Tokens
After login, the server generates a token like:
```
token_student_23331a42001_1695123456
```
This identifies the user for subsequent requests (though no real JWT validation is performed — it's a simplified session system).

### Session Persistence
- `sessionStorage`: Role and user data (cleared when browser tab closes).
- `localStorage`: Supabase key (persists across sessions).

---

## 12. AI Chatbot Engine

The chatbot is **not powered by an external AI model** — it's a **rule-based keyword matching engine** inside `server.py`. It reads your real data and generates context-aware responses.

### How It Works

```
User types: "Can I skip DBMS today?"
    ↓
Lowercase: "can i skip dbms today?"
    ↓
Check role: student
    ↓
Match keyword: "skip" found → attendance inquiry branch
    ↓
Find DBMS in student's subjects:
  CS803 - Database Management Systems: 28/36 = 77.8%
    ↓
Calculate if skip 1 session:
  New: 28/37 = 75.7% → still above 75% but close
    ↓
Return formatted Markdown response with emoji:
  ⚠️ **Attendance Alert for Database Management Systems**:
  - Current: 77.8%
  - After skip: 75.7% (close to cutoff)
  - 💡 Attend next 2 lectures to reach safe zone.
```

### Student Query Types

| Keywords Detected | What It Does | Example Query |
|---|---|---|
| skip, miss, absent, bunk | Predicts attendance if missed | "Can I skip DBMS today?" |
| attendance, percentage | Shows all subject attendance | "What is my attendance?" |
| fee, dues, balance | Shows fee info | "Explain my fee breakup" |
| cgpa, marks, grade | Shows academic tier | "What is my CGPA rank?" |
| bonafide, certificate | Shows certificate process | "How to apply for Bonafide?" |
| (fallback) | Generic welcome message | "Hello" |

### Staff Query Types (additional)

| Keywords Detected | What It Does |
|---|---|
| above, cgpa, top performer | Lists students above CGPA threshold |
| send email, mail to | Auto-emails students above threshold |
| student, roster, shortage | Shows department attendance overview |
| cabin, office hours | Shows staff schedule and location |

---

## 13. Key Features With Examples

### Feature 1: Dashboard Overview
**Who sees it:** Students after login
**Example:**
```
┌──────────────────────────────────────────────┐
│  Good morning, Aarav 👋                      │
│  B.Tech CSE • 4th Year • Semester 8         │
│                                              │
│  [Attendance: 91% On Track]                  │
│  [CGPA: 8.74 Distinction Tier]              │
│  [Tuition: ₹12,500 Due Nov 15]              │
│  [1 Active Request]                          │
└──────────────────────────────────────────────┘
```

### Feature 2: Fee Payment Simulator
**User flow:**
1. Click **"Pay Fees"** → payment modal opens
2. Modal shows: Total payable ₹12,500, method: UPI/Net Banking
3. Click **"Confirm & Pay Now"**
4. Server sets `fee_balance = 0`, `fee_status = 'Paid'`
5. Receipt generated: `REC-2509181430`
6. Dashboard updates: "Fully Paid ✅", card shows ₹0.00

### Feature 3: AI Attendance Advice
**User asks:** *"Can I skip DBMS today?"*

**Student with 77.8% DBMS attendance:**
```
⚠️ Attendance Alert for Database Management Systems:
- Current: 28/36 sessions (77.8%)
- If you skip today: 75.7% — dangerously close to cutoff
- 💡 Attend next 2 lectures to reach 80% safe zone
```

**Student with 92% DBMS attendance:**
```
ℹ️ Attendance Forecast:
- Current: 38/41 sessions (92.6%)
- If you miss 1: 91.7% — well above cutoff ✅
- 💡 You're safe to skip if needed.
```

### Feature 4: Staff Attendance Marker
**Staff (Dr. Rajesh Raman) opens Attendance Marker:**
```
| Student ID    | Name         | Attendance | Actions              |
|---------------|--------------|------------|----------------------|
| 23331a42001  | Aarav Sharma | 91.0%      | [+ Present] [Absent] |
| 23331a42007  | Amit Singh   | 84.0%      | [+ Present] [Absent] |
```
Click **"+ Present"** for Aarav → backend updates → his attendance may increase → table refreshes.

### Feature 5: Certificate Requests
**Student applies:**
1. Click **"Apply for Certificate"** → modal opens
2. Select type: "Bonafide Certificate (Passport/Visa)"
3. Enter purpose: "Passport Renewal"
4. Click **"Submit"**
5. Request ID generated: `REQ-09181430`
6. Status: "In Review" — visible in Certificates tab

**Staff reviews:**
1. Open **"Certificate Approvals"** tab
2. See: `REQ-09181430 | Aarav Sharma | Bonafide | In Review`
3. Click **"Approve"** or **"Reject"**
4. Status updates instantly

### Feature 6: Staff AI Copilot (Unique to Staff)
**Dr. Radhika Menon (IT dept) types:** *"Show students above 7 CGPA"*
```
🏆 **Top Performers — CGPA ≥ 7** (IT Department) — 4 students:
1. **Priya Patel** (23331a42002) — CGPA 9.12 | 🟢 94.3% | 📧 priya.patel2@college.edu
2. **Karthik Verma** (23331a42008) — CGPA 8.15 | 🟢 86.0% | 📧 karthik.verma8@college.edu
...

💡 *To auto-email these 4 students, type: **send email to students above 7***
```

### Feature 7: Digital Twin Health Score
A predictive metric calculated from:
- Attendance consistency
- Internal assessment grades
- Fee clearance timeliness
- Lab milestones

**Example:**
```
Aarav Sharma:
- Attendance: 91% ✅
- CGPA: 8.74 ✅
- Fees: ₹12,500 pending ⚠️
- Twin Score: 93/100 → "High probability of Distinction tier degree"
```

---

## 14. API Endpoints

### GET Endpoints

| Endpoint | Description | Example Response |
|---|---|---|
| `/api/config` | App config + Supabase URL | `{ app_name, version, total_students: 20 }` |
| `/api/students` | All students (filterable by `?dept=`, `?search=`) | `[{ student_id, full_name, ... }, ...]` |
| `/api/students/23331a42001` | Single student record | `{ ...Aarav's full data }` |
| `/api/staff` | All staff | `[{ staff_id, full_name, ... }, ...]` |
| `/api/staff/STF101/courses` | Staff's courses + department students | `{ staff, courses, enrolled_students }` |
| `/api/requests/all` | All pending certificate requests | `[{ request_id, student_name, status }, ...]` |
| `/api/stats` | College statistics | `{ avg_cgpa, avg_attendance, fees_cleared_ratio }` |
| `/api/supabase-schema` | Download SQL schema file | SQL file download |

### POST Endpoints

| Endpoint | Body | Purpose |
|---|---|---|
| `/api/auth/login` | `{ role, identifier, password }` | Authenticate user |
| `/api/chat` | `{ message, user_id, role }` | Chatbot query |
| `/api/fees/pay` | `{ student_id, amount, method }` | Pay fees |
| `/api/requests` | `{ student_id, certificate_type, purpose }` | Apply for certificate |
| `/api/requests/ID/approve` | _(body ignored)_ | Approve request |
| `/api/requests/ID/reject` | _(body ignored)_ | Reject request |
| `/api/attendance/mark` | `{ student_id, subject_name, action }` | Mark attendance |
| `/api/send-email` | `{ staff_id, to_cgpa_above, subject, body_text }` | Bulk email |

---

## 15. How To Run

### Quick Start
```bash
# 1. Navigate to project folder
cd D:\test\smart-college-management

# 2. Start the server
python3 server.py 8080
# Or use the startup script:
./run.sh

# 3. Open browser
# Visit: http://localhost:8080
```

### What You'll See
1. **Login screen** with college branding and demo pills
2. **Click** "🎓 Aarav Sharma (CSE)" for instant student login
3. **Or** click "👨‍🏫 Dr. Rajesh Raman (CSE HOD)" for staff login
4. **Explore** all tabs in the sidebar

### Default Accounts

| Role | ID | Email | Password |
|---|---|---|---|
| Student | `23331a42001` | aarav.sharma1@college.edu | `student@123` |
| Student | `23331a42006` | ananya.rao6@college.edu | `student@123` |
| Staff | `STF101` | rajesh.raman@college.edu | `staff@123` |
| Staff | `STF117` | dean.academics@college.edu | `staff@123` |

---

## 16. Testing

Run the automated test suite:
```bash
python3 test_app.py
```

### What Tests Cover

| Test | What It Verifies |
|---|---|
| `test_01_student_dataset_csv` | CSV has 20 students, first is Aarav Sharma, last is Aditi Sharma |
| `test_02_staff_dataset_csv` | CSV has 20 staff across 7 departments |
| `test_03_student_auth` | Student login by ID, by email, case-insensitive |
| `test_04_staff_auth` | Staff login by ID, by email |
| `test_05_invalid_credentials` | Wrong password rejected, unknown user rejected |
| `test_06_supabase_schema` | SQL file has all required tables and seed data |
| `test_07_chatbot_engine` | AI responds correctly to attendance, fee, faculty, roster queries |

### Expected Output
```
.......
----------------------------------------------------------------------
Ran 7 tests in 0.5s
OK
```

---

## 17. Summary Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    SMART COLLEGE AI PLATFORM                     │
│                                                                  │
│  ┌──────────┐   HTTP/REST API calls   ┌──────────────────────┐  │
│  │  BROWSER │ ◄─────────────────────► │   server.py          │  │
│  │          │                          │  (Python HTTP Server)│  │
│  │ index    │                          │                      │  │
│  │ .html    │                          │ • Auth               │  │
│  │ app.js   │                          │ • AI Chatbot Engine  │  │
│  │          │                          │ • Fee Processor      │  │
│  │ Tailwind │                          │ • Attendance Manager │  │
│  │ CSS      │                          │ • Email Sender       │  │
│  │ Material │                          │ • Certificate Clerk  │  │
│  │ Symbols  │                          │                      │  │
│  └──────────┘                          └──────┬───────────────┘  │
│                                               │                  │
│                          ┌────────────────────┤                  │
│                          │                    │                  │
│                   ┌──────▼──────┐     ┌───────▼────────┐       │
│                   │ students.json│     │  staff.json     │       │
│                   │  (20 records)│     │  (20 records)   │       │
│                   └─────────────┘     └────────────────┘       │
│                                               │                  │
│                          ┌────────────────────┤                  │
│                          │ (Optional)         │                  │
│                   ┌──────▼──────────┐        │                  │
│                   │  Supabase Cloud │        │                  │
│                   │  aqfqdjhddfvy... │        │                  │
│                   │  9 SQL tables   │        │                  │
│                   └─────────────────┘        │                  │
│                                              │                  │
│ ┌────────────────────────────────────────────┘                  │
│ │                                                                │
│ │  USERS:  Students (20)  │  Staff (20)  │  Admins (3)          │
│ │  DEPTs:  CSE, IT, MECH, DE, CIVIL, EEE, ADMIN                  │
│ │  FEATURES: Login, Dashboard, AI Chatbot, Fees, Attendance,     │
│ │            Certificates, Digital Twin, Directories             │
│ └────────────────────────────────────────────────────────────────┘
```

---

### Version Info
- **App Version:** 2.5.0
- **Supabase Project:** `https://aqfqdjhddfvyprpwccyp.supabase.co`
- **Default Port:** 8080
- **Backend:** Python 3 (built-in HTTP server — no external dependencies needed)
- **Frontend:** HTML + Tailwind CSS + Vanilla JavaScript + Material Symbols
- **Database:** Supabase (PostgreSQL) — optional, works locally without it
- **Database Port:** 3306 (MySQL) / 1433 (MSSQL) — not used by this project

---

*Document generated for the Smart College AI Management Platform project.*
*All explanations, examples, and technical details derived from actual project source code.*
