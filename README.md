# 🎓 Smart College AI — Digital Twin OS & Management Platform

A modern, full-stack Academic Management & Digital Twin Web Platform featuring an **interactive campus AI Chatbot**, **Student dataset (20 students)**, **Staff dataset (20 faculty & leaders)**, and backend integration configured for Supabase project URL: **`https://aqfqdjhddfvyprpwccyp.supabase.co`**.

---

## 🌟 Key Capabilities

1. **Academic Student Workspace**:
   - **Dashboard**: Live attendance percentages, CGPA/SGPA tracking, tuition fee dues, active certificate requests, priority shortage warnings, recent activity feed, digital twin health snapshot, and upcoming schedules.
   - **Student Profile Switcher**: Instantly switch between all 20 enrolled students from the top bar to inspect personalized records, grades, and dues.
   - **Attendance Ledger**: Subject-by-subject attendance progress with dynamic 75% cutoff and safe-to-miss vs. must-attend calculations.
   - **Fee Management**: Interactive fee settlement simulator with immediate digital receipt generation.
   - **Certificates Desk**: Apply for Bonafide, Provisional, Course Completion letters with real-time status tracking.

2. **Campus AI Copilot & Chatbot**:
   - Integrated in the dashboard quick widget, modal, and dedicated AI Assistant tab.
   - Accurately answers questions on:
     - Attendance thresholds: *"Can I skip DBMS today?"*
     - Fee balances & due dates: *"Explain Sem 8 fee breakup"*
     - Faculty office locations & hours: *"Where is Dr. Rajesh Raman's cabin?"*, *"Who is HOD of CSE?"*
     - University guidelines: Minimum 75% attendance policy, examination schedules, bonafide application procedures.

3. **Administrative Governance Hub**:
   - **Control Center**: Institution-wide metrics, cohort averages, fee recovery rates.
   - **Request Monitor**: Review, approve, or reject student certificate requests.
   - **Agent Fleet**: Autonomous background agents (Attendance Sentinel, Fee Clearance Bot, Digital Twin Predictor).

4. **Dual Data Architecture & Supabase Cloud**:
   - **Supabase Project**: `https://aqfqdjhddfvyprpwccyp.supabase.co`
   - **Schema & Migrations**: Complete DDL and seed queries in `supabase/supabase_schema.sql`.
   - **Hybrid Connectivity**: Works out of the box using local datasets, and seamlessly activates live cloud synchronization when the user enters their Supabase Anon key.

---

## 📊 Datasets Included

### 1. Student Dataset (`data/students_dataset.csv` & `data/students.json`)
Contains the 20 students across 6 departments (`CSE`, `IT`, `MECH`, `DE`, `CIVIL`, `EEE`):
- `23331a42001` — Aarav Sharma (CSE, CGPA: 8.74)
- `23331a42002` — Priya Patel (IT, CGPA: 9.12)
- `23331a42003` — Rohan Reddy (MECH, CGPA: 7.45)
- `23331a42004` — Sneha Nair (DE, CGPA: 8.89)
- `23331a42005` — Vikram Gupta (CIVIL, CGPA: 6.82)
- `23331a42006` — Ananya Rao (EEE, CGPA: 9.40)
- `23331a42007` — Amit Singh (CSE, CGPA: 7.91)
- `23331a42008` — Karthik Verma (IT, CGPA: 8.15)
- `23331a42009` — Pooja Joshi (MECH, CGPA: 7.20)
- `23331a42010` — Rahul Mishra (CIVIL, CGPA: 8.05)
- `23331a42011` — Divya Kumar (EEE, CGPA: 8.90)
- `23331a42012` — Suresh Das (DE, CGPA: 6.75)
- `23331a42013` — Meera Kulkarni (CSE, CGPA: 9.60)
- `23331a42014` — Arjun Chatterjee (IT, CGPA: 7.80)
- `23331a42015` — Neha Verma (MECH, CGPA: 8.34)
- `23331a42016` — Manish Reddy (CIVIL, CGPA: 6.95)
- `23331a42017` — Kavya Iyer (EEE, CGPA: 9.18)
- `23331a42018` — Ravi Singh (CSE, CGPA: 8.42)
- `23331a42019` — Swati Gupta (DE, CGPA: 7.65)
- `23331a42020` — Aditi Sharma (IT, CGPA: 9.05)

### 2. Staff Dataset (`data/staff_dataset.csv` & `data/staff.json`)
Contains 20 faculty leaders and officers across all departments:
- `STF101` — Dr. Rajesh Raman (CSE HOD, Deep Learning & AI, CS-301)
- `STF102` — Dr. Sunita Kulkarni (CSE Assoc Prof, Distributed Cloud Systems, CS-305)
- `STF103` — Prof. Vikram Saxena (CSE Asst Prof, Database Management Systems, CS-208)
- `STF104` — Er. Ananya Sen (CSE Senior Lab Instructor, AI Lab 404)
- `STF105` — Prof. Amitav Sen (IT HOD, Cloud Infrastructure & DevOps, IT-201)
- `STF106` — Dr. Radhika Menon (IT Assoc Prof, Natural Language Processing, IT-204)
- `STF107` — Prof. Tarun Bansal (IT Asst Prof, Full Stack Web, IT-212)
- `STF108` — Dr. K. V. Narayana (MECH HOD, Robotics & Thermal Systems, ME-101)
- `STF109` — Prof. Deepak Chawla (MECH Asst Prof, CAD/CAM & FEA, ME-108)
- `STF110` — Er. Ramesh Iyer (MECH Workshop Superintendent, Central Bay 2)
- `STF111` — Dr. Shalini Deshmukh (DE HOD, Design Thinking & IoT, DE-401)
- `STF112` — Prof. Nikhil Bansal (DE Asst Prof, Rapid Prototyping & 3D, DE-405)
- `STF113` — Dr. Hariprasad Varma (CIVIL HOD, Structural Dynamics, CV-102)
- `STF114` — Prof. Geetha Krishnan (CIVIL Assoc Prof, Geotechnical & GIS, CV-107)
- `STF115` — Dr. Venkatachalam P. (EEE HOD, Smart Grid & Renewable Energy, EE-201)
- `STF116` — Prof. Archana Nambiar (EEE Asst Prof, EV Drives & Power, EE-206)
- `STF117` — Dr. Sudhir B. Joshi (Dean of Academics, Admin-102)
- `STF118` — Prof. Anita Roy (Dean of Student Affairs, Admin-105)
- `STF119` — Mr. C. K. Narayanan (Controller of Examinations, Exam Cell-10)
- `STF120` — Mrs. Sumathi Sundaram (Finance & Accounts Officer, Accounts Counter-1)

---

## 🚀 How to Launch the Web Portal

### 1. Quick Startup
In your terminal, navigate to the project directory and run:

```bash
cd /Users/harish/.gemini/antigravity/scratch/smart-college-management
./run.sh
```

Or directly via Python:

```bash
python3 server.py 8080
```

### 2. Access the Application
Open your browser and navigate to:
👉 **[http://localhost:8080](http://localhost:8080)**

---

## ⚡ Supabase Setup (Project: `aqfqdjhddfvyprpwccyp.supabase.co`)

To load the database tables directly into your Supabase cloud project:

1. Open your [Supabase Dashboard](https://supabase.com/dashboard/project/aqfqdjhddfvyprpwccyp).
2. Click on the **SQL Editor** tab on the left menu.
3. Open or copy the file:
   `supabase/supabase_schema.sql`
4. Paste the SQL and click **Run**.
5. Once executed, go to **Project Settings -> API** and copy your `anon` `public` key.
6. In the web portal, navigate to the **Settings** tab and paste your key into the **Supabase Anon Public API Key** field, then click **Test Connection**.

---

## 🧪 Verification & Testing

To run the automated test suite:

```bash
python3 test_app.py
```
