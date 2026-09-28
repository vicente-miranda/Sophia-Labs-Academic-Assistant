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

"""
Module: Update Note Chain

This module provides a chain for handling user requests to update notes. It processes 
user input to extract the note ID and new content, ensuring a structured format for 
further processing.

Classes:
    - UpdateNoteInformation: Schema for note update requests.
    - UpdateNoteChain: Processes user input to extract note ID and new content.

Usage:
    Use `UpdateNoteChain` to extract and validate note update requests from user input.
"""

import os
from dotenv import load_dotenv
import sqlite3
from pydantic import BaseModel, ValidationError
from langchain.schema.runnable.base import Runnable
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates
from Sophia_Labs.data.loader import get_database_path

# Load environment variables
load_dotenv()

# Database path and API key initialization
db_path = get_database_path()
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)


class UpdateNoteInformation(BaseModel):
    """
    Represents the input schema for note updates.

    Attributes:
        note_id (int): The ID of the note to be updated.
        new_content (str): The new content to update the note with.
    """
    note_id: int
    new_content: str


class UpdateNoteChain(Runnable):
    """
    Handles reasoning and processing for updating notes based on user input.

    Attributes:
        llm: The language model for processing input.
        prompt: Chat prompt template for generating reasoning outputs.
        output_parser: Parses the output into an UpdateNoteInformation object.
        chain: Composed chain to handle prompt generation, processing, and parsing.
    """

    def __init__(self, llm, memory=True):
        """
        Initializes the UpdateNoteChain with a language model and optional memory.

        Args:
            llm: An instance of the language model.
            memory (bool): Whether to include chat history in the reasoning process.
        """
        super().__init__()
        self.llm = llm

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a chatbot designed to help students update their notes.
            Your task is to identify the note_id and the new content from the user's input.

            User inputs can vary, such as:
            - Update note with ID 3 with the content I will study math on Wednesday
            - Change my third note to say Meeting postponed to Friday
            - Edit note 3 to: Homework due next Monday

            **Output Format:** Return the following JSON structure:
            {{
                "note_id": <note_id>,
                "new_content": "<new_content>"
            }}

            User input: {user_input}
            """,
            human_template="User Input: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=False)
        self.output_parser = PydanticOutputParser(
            pydantic_object=UpdateNoteInformation
        )
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, user_input: str) -> UpdateNoteInformation:
        """
        Processes the user input to extract the note ID and new content.

        Args:
            user_input (str): The user's input containing the note ID and new content.

        Returns:
            UpdateNoteInformation: Parsed information as an UpdateNoteInformation object.

        Raises:
            ValueError: If the input format is invalid or parsing fails.
        """
        try:
            return self.chain.invoke({"user_input": user_input})
        except ValidationError as e:
            raise ValueError(f"Invalid input format: {e}")