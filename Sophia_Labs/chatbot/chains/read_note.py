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
Module: Read Notes Chain

This module provides functionality for retrieving and formatting user notes. It interacts 
with the database to fetch notes associated with a specific user and formats them into 
a user-friendly response.

Classes:
    - NoteRecord: A Pydantic model representing a single note record.
    - ReadNoteResponseChain: Formats notes into a user-friendly response.
    - ReadNoteChain: Fetches notes from the database and uses `ReadNoteResponseChain` 
      to generate a formatted response.

Usage:
    Use `ReadNoteChain` to retrieve and format user notes. If no notes exist, it provides 
    a helpful prompt for creating new notes.
"""

import sqlite3
from typing import List
from pydantic import BaseModel


class NoteRecord(BaseModel):
    """
    Represents a single note record.

    Attributes:
        id (int): The ID of the note.
        content (str): The content of the note.
    """
    id: int
    content: str


class ReadNoteResponseChain:
    """
    Formats notes into a user-friendly response for display.

    Attributes:
        response_template (str): Template for formatting notes when they exist.
        empty_response (str): Message to display when no notes are found.
    """

    def __init__(self):
        """
        Initialize the response chain for formatting notes.
        """
        self.response_template = (
            "Here are your notes:\n"
            "{notes}\n"
            "Let me know if there's anything else I can help with!"
        )
        self.empty_response = (
            "It seems you don’t have any notes yet. You can create one by saying "
            "'Add a new note' or a similar command."
        )

    def format_notes(self, notes: List[NoteRecord]) -> str:
        """
        Format the notes into a user-friendly response.

        Args:
            notes (List[NoteRecord]): A list of note objects.

        Returns:
            str: Formatted response string.
        """
        if not notes:
            return self.empty_response

        formatted_notes = "\n".join(
            [f"- Note ID {note.id}: {note.content}" for note in notes]
        )
        return self.response_template.format(notes=formatted_notes)


class ReadNoteChain:
    """
    Fetches notes from the database for a specific user and formats them into a response.

    Attributes:
        db_path (str): Path to the SQLite database.
        response_chain (ReadNoteResponseChain): Responsible for formatting the notes.
    """

    def __init__(self, db_path: str):
        """
        Initializes the ReadNoteChain with a database path.

        Args:
            db_path (str): Path to the SQLite database.
        """
        self.db_path = db_path
        self.response_chain = ReadNoteResponseChain()

    def invoke(self, user_id: int) -> str:
        """
        Fetch notes for a specific student from the database and format the response.

        Args:
            user_id (int): The ID of the student whose notes need to be retrieved.

        Returns:
            str: Formatted response containing the notes or a message if no notes exist.

        Raises:
            ValueError: If there is an operational error with the database.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT note_id, note
                FROM Personal_Notes
                WHERE user_id = ?
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            raise ValueError(f"Database error: {e}")
        finally:
            cursor.close()
            connection.close()

        notes = [NoteRecord(id=row[0], content=row[1]) for row in rows]
        return self.response_chain.format_notes(notes)