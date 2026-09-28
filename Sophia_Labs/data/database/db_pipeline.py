# Proprietary License
# Effective Date: 3rd of January of 2025
#
# Copyright (c) 2025 Sophia Labs
#
# This software is the proprietary property of Sophia Labs and is provided exclusively for 
# evaluation purposes by Tiago Santos or NOVA IMS staff. Any other use, reproduction, 
# distribution, or modification without explicit written permission from the authors 
# is strictly prohibited.
#
# Consult the license for detailed terms and conditions before using this software.

import sqlite3
import random
import csv
import os
from faker import Faker
from datetime import datetime, timedelta
from Sophia_Labs.data.loader import connect_to_database

faker = Faker()

def drop_tables(conn):
    """
    Drops all tables if they exist.
    This ensures we start with a fresh database each time.
    """
    cursor = conn.cursor()

    # Drop tables in reverse order of dependency to avoid foreign key constraints.
    cursor.execute("DROP TABLE IF EXISTS Subject_Staff_AcademicTerm")
    cursor.execute("DROP TABLE IF EXISTS Teaching_Staff")
    cursor.execute("DROP TABLE IF EXISTS Users_Schedule")
    cursor.execute("DROP TABLE IF EXISTS Schedule")
    cursor.execute("DROP TABLE IF EXISTS Grades")
    cursor.execute("DROP TABLE IF EXISTS Evaluations")
    cursor.execute("DROP TABLE IF EXISTS Degrees_Subjects")
    cursor.execute("DROP TABLE IF EXISTS Subjects")
    cursor.execute("DROP TABLE IF EXISTS Degrees")
    cursor.execute("DROP TABLE IF EXISTS Users")
    cursor.execute("DROP TABLE IF EXISTS Personal_Notes")

    conn.commit()

def create_tables(conn):
    cursor = conn.cursor()
    
    # 1) USERS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            course TEXT NOT NULL,
            year_of_study INTEGER NOT NULL,
            semester TEXT NOT NULL,
            academic_year TEXT NOT NULL,
            FOREIGN KEY (course) REFERENCES Degrees(degree_name),
            FOREIGN KEY (year_of_study) REFERENCES Degrees(year),
            FOREIGN KEY (semester) REFERENCES Subject_Staff_AcademicTerm(semester),
            FOREIGN KEY (academic_year) REFERENCES Subject_Staff_AcademicTerm(academic_year),
            UNIQUE(username)
        )
    ''')

    # 2) DEGREES
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Degrees (
            degree_id INTEGER PRIMARY KEY,
            degree_name TEXT NOT NULL,
            year INTEGER
        )
    ''')

    # 3) SUBJECTS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Subjects (
            subject_id INTEGER PRIMARY KEY,
            subject_name TEXT NOT NULL,
            credits INTEGER,
            syllabus TEXT,
            content TEXT
        )
    ''')

    # 4) DEGREES_SUBJECTS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Degrees_Subjects (
            degree_id INTEGER,
            subject_id INTEGER,
            PRIMARY KEY (degree_id, subject_id),
            FOREIGN KEY (degree_id) REFERENCES Degrees(degree_id),
            FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id)
        )
    ''')

    # 5) EVALUATIONS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Evaluations (
            evaluation_id INTEGER PRIMARY KEY,
            subject_id INTEGER,
            evaluation_name TEXT,
            evaluation_date DATETIME,
            evaluation_type TEXT,
            FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id)
        )
    ''')

    # 6) GRADES
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Grades (
            grade_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            evaluation_id INTEGER,
            grade REAL,
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (evaluation_id) REFERENCES Evaluations(evaluation_id)
        )
    ''')

    # 7) SCHEDULE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Schedule (
            schedule_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            subject_id INTEGER,
            event_type INTEGER,     -- e.g., 1=Lecture, 2=Lab, etc.
            start_time TIME,
            end_time TIME,
            description TEXT,
            local TEXT,
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id)
        )
    ''')

    # 8) USERS_SCHEDULE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users_Schedule (
            user_id INTEGER,
            subject_id INTEGER,
            PRIMARY KEY (user_id, subject_id),
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id)
        )
    ''')

    # 9) TEACHING_STAFF
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Teaching_Staff (
            staff_id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    ''')
    

    # 10) SUBJECT_STAFF_ACADEMICTERM (Replaces old Subject_Staff)
    #
    #  - degree_id: which degree (e.g., Data Science, Info Management, etc.)
    #  - subject_id: which course or subject
    #  - staff_id: who teaches it
    #  - academic_year: "2024/2025", "2023/2024", etc.
    #  - semester: "Fall", "Spring", "1st", "2nd", etc.
    #
    #  This table allows you to store multiple entries for the same subject
    #  across different academic years or semesters, with possibly different staff or degrees.
    #
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Subject_Staff_AcademicTerm (
            subject_staff_term_id INTEGER PRIMARY KEY,
            degree_id INTEGER,
            subject_id INTEGER,
            staff_id INTEGER,
            academic_year TEXT NOT NULL,
            semester TEXT NOT NULL,
            FOREIGN KEY (degree_id) REFERENCES Degrees(degree_id),
            FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id),
            FOREIGN KEY (staff_id) REFERENCES Teaching_Staff(staff_id)
        )
    ''')
    # 11) Personal Notes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Personal_Notes (
            note_id INTEGER PRIMARY KEY,
            note TEXT,
            user_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
    
    ''')

    conn.commit()

def main():
    # ---------------------------------------
    # 1) SEED for Reproducibility
    # ---------------------------------------
    random.seed(0)
    Faker.seed(0)

    # ---------------------------------------
    # 2) Connect to DB and Drop Tables
    # ---------------------------------------
    conn = connect_to_database()
    drop_tables(conn)  # Comment this out to NOT clear old data

    # ---------------------------------------
    # 3) Create Tables, Populate, and Query
    # ---------------------------------------
    create_tables(conn)
    conn.close()

if __name__ == "__main__":
    main()
