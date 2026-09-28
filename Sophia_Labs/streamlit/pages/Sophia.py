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
import openai
import os
from dotenv import load_dotenv

# Menu import (ensures we can display correct sidebar or handle logout)
from menu import menu

# Chatbot import
from Sophia_Labs.chatbot.bot import SophiaChatbot

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

menu()

if "authentication_status" not in st.session_state or not st.session_state.authentication_status:
    st.warning("You are not logged in. Please log in first.")
    st.stop()

st.title("Sophia")

# Initialize chat history if not present
if "messages" not in st.session_state:
    st.session_state.messages = []

def main(user_input: str) -> str:
    """
    Process user input through the SophiaChatbot and return the response.
    """
    try:
        # Retrieve the username or a placeholder
        user_name = st.session_state.get("username", "UnknownUser")

        # You can pass user_id or conversation_id if your bot tracks them.
        bot = SophiaChatbot(user_id=1, conversation_id=1)
        response = bot.process_user_input({"user_input": user_input})
        return response
    except Exception as e:
        return f"Error: {str(e)}"

# Display any existing conversation messages
for message in st.session_state.messages:
    with st.chat_message(name=message["role"]):
        st.markdown(message["content"])

# Provide a text input for the user at the bottom of the screen
prompt = st.chat_input("What is on your mind?")
if prompt:
    # Add the user's message to the chat
    with st.chat_message(name="user"):
        st.markdown(prompt)

    # Get bot response
    response = main(prompt)

    # Update session state with user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display the bot's response
    with st.chat_message(name="assistant"):
        st.markdown(response)

    # Add the bot’s response to the conversation
    st.session_state.messages.append({"role": "assistant", "content": response})
