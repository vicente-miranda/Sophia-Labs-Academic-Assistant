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

import streamlit as st

def authenticated_menu():
    # Navigation links for authenticated users
    # Removed the "Sophia" link to exclude the "App" tab
    logout = st.sidebar.button("Logout", key="logout_btn_unique")
    if logout:
        # On logout, set auth to False and switch to "Home" page
        st.session_state.authentication_status = False
        st.switch_page("pages/Home.py")

def unauthenticated_menu():
    # Navigation links for unauthenticated users
    st.sidebar.page_link("pages/Home.py", label="Home", icon="🏠")
    st.sidebar.page_link("pages/Login.py", label="Log in", icon="🔑")
    st.sidebar.page_link("pages/Register.py", label="Register", icon="🆕")

def menu(start=False, change=False):
    # Initialize authentication status if not present
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = False

    # Route to home if start is True
    if start:
        st.switch_page("pages/Home.py")
        return

    # Change page after login/register if change is True
    if change:
        st.switch_page("pages/Home.py")  # Redirect to Home or another page as needed
        return

    # Display appropriate menu based on authentication status
    if st.session_state.authentication_status:
        authenticated_menu()
    else:
        unauthenticated_menu()
