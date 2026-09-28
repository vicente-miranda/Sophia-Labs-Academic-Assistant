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

import re
import streamlit as st

# Various data loader utility functions
from Sophia_Labs.data.loader import (
    add_user_to_database,
    is_username_unique,
    is_course_valid,
    is_year_of_study_valid,
    get_semester_from_date,
    get_academic_year
)

from menu import menu

def is_valid_username(username: str) -> bool:
    """
    Checks if the username has at least 3 characters.
    """
    return len(username) > 2

st.title("User Registration")

# Optionally show a sidebar or handle navigation
menu()

# Provide a close button
empty_space, button_place = st.columns((18, 1))
with button_place:
    # Use type="secondary" because Streamlit only supports "primary" or "secondary"
    if st.button("", type="secondary", icon=":material/close:"):
        # Switch to home or any other page
        st.switch_page("Home")

with st.form("registration_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    course = st.text_input("Nova IMS Course")
    year_of_study = st.text_input("Year of Study")
    semester = get_semester_from_date()
    academic_year = get_academic_year()

    submit = st.form_submit_button("Register")

    if submit:
        if not all([username, password, course, year_of_study]):
            st.error("Please fill all fields")
            st.session_state.authentication_status = False

        elif not is_valid_username(username):
            st.error("A username must have at least 3 characters")
            st.session_state.authentication_status = False

        elif len(password) < 8:
            st.error("Password must be at least 8 characters")
            st.session_state.authentication_status = False

        elif not is_username_unique(username):
            st.error("Username already registered")
            st.session_state.authentication_status = False

        elif not is_course_valid(course):
            st.error("Please enter a valid course")
            st.session_state.authentication_status = False

        elif not is_year_of_study_valid(year_of_study):
            st.error("Please enter a valid year of study")
            st.session_state.authentication_status = False

        else:
            # Attempt to create the user in the database
            success = add_user_to_database(username, password, course, year_of_study, semester, academic_year)
            if success:
                st.success("Registration Successful! You can now login.")
                # Mark the user as authenticated immediately
                st.session_state.authentication_status = True
                st.session_state.username = username
            else:
                st.error("Registration failed. Please try again.")
                st.session_state.authentication_status = False
                # Possibly switch to home or show an error
