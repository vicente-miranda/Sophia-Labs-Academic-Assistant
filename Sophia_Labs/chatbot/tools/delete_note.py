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
Module: Delete Note Tool

This module provides a tool for deleting notes from the student notes database. It uses 
a language model to process user input, extracts the note ID, and deletes the note from 
the database.

Classes:
    - DeleteNoteInput: Pydantic model for validating input for deleting a note.
    - DeleteNoteTool: Tool for deleting a note from the database using its ID.

Usage:
    Instantiate `DeleteNoteTool` and call its `_run` method to delete a note by its ID.
"""

import sqlite3
from pydantic import BaseModel
from typing import Type
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

from Sophia_Labs.data.loader import get_database_path
from Sophia_Labs.chatbot.chains.delete_note import DeleteNoteByIDChain

class DeleteNoteInput(BaseModel):
    """
    Model for validating input for note deletion.

    Attributes:
        user_id (int): The ID of the student.
        user_input (str): The user's input specifying the note to delete.
    """
    user_id: int
    user_input: str

class DeleteNoteTool(BaseTool):
    """
    Tool for deleting a note from the student notes database using its ID.

    Attributes:
        name (str): The name of the tool.
        description (str): Description of the tool's functionality.
        args_schema (Type[BaseModel]): Schema for validating input arguments.
        return_direct (bool): Whether the tool returns its response directly.
    """
    name: str = "DeleteNoteTool"
    description: str = "Delete a note from the student notes database using its ID."
    args_schema: Type[BaseModel] = DeleteNoteInput
    return_direct: bool = True

    def _run(self, user_id: int, user_input: str) -> str:
        """
        Executes the note deletion tool by extracting the note ID and deleting it from the database.

        Args:
            user_id (int): The ID of the student.
            user_input (str): The user's input specifying the note to delete.

        Returns:
            str: Confirmation message or error description.
        """
        llm = ChatOpenAI(model="gpt-4o-mini")
        db_path = get_database_path()
        note_info = DeleteNoteByIDChain(llm).invoke(user_input)

        note_id = note_info.note_id

        connection = sqlite3.connect(db_path)

        cursor = connection.cursor()

        try:
            # Retrieve the note content before deletion
            cursor.execute(
                """
                SELECT note FROM Personal_Notes WHERE user_id = ? AND note_id = ?
                """,
                (user_id, note_id),
            )
            note = cursor.fetchone()

            if not note:
                return f"No note found with ID {note_id} for the specified user."

            # Delete the note
            cursor.execute(
                """
                DELETE FROM Personal_Notes WHERE user_id = ? AND note_id = ?
                """,
                (user_id, note_id),
            )
            connection.commit()

        except sqlite3.OperationalError as e:
            return f"An error occurred while deleting the note: {e}"
        finally:
            cursor.close()
            connection.close()

        return f"Successfully deleted note with ID {note_id} and content: '{note[0]}'."