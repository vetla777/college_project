import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENTS_CSV = os.path.join(BASE_DIR, 'students_dataset.csv')
STAFF_CSV = os.path.join(BASE_DIR, 'staff_dataset.csv')
STUDENTS_JSON = os.path.join(BASE_DIR, 'students.json')
STAFF_JSON = os.path.join(BASE_DIR, 'staff.json')

# Subject mapping by department
DEPT_SUBJECTS = {
    'CSE': [
        {'code': 'CS801', 'name': 'Deep Learning Architecture', 'attended': 38, 'total': 41, 'pct': 92.6},
        {'code': 'CS802', 'name': 'Natural Language Processing', 'attended': 34, 'total': 38, 'pct': 89.4},
        {'code': 'CS803', 'name': 'Database Management Systems', 'attended': 28, 'total': 36, 'pct': 77.8},
        {'code': 'CS804', 'name': 'Distributed Cloud Systems', 'attended': 32, 'total': 35, 'pct': 91.4}
    ],
    'IT': [
        {'code': 'IT801', 'name': 'Cloud Infrastructure & DevOps', 'attended': 39, 'total': 40, 'pct': 97.5},
        {'code': 'IT802', 'name': 'Modern Web Architectures', 'attended': 35, 'total': 38, 'pct': 92.1},
        {'code': 'IT803', 'name': 'Cybersecurity & Ethical Hacking', 'attended': 31, 'total': 36, 'pct': 86.1},
        {'code': 'IT804', 'name': 'Big Data Analytics Engine', 'attended': 33, 'total': 35, 'pct': 94.3}
    ],
    'MECH': [
        {'code': 'ME801', 'name': 'Robotics & Mechatronics', 'attended': 33, 'total': 40, 'pct': 82.5},
        {'code': 'ME802', 'name': 'Finite Element Method', 'attended': 29, 'total': 38, 'pct': 76.3},
        {'code': 'ME803', 'name': 'Computational Fluid Dynamics', 'attended': 34, 'total': 38, 'pct': 89.5},
        {'code': 'ME804', 'name': 'Automotive Powertrains', 'attended': 30, 'total': 35, 'pct': 85.7}
    ],
    'DE': [
        {'code': 'DE801', 'name': 'IoT & Sensor Systems Design', 'attended': 35, 'total': 38, 'pct': 92.1},
        {'code': 'DE802', 'name': 'Rapid Prototyping & CAD', 'attended': 32, 'total': 36, 'pct': 88.9},
        {'code': 'DE803', 'name': 'Human-Centered Product Design', 'attended': 34, 'total': 38, 'pct': 89.5},
        {'code': 'DE804', 'name': 'Embedded Firmware & RTOS', 'attended': 30, 'total': 36, 'pct': 83.3}
    ],
    'CIVIL': [
        {'code': 'CV801', 'name': 'Advanced Structural Dynamics', 'attended': 29, 'total': 38, 'pct': 76.3},
        {'code': 'CV802', 'name': 'Earthquake Resistant Design', 'attended': 31, 'total': 38, 'pct': 81.6},
        {'code': 'CV803', 'name': 'Geotechnical Site Exploration', 'attended': 33, 'total': 38, 'pct': 86.8},
        {'code': 'CV804', 'name': 'Environmental Impact Analysis', 'attended': 35, 'total': 40, 'pct': 87.5}
    ],
    'EEE': [
        {'code': 'EE801', 'name': 'Smart Grid & Power Quality', 'attended': 38, 'total': 40, 'pct': 95.0},
        {'code': 'EE802', 'name': 'Electric Vehicle Drives & Batteries', 'attended': 36, 'total': 38, 'pct': 94.7},
        {'code': 'EE803', 'name': 'High Voltage Engineering', 'attended': 32, 'total': 36, 'pct': 88.9},
        {'code': 'EE804', 'name': 'Industrial Automation & PLC', 'attended': 34, 'total': 36, 'pct': 94.4}
    ]
}

# 1. Parse Students
students = []
with open(STUDENTS_CSV, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        student_id = row['Student ID'].strip()
        cgpa = float(row['CGPA'].strip())
        dept = row['Department'].strip()
        
        # Calculate dynamic realistic stats
        attendance_base = round(min(98.5, max(68.0, 72.0 + (cgpa - 6.5) * 8.5)), 1)
        twin_score = int(min(100, max(65, int(cgpa * 10 + (attendance_base - 70) * 0.3))))
        fee_balance = 0.0 if cgpa > 9.0 else (12500.0 if cgpa > 7.5 else 18500.0)
        fee_status = "Paid" if fee_balance == 0.0 else ("Partial" if fee_balance < 10000 else "Pending")
        
        subjects = DEPT_SUBJECTS.get(dept, DEPT_SUBJECTS['CSE'])
        
        students.append({
            'student_id': student_id,
            'password': row['Passwords'].strip(),
            'full_name': row['Full Name'].strip(),
            'department': dept,
            'email': row['Email Address'].strip(),
            'cgpa': cgpa,
            'phone': row['Phone Number'].strip(),
            'semester': 8,
            'year': 4,
            'attendance_pct': attendance_base,
            'fee_balance': fee_balance,
            'fee_status': fee_status,
            'digital_twin_score': twin_score,
            'subjects': subjects,
            'active_requests': [
                {
                    'request_id': f'REQ-{1000 + len(students)}',
                    'certificate_type': 'Bonafide Certificate (Passport / Visa)',
                    'status': 'In Review',
                    'applied_date': '2026-09-14',
                    'remarks': 'Dean academic approval pending'
                }
            ],
            'recent_activities': [
                {
                    'title': 'Biometric Attendance Recorded',
                    'description': f'{dept} Lab 404 • Console RFID check verified',
                    'time_label': 'Today, 10:42 AM',
                    'icon': 'check_circle',
                    'color': 'emerald'
                },
                {
                    'title': 'Academic Twin Synchronized',
                    'description': f'Semester 8 SGPA model confidence: {twin_score}%',
                    'time_label': 'Yesterday',
                    'icon': 'hub',
                    'color': 'purple'
                }
            ]
        })

with open(STUDENTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(students, f, indent=2)

# 2. Parse Staff
staff = []
with open(STAFF_CSV, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        staff.append({
            'staff_id': row['Staff ID'].strip(),
            'password': row['Passwords'].strip(),
            'full_name': row['Full Name'].strip(),
            'department': row['Department'].strip(),
            'designation': row['Designation'].strip(),
            'email': row['Email Address'].strip(),
            'phone': row['Phone Number'].strip(),
            'cabin_location': row['Cabin Location'].strip(),
            'specialization': row['Specialization'].strip(),
            'experience_years': int(row['Experience Years'].strip()),
            'office_hours': row['Office Hours'].strip()
        })

with open(STAFF_JSON, 'w', encoding='utf-8') as f:
    json.dump(staff, f, indent=2)

print(f"Generated {len(students)} student records and {len(staff)} staff records.")
