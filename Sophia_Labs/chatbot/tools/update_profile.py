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
Module: Profile Update Tools

This module provides tools to update user profile information in the database. It includes 
tools for updating both the username and password. These tools validate the user input 
before updating the database.

Classes:
    - UpdateUsernameInput: Pydantic model for validating input for updating username.
    - UpdateUsernameTool: Tool for updating the username of a user.
    - UpdatePasswordInput: Pydantic model for validating input for updating password.
    - UpdatePasswordTool: Tool for updating the password of a user.

Usage:
    Instantiate the respective tool and call its `_run` method to update the profile information.
"""

from pydantic import BaseModel
from typing import Type
import sqlite3

from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool

from Sophia_Labs.data.loader import get_database_path
from Sophia_Labs.chatbot.chains.profile_update_password import *
from Sophia_Labs.chatbot.chains.profile_update_username import *  

class UpdateUsernameInput(BaseModel):
    """
    Model for validating input for updating a username.

    Attributes:
        user_id (int): The ID of the user.
        user_input (str): The user's input specifying the new username.
    """
    user_id: int
    user_input: str

class UpdateUsernameTool(BaseTool):
    """
    Tool for updating the username of a user in the database.

    Attributes:
        name (str): The name of the tool.
        description (str): Description of the tool's functionality.
        args_schema (Type[BaseModel]): Schema for validating input arguments.
        return_direct (bool): Whether the tool returns its response directly.
    """
    name: str = "UpdateUsernameTool"
    description: str = "Update the user's username in the database."
    args_schema: Type[BaseModel] = UpdateUsernameInput
    return_direct: bool = True

    def _run(self, user_id: int, user_input: str) -> str:
        """
        Executes the username update tool by validating and updating the username in the database.

        Args:
            user_id (int): The ID of the user.
            user_input (str): The user's input specifying the new username.

        Returns:
            str: Confirmation message or error description.
        """
        llm = ChatOpenAI(model="gpt-4o-mini")
        db_path = get_database_path()

        reasoning_result = UpdateUsernameReasoningChain(llm, db_path).invoke({
            "user_input": user_input
        })

        if "error" in reasoning_result:
            return f"Failed to update username: {reasoning_result['error']}"

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        validated_username = reasoning_result.new_username

        try:
            cursor.execute(
                "UPDATE Users SET username = ? WHERE user_id = ?",
                (validated_username, user_id)
            )
            connection.commit()

            cursor.execute(
                "SELECT username FROM Users WHERE user_id = ?",
                (user_id,)
            )
            updated_username = cursor.fetchone()[0]

        except sqlite3.OperationalError as e:
            print(f"Error: {e}")
            return "An error occurred while updating the username."
        
        finally:
            cursor.close()
            connection.close()

        return f"Username updated successfully to '{updated_username}' for user ID {user_id}."

class UpdatePasswordInput(BaseModel):
    """
    Model for validating input for updating a password.

    Attributes:
        user_id (int): The ID of the user.
        user_input (str): The user's input specifying the new password.
    """
    user_id: int
    user_input: str

class UpdatePasswordTool(BaseTool):
    """
    Tool for updating the password of a user in the database.

    Attributes:
        name (str): The name of the tool.
        description (str): Description of the tool's functionality.
        args_schema (Type[BaseModel]): Schema for validating input arguments.
        return_direct (bool): Whether the tool returns its response directly.
    """
    name: str = "UpdatePasswordTool"
    description: str = "Update the user's password in the database."
    args_schema: Type[BaseModel] = UpdatePasswordInput
    return_direct: bool = True

    def _run(self, user_id: int, user_input: str) -> str:
        """
        Executes the password update tool by validating and updating the password in the database.

        Args:
            user_id (int): The ID of the user.
            user_input (str): The user's input specifying the new password.

        Returns:
            str: Confirmation message or error description.
        """
        llm = ChatOpenAI(model="gpt-4o-mini")
        db_path = get_database_path()

        reasoning_result = UpdatePasswordReasoningChain(llm, db_path).invoke({
            "user_input": user_input
        })

        if "error" in reasoning_result:
            return f"Failed to update password: {reasoning_result['error']}"

        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        validated_password = reasoning_result.new_password

        try:
            cursor.execute(
                "UPDATE Users SET password = ? WHERE user_id = ?",
                (validated_password, user_id)
            )
            connection.commit()

            cursor.execute(
                "SELECT password FROM Users WHERE user_id = ?",
                (user_id,)
            )
            updated_password = cursor.fetchone()[0]

        except sqlite3.OperationalError as e:
            print(f"Error: {e}")
            return "An error occurred while updating the password."
        finally:
            cursor.close()
            connection.close()

        return f"Password updated successfully for user ID {user_id}."