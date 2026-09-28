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

import os
import sqlite3
from typing import Any
from datetime import datetime

# Define the base directory for data files
BASE_DIR = os.path.dirname(__file__)

def get_database_path(db_name: str = "academic_management.db") -> str:
    """
    Get the absolute path to the SQLite database file.

    Args:
        db_name (str): The name of the database file. Default is 'academic_management.db'.

    Returns:
        str: The absolute path to the database file.
    """
    db_path = os.path.join(BASE_DIR, "database", db_name)
    return db_path

def connect_to_database(db_name: str = "academic_management.db") -> sqlite3.Connection:
    """
    Establish a connection to the SQLite database.

    Args:
        db_name (str): The name of the database file. Default is 'academic_management.db'.

    Returns:
        sqlite3.Connection: A connection object for the database.
    """
    db_path = get_database_path(db_name)
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found at {db_path}")
    print('db_path:', db_path)
    return sqlite3.connect(db_path)

def load_pickle_file(filename: str) -> Any:
    """
    Load data from a pickle file in the `data/database` folder.

    Args:
        filename (str): The name of the file to load.

    Returns:
        Any: The data deserialized from the pickle file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file cannot be deserialized.
    """
    import pickle  # Import locally as it may not always be needed
    file_path = os.path.join(BASE_DIR, "database", filename)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "rb") as handle:
        data = pickle.load(handle)

    return data

def fetch_all_from_table(table_name: str) -> list[tuple]:
    """
    Fetch all rows from a given table in the database.

    Args:
        table_name (str): The name of the table to query.

    Returns:
        list[tuple]: A list of tuples containing all rows from the table.

    Raises:
        sqlite3.OperationalError: If the table does not exist in the database.
    """
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        conn.close()
        raise sqlite3.OperationalError(f"Error accessing table '{table_name}': {str(e)}")

    conn.close()
    return rows

def retrieve_data():
    """
    Retrieve all user data from the users table in the database.

    Returns:
        dict: A dictionary where each key is a column name and values are lists of column data.
    """
    conn = connect_to_database()
    cursor = conn.cursor()

    # Retrieve all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Assuming you know the table name, for example, 'users'
    table_name = "Users"  # Replace this with your actual table name

    # Retrieve column names
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [col[1] for col in cursor.fetchall()]

    # Retrieve data from the table
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    # Create a dictionary for each column
    column_data = {col: [] for col in columns}
    for row in rows:
        for idx, value in enumerate(row):
            column_data[columns[idx]].append(value)
    
    conn.close()
    return column_data


def is_username_unique(username):
    """
    Check if the given username is unique in the user data dictionary.

    Args:
        username (str): The username to check.
        user_data (dict): Dictionary containing user information.

    Returns:
        bool: True if the username is unique, False otherwise.
    """
    user_data=retrieve_data()
    return username not in user_data["username"]

def is_course_valid(course):
    """
    Check if the given course is valid.

    Args:
        course (str): The course to check.

    Returns:
        bool: True if the course is valid, False otherwise.
    """
    valid_courses = ["data science", "information management", "information systems"]
    return course.lower() in valid_courses

def is_year_of_study_valid(year):
    """
    Check if the given year of study is valid.

    Args:
        year (str): The year of study to check.

    Returns:
        bool: True if the year of study is valid, False otherwise.
    """
    return year.isdigit() and 1 <= int(year) <= 3

def get_semester_from_date() -> str:
    """
    Get the semester based on the current date.

    Returns:
        str: The semester corresponding to the current date.
    """
    now = datetime.now()
    year = now.year
    month = now.month
    if month < 6:
        return f"Spring"
    else:
        return f"Fall"
    
def get_academic_year() -> str:
    """
    Get the academic year based on the current date.

    Returns:
        str: The academic year corresponding to the current date.
    """
    now = datetime.now()
    year = now.year
    month = now.month
    if month < 6:
        return f"{year-1}/{year}"
    else:
        return f"{year}/{year+1}"

def add_user_to_database(username, password, course, year_of_study, semester, academic_year):
    """
    Add a new user to the database.

    Args:
        username (str): The username of the new user.
        password (str): The hashed password of the new user.
        course (str): The course of the new user.   
        year_of_study (int): The year of study of the new user.
        semester (str): The semester of the new user.
        academic_year (str): The academic year of the new user.

    Returns:
        bool: True if the user was added successfully, False otherwise.
    """
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Users (username, password, course, year_of_study, semester, academic_year) VALUES (?, ?, ?, ?, ?, ?)",
        (username, password, course, year_of_study, semester, academic_year),
    )
    conn.commit()
    conn.close()
    return True

