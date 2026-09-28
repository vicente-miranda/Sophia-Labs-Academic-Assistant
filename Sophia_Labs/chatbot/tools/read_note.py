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
Module: Read Note Tool

This module provides a tool for retrieving all notes associated with a specific student 
from the database. It uses the ReadNoteChain to fetch and format the notes for presentation.

Classes:
    - ReadNoteInput: Pydantic model for validating input for reading notes.
    - ReadNoteTool: Tool for retrieving and formatting student notes.

Usage:
    Instantiate `ReadNoteTool` and call its `_run` method to retrieve notes for a student.
"""

from typing import Type, List
from langchain.tools import BaseTool
from pydantic import BaseModel

from Sophia_Labs.data.loader import get_database_path
from Sophia_Labs.chatbot.chains.read_note import ReadNoteChain


class ReadNoteInput(BaseModel):
    """
    Model for validating input for reading notes.

    Attributes:
        user_id (int): The ID of the student whose notes need to be retrieved.
    """
    user_id: int

class ReadNoteTool(BaseTool):
    """
    Tool for retrieving all notes for a specific student from the database.

    Attributes:
        name (str): The name of the tool.
        description (str): Description of the tool's functionality.
        args_schema (Type[BaseModel]): Schema for validating input arguments.
        return_direct (bool): Whether the tool returns its response directly.
    """
    name: str = "ReadNoteTool"
    description: str = "Retrieve all notes for a specific student from the database."
    args_schema: Type[BaseModel] = ReadNoteInput
    return_direct: bool = True

    def _run(self, user_id: int) -> str:
        """
        Executes the read notes tool, fetching and formatting notes from the database.

        Args:
            user_id (int): The ID of the student whose notes need to be retrieved.

        Returns:
            str: A formatted string representing the student's notes or an appropriate message.
        """
        db_path = get_database_path()
        note_chain = ReadNoteChain(db_path)  
        formatted_response = note_chain.invoke(user_id)

        return formatted_response