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
Module: Update Password Chain

This module provides functionality for handling password update requests. It extracts 
and validates new passwords provided by the user and ensures they meet defined 
requirements.

Classes:
    - UpdatePasswordInput: Pydantic model for representing the new password.
    - UpdatePasswordReasoningChain: Processes user input to extract and validate new passwords.

Usage:
    Use `UpdatePasswordReasoningChain` to validate and extract new passwords from user input.
"""

import sqlite3
from pydantic import BaseModel, ValidationError
from langchain.schema.runnable.base import Runnable
from langchain.output_parsers import PydanticOutputParser
from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates


class UpdatePasswordInput(BaseModel):
    """
    Represents the input schema for password updates.

    Attributes:
        new_password (str): The new password extracted and validated from user input.
    """
    new_password: str


class UpdatePasswordReasoningChain(Runnable):
    """
    Handles reasoning and validation for updating passwords based on user input.

    Attributes:
        llm: The language model for processing input.
        db_path (str): Path to the SQLite database.
        prompt: Chat prompt template for generating reasoning outputs.
        output_parser: Parses the output into an UpdatePasswordInput object.
    """

    def __init__(self, llm, db_path, memory=False):
        """
        Initializes the UpdatePasswordReasoningChain with a language model and database path.

        Args:
            llm: An instance of the language model.
            db_path (str): Path to the SQLite database.
            memory (bool): Whether to include chat history in the reasoning process.
        """
        super().__init__()

        self.llm = llm
        self.db_path = db_path

        prompt_template = PromptTemplate(
            system_template="""
            You are a chatbot designed to assist students in validating their new password.

            **Guidelines:**

            1. Extract the new password from the user input.

            2. Validate it by confirming it has between 8 and 64 characters.

            3. If invalid, return an error message explaining why it is invalid.

            4. If valid, use the new password you extracted from the user input to return
            with a JSON format:
            - Include only the new password in the JSON format, do not provide any
            additional keys.
            - Pass the extracted new password as the value for the key "new_password".

            **Output Format:** Return the following JSON structure:
            {{
                "new_password": "<new_password>"
            }}

            User input: {user_input}
            """,
            human_template="User Input: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = PydanticOutputParser(
            pydantic_object=UpdatePasswordInput
        )

        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, inputs, config=None, **kwargs):
        """
        Processes the user input to extract and validate the new password.

        Args:
            inputs (dict): Input containing the user's password update request.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            dict: Contains the extracted new password or an error message if validation fails.
        """
        try:
            print("PromptTemplate Expected Variables:", self.prompt.input_variables)
            print("Input Variables:", inputs)
            result = self.chain.invoke(
                {
                    "user_input": inputs["user_input"]
                },
                config=config,
            )
            return result
        except ValidationError as e:
            return {"error": f"Validation error: {e}"}
        except Exception as e:
            return {"error": f"An error occurred: {e}"}