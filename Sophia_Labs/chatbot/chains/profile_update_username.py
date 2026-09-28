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
Module: Update Username Chain

This module provides functionality for handling username update requests. It extracts 
and validates new usernames provided by the user and ensures they meet defined 
requirements.

Classes:
    - UpdateUsernameInput: Pydantic model for representing the new username.
    - UpdateUsernameReasoningChain: Processes user input to extract and validate new usernames.

Usage:
    Use `UpdateUsernameReasoningChain` to validate and extract new usernames from user input.
"""

import sqlite3
from pydantic import BaseModel, ValidationError
from langchain.schema.runnable.base import Runnable
from langchain.output_parsers import PydanticOutputParser
from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates


class UpdateUsernameInput(BaseModel):
    """
    Represents the input schema for username updates.

    Attributes:
        new_username (str): The new username extracted and validated from user input.
    """
    new_username: str


class UpdateUsernameReasoningChain(Runnable):
    """
    Handles reasoning and validation for updating usernames based on user input.

    Attributes:
        llm: The language model for processing input.
        db_path (str): Path to the SQLite database.
        prompt: Chat prompt template for generating reasoning outputs.
        output_parser: Parses the output into an UpdateUsernameInput object.
    """

    def __init__(self, llm, db_path, memory=False):
        """
        Initializes the UpdateUsernameReasoningChain with a language model and database path.

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
            You are a chatbot designed to assist students in validating their new username.

            **Guidelines:**

            1. Extract the new username from the user input.

            2. Validate the new username:
               - Ensure it is between 5 and 20 characters.
               - Ensure it only contains alphanumeric characters or underscores.

            3. If invalid, return an error message explaining why it is invalid.

            4. If valid use the new username you extracted from the user input to return
            with a JSON format:
            - Include only the new username in the JSON format, do not provide any
            additional keys.
            - Pass the extracted new username as the value for the key "new_username".

            User input: {user_input}
            """,
            human_template="User Input: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = PydanticOutputParser(
            pydantic_object=UpdateUsernameInput
        )

        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, inputs, config=None, **kwargs):
        """
        Processes the user input to extract and validate the new username.

        Args:
            inputs (dict): Input containing the user's username update request.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            dict: Contains the extracted new username or an error message if validation fails.
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