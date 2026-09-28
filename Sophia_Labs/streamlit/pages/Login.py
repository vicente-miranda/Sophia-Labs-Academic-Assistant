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
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu

# Your data loader or user retrieval function
from Sophia_Labs.data.loader import retrieve_data

# The menu function that sets up sidebars and possibly handles logout
from menu import menu

# Show the menu (unauthenticated or authenticated)
menu()

# Ensure we have an authentication status in session
if "authentication_status" not in st.session_state:
    st.session_state.authentication_status = False

user_data = retrieve_data()
usernames = user_data["username"] 
plain_text_passwords = user_data["password"]
print(user_data)
print(user_data["username"][0])
print(user_data["password"][0])


# Hash the passwords for streamlit_authenticator
hashed_passwords = stauth.Hasher(plain_text_passwords).generate()

# Configure streamlit_authenticator
authenticator = stauth.Authenticate(
    usernames,
    usernames,
    hashed_passwords,
    cookie_name="my_unique_cookie_name",
    key="my_auth_key",
    cookie_expiry_days=0
)


display_name, authentication_status, username = authenticator.login("Log-in to your account", "main")
print(display_name, authentication_status, username)

if authentication_status is False:
    st.error("Incorrect credentials")

    if st.button("Don't have an account yet? Register here!"):
        # Switch to your register page
        st.switch_page("Register")

elif authentication_status is True:
    st.title("Welcome Back!")
    st.success("Login Successful!")
    # Mark user as logged in
    st.session_state.authentication_status = True
    st.session_state.username = username

else:
    st.warning("Please enter your username and password")
    if st.button("Don't have an account yet? Register here!"):
        st.switch_page("Register")
