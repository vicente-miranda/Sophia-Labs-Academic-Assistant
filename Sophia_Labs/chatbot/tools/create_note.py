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
Module: Create Note Tool

This module provides a tool to create notes in the student notes database. It uses a 
language model to process user input, extracts note content, and stores it in the 
database.

Classes:
    - CreateNoteInput: Pydantic model for validating note creation input.
    - CreateNoteTool: Tool to create a new note in the database.

Usage:
    Instantiate `CreateNoteTool` and call its `_run` method to create a note.
"""

import sqlite3
from typing import Type

from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from Sophia_Labs.chatbot.chains.create_note import CreateNoteChain
from Sophia_Labs.data.loader import get_database_path 

class CreateNoteInput(BaseModel):
    """
    Model for validating input for note creation.

    Attributes:
        user_id (int): The ID of the student creating the note.
        user_input (str): The user's input containing the note content.
    """
    user_id: int
    user_input: str

class CreateNoteTool(BaseTool):
    """
    Tool for creating a new note in the student notes database.

    Attributes:
        name (str): The name of the tool.
        description (str): Description of the tool's functionality.
        args_schema (Type[BaseModel]): Schema for validating input arguments.
        return_direct (bool): Whether the tool returns its response directly.
    """
    name: str = "CreateNoteTool" 
    description: str = "Create a new note in the student notes database"
    args_schema: Type[BaseModel] = CreateNoteInput
    return_direct: bool = True

    def _run(self, user_id: int, user_input: str) -> str:
        """
        Executes the note creation tool, extracting content and saving to the database.

        Args:
            user_id (int): The ID of the student creating the note.
            user_input (str): The user's input containing the note content.

        Returns:
            str: Confirmation message or error description.
        """
        llm = ChatOpenAI(model="gpt-4o-mini")
        db_path = get_database_path()  

        note_info = CreateNoteChain(llm, db_path).invoke({"user_input": user_input})

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO Personal_Notes (user_id, note) VALUES (?, ?)
                """,
                (user_id, note_info.content),
            )
            connection.commit()

            note_id = cursor.lastrowid
        except sqlite3.OperationalError as e:
            print(f"Error: {e}")
            return "An error occurred while creating the note."
        finally:
            cursor.close()
            connection.close()

        return f"Note created with ID: {note_id}, and content: {note_info.content}"