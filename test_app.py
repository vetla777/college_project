#!/usr/bin/env python3
"""
Automated Test Suite for Smart College AI Platform
Validates authentication (ID/Email + Password), datasets, server logic, and chatbot.
"""

import unittest
import json
import os
import csv
from server import authenticate_user, generate_ai_response, load_json, STUDENTS_FILE, STAFF_FILE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENTS_CSV = os.path.join(BASE_DIR, 'data', 'students_dataset.csv')
STAFF_CSV = os.path.join(BASE_DIR, 'data', 'staff_dataset.csv')
STUDENTS_JSON = os.path.join(BASE_DIR, 'data', 'students.json')
STAFF_JSON = os.path.join(BASE_DIR, 'data', 'staff.json')
SCHEMA_SQL = os.path.join(BASE_DIR, 'supabase', 'supabase_schema.sql')

class TestSmartCollegePlatform(unittest.TestCase):

    def test_01_student_dataset_csv(self):
        """Verify students_dataset.csv contains exactly 20 students from Table 1."""
        self.assertTrue(os.path.exists(STUDENTS_CSV), "students_dataset.csv missing")
        with open(STUDENTS_CSV, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 20, "Should have exactly 20 student records")
            self.assertEqual(reader[0]['Student ID'], '23331a42001')
            self.assertEqual(reader[0]['Full Name'], 'Aarav Sharma')
            self.assertEqual(reader[0]['Department'], 'CSE')
            self.assertEqual(reader[0]['CGPA'], '8.74')
            self.assertEqual(reader[19]['Student ID'], '23331a42020')
            self.assertEqual(reader[19]['Full Name'], 'Aditi Sharma')

    def test_02_staff_dataset_csv(self):
        """Verify staff_dataset.csv contains 20 generated staff members."""
        self.assertTrue(os.path.exists(STAFF_CSV), "staff_dataset.csv missing")
        with open(STAFF_CSV, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 20, "Should have 20 staff records")
            self.assertIn('Dr. Rajesh Raman', [r['Full Name'] for r in reader])
            self.assertIn('Prof. Amitav Sen', [r['Full Name'] for r in reader])
            departments = {r['Department'] for r in reader}
            self.assertTrue({'CSE', 'IT', 'MECH', 'DE', 'CIVIL', 'EEE', 'ADMIN'}.issubset(departments))

    def test_03_student_auth_by_id_and_email(self):
        """Verify student can login via Student ID OR Email + Password."""
        # By Student ID
        user1, err1 = authenticate_user('student', '23331a42001', 'student@123')
        self.assertIsNone(err1)
        self.assertIsNotNone(user1)
        self.assertEqual(user1['full_name'], 'Aarav Sharma')

        # By Email
        user2, err2 = authenticate_user('student', 'aarav.sharma1@college.edu', 'student@123')
        self.assertIsNone(err2)
        self.assertIsNotNone(user2)
        self.assertEqual(user2['student_id'], '23331a42001')

        # Case-insensitivity
        user3, err3 = authenticate_user('student', '23331A42001', 'student@123')
        self.assertIsNone(err3)
        self.assertEqual(user3['student_id'], '23331a42001')

    def test_04_staff_auth_by_id_and_email(self):
        """Verify staff can login via Staff ID OR Email + Password."""
        # By Staff ID
        st1, err1 = authenticate_user('staff', 'STF101', 'staff@123')
        self.assertIsNone(err1)
        self.assertIsNotNone(st1)
        self.assertEqual(st1['full_name'], 'Dr. Rajesh Raman')
        self.assertEqual(st1['department'], 'CSE')

        # By Email
        st2, err2 = authenticate_user('staff', 'rajesh.raman@college.edu', 'staff@123')
        self.assertIsNone(err2)
        self.assertIsNotNone(st2)
        self.assertEqual(st2['staff_id'], 'STF101')

    def test_05_auth_invalid_credentials(self):
        """Verify invalid passwords or non-existent identifiers are rejected."""
        # Wrong password
        user, err = authenticate_user('student', '23331a42001', 'wrongpassword')
        self.assertIsNone(user)
        self.assertIn("Incorrect password", err)

        # Non-existent user
        user2, err2 = authenticate_user('student', '99999999', 'student@123')
        self.assertIsNone(user2)
        self.assertIn("No student found", err2)

        # Staff wrong password
        st, err_st = authenticate_user('staff', 'STF101', 'wrongpwd')
        self.assertIsNone(st)
        self.assertIn("Incorrect password", err_st)

    def test_06_supabase_schema(self):
        """Verify Supabase schema file exists and contains valid DDL/DML."""
        self.assertTrue(os.path.exists(SCHEMA_SQL))
        with open(SCHEMA_SQL, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("CREATE TABLE IF NOT EXISTS public.students", content)
            self.assertIn("CREATE TABLE IF NOT EXISTS public.staff", content)
            self.assertIn("CREATE TABLE IF NOT EXISTS public.knowledge_base", content)
            self.assertIn("23331a42001", content)
            self.assertIn("STF101", content)
            self.assertIn("https://aqfqdjhddfvyprpwccyp.supabase.co", content)

    def test_07_chatbot_engine(self):
        """Verify AI Chatbot query processing for both students and staff."""
        # Student query: Can I skip DBMS?
        r1 = generate_ai_response("Can I skip DBMS today?", "23331a42001", role='student')
        self.assertIn("Database Management Systems", r1)
        self.assertIn("75%", r1)

        # Student query: Fee breakup
        r2 = generate_ai_response("Explain my tuition fee breakup", "23331a42001", role='student')
        self.assertIn("Tuition", r2)
        self.assertIn("12,500", r2)

        # Staff query: Student roster and shortage
        r3 = generate_ai_response("Show student attendance shortage in my class", "STF101", role='staff')
        self.assertIn("Faculty Roster Overview", r3)

        # Faculty lookup
        r4 = generate_ai_response("Who is the HOD of CSE?", "23331a42001", role='student')
        self.assertIn("Rajesh Raman", r4)
        self.assertIn("CS-Block Room 301", r4)

if __name__ == '__main__':
    unittest.main()
