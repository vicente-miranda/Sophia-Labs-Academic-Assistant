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
Module: Note Creation Chain

This module defines a chain for creating notes based on user input. The chain processes 
the input to extract the note content and stores it in a structured format.

Classes:
    - NoteInformation: Pydantic model for representing note content.
    - CreateNoteChain: Chain for extracting and processing note content from user input.

Usage:
    Use `CreateNoteChain` to parse user inputs for creating notes. The chain ensures the 
    output is structured and validated.
"""

import ast
import re

from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable.base import Runnable
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, ValidationError, Field

from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates
from Sophia_Labs.data.loader import get_database_path


class NoteInformation(BaseModel):
    """
    Represents the content of a note.

    Attributes:
        content (str): The content of the note extracted from the user input.
    """
    content: str


class CreateNoteChain(Runnable):
    """
    A chain for extracting and creating notes based on user input.

    Attributes:
        llm: The language model for processing input.
        db: SQLDatabase instance for database interactions.
        prompt: Chat prompt template for generating outputs.
        output_parser: Parses the output into a structured NoteInformation object.
    """

    def __init__(self, llm, memory=True):
        """
        Initializes the CreateNoteChain with a language model and database connection.

        Args:
            llm: An instance of the language model.
            memory (bool): Whether to include chat history in the prompt generation.
        """
        super().__init__()
        self.llm = llm
        self.db = SQLDatabase.from_uri(f"sqlite:///{get_database_path()}")

        prompt_template = PromptTemplate(
            system_template=""" 
            You are a chatbot designed to help students create new notes.
            Your task is to identify the content for the new note from the user input.

            User inputs can vary, such as:
            - Add a new note saying ...
            - Create a note with the content ...
            - Write a new note with ...

            **Output Format:** Return the following JSON structure:
            {{
                "content": "<content>"
            }}

            User input: {user_input}
            """,
            human_template="User Input: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=False)
        self.output_parser = PydanticOutputParser(pydantic_object=NoteInformation)
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, user_input: str) -> NoteInformation:
        """
        Execute the chain to extract the note content from the user input.

        Args:
            user_input (str): The user's input containing the note content.

        Returns:
            NoteInformation: Parsed content as a NoteInformation object.
        
        Raises:
            ValueError: If the input format is invalid or parsing fails.
        """
        try:
            return self.chain.invoke({"user_input": user_input})
        except ValidationError as e:
            raise ValueError(f"Invalid input format: {e}")