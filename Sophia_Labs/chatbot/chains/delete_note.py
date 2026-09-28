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
Module: Note Deletion Chain

This module provides a chain for deleting notes by extracting the note ID from user 
input. It ensures the note ID is correctly parsed and validated before deletion.

Classes:
    - NoteIDInformation: Pydantic model for representing the note ID.
    - DeleteNoteByIDChain: Chain for identifying and processing note IDs for deletion.

Usage:
    Use `DeleteNoteByIDChain` to parse user inputs for deleting notes by ID. The chain 
    ensures the output is structured and validated.
"""

import sqlite3
from typing import Optional
from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable.base import Runnable
from langchain_community.utilities.sql_database import SQLDatabase
from pydantic import BaseModel, ValidationError
from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates


class NoteIDInformation(BaseModel):
    """
    Represents the ID of a note to be deleted.

    Attributes:
        note_id (int): The ID of the note to be deleted.
    """
    note_id: int


class DeleteNoteByIDChain(Runnable):
    """
    A chain for identifying and deleting notes by ID based on user input.

    Attributes:
        llm: The language model for processing input.
        prompt: Chat prompt template for generating outputs.
        output_parser: Parses the output into a structured NoteIDInformation object.
    """

    def __init__(self, llm, memory=True):
        """
        Initializes the DeleteNoteByIDChain with a language model and optional memory.

        Args:
            llm: An instance of the language model.
            memory (bool): Whether to include chat history in the prompt generation.
        """
        super().__init__()
        self.llm = llm

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a chatbot designed to help students delete their notes.
            Your task is to identify the note_id from the user input.

            User inputs can vary, such as:
            - Delete note with ID 3
            - Remove note number 3
            - Remove the note with ID 3

            **Output Format:** Return the following JSON structure:
            {{
                "note_id": {{note_id}}
            }}

            User input: {user_input}
            """,
            human_template="User Input: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=False)
        self.output_parser = PydanticOutputParser(pydantic_object=NoteIDInformation)
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, user_input: str) -> NoteIDInformation:
        """
        Execute the chain to extract the note ID from the user input.

        Args:
            user_input (str): The user's input containing the note ID.

        Returns:
            NoteIDInformation: Parsed note ID as a NoteIDInformation object.

        Raises:
            ValueError: If the input format is invalid or the note ID could not be extracted.
        """
        try:
            raw_output = self.chain.invoke({"user_input": user_input})
            if raw_output.note_id is None:
                raise ValueError("Note ID could not be extracted. Please try again.")
            return raw_output

        except ValidationError as e:
            raise ValueError(f"Invalid input format: {e}")