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
Module: Update Note Tool

This module provides a tool for updating the content of existing notes in the student 
notes database. It extracts the note ID and new content from the user's input and 
updates the note in the database.

Classes:
    - UpdateNoteInput: Pydantic model for validating input for updating a note.
    - UpdateNoteTool: Tool for updating the content of an existing note.

Usage:
    Instantiate `UpdateNoteTool` and call its `_run` method to update a note's content.
"""

import sqlite3
from pydantic import BaseModel, ValidationError
from typing import Type
from langchain.tools.base import BaseTool
from langchain.schema.runnable.base import Runnable
from langchain.output_parsers import PydanticOutputParser
from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

from Sophia_Labs.data.loader import get_database_path
from Sophia_Labs.chatbot.chains.update_note import UpdateNoteChain

# Load environment variables
load_dotenv()
db_path = get_database_path()
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)

class UpdateNoteInput(BaseModel):
    """
    Model for validating input for updating a note.

    Attributes:
        user_id (int): The ID of the student.
        user_input (str): The user's input specifying the note to update and its new content.
    """
    user_id: int
    user_input: str

class UpdateNoteTool(BaseTool):
    """
    Tool for updating the content of an existing note in the student notes database.

    Attributes:
        name (str): The name of the tool.
        description (str): Description of the tool's functionality.
        args_schema (Type[BaseModel]): Schema for validating input arguments.
        return_direct (bool): Whether the tool returns its response directly.
    """
    name: str = "UpdateNoteTool"
    description: str = "Update the content of an existing note in the student notes database."
    args_schema: Type[BaseModel] = UpdateNoteInput
    return_direct: bool = True

    def _run(self, user_id: int, user_input: str) -> str:
        """
        Executes the note update tool by extracting note ID and new content, then updating the database.

        Args:
            user_id (int): The ID of the student.
            user_input (str): The user's input specifying the note to update and its new content.

        Returns:
            str: Confirmation message or error description.
        """
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
        db_path = get_database_path()

        # Extract note_id and new_content using UpdateNoteChain
        update_info = UpdateNoteChain(llm).invoke(user_input)
        note_id = update_info.note_id
        new_content = update_info.new_content

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        try:
            # Check if the note exists
            cursor.execute(
                """
                SELECT note FROM Personal_Notes WHERE user_id = ? AND note_id = ?
                """,
                (user_id, note_id),
            )
            note = cursor.fetchone()

            if not note:
                return f"No note found with ID {note_id} for the specified user."

            # Update the note content
            cursor.execute(
                """
                UPDATE Personal_Notes SET note = ? WHERE user_id = ? AND note_id = ?
                """,
                (new_content, user_id, note_id),
            )
            connection.commit()

        except sqlite3.OperationalError as e:
            return f"An error occurred while updating the note: {e}"

        finally:
            cursor.close()
            connection.close()

        return f"Successfully updated note with ID {note_id}. New content: '{new_content}'."