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
Module: Teaching Staff Chains

This module provides reasoning and response chains for retrieving and formatting teaching 
staff contact information. It processes user queries, validates inputs, queries the 
database, and generates user-friendly responses.

Classes:
    - TeachingStaffQueryInput: Schema for teaching staff queries.
    - TeachingStaffReasoningChain: Processes user input to retrieve teaching staff details.
    - TeachingStaffResponseChain: Formats teaching staff data into a user-friendly response.

Usage:
    Use `TeachingStaffReasoningChain` to query teaching staff details from the database 
    and `TeachingStaffResponseChain` to generate a formatted response for the user.
"""

import sqlite3
from pydantic import BaseModel, ValidationError, Field
from langchain.schema.runnable.base import Runnable
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates
from Sophia_Labs.data.loader import get_database_path


def get_default_academic_year():
    """
    Returns the default academic year.

    Returns:
        str: The default academic year (e.g., "2024/2025").
    """
    return "2024/2025"


class TeachingStaffQueryInput(BaseModel):
    """
    Represents the input schema for teaching staff queries.

    Attributes:
        subject (str): The name of the subject for which teaching staff details are requested.
        academic_year (str): The academic year for the subject (default is "2024/2025").
        chat_history (str): The chat history of the conversation.
    """
    subject: str = Field(
        description="The name of the subject for which teaching staff details are requested."
    )
    academic_year: str = Field(
        default_factory=get_default_academic_year,
        description="The academic year for the subject (e.g., 2024/2025).",
    )
    chat_history: str = Field(
        description="The chat history of the conversation."
    )


class TeachingStaffReasoningChain(Runnable):
    """
    Handles reasoning for retrieving teaching staff contact details based on user input.

    Attributes:
        llm: The language model for processing input.
        db_path (str): Path to the SQLite database.
        prompt: Chat prompt template for generating reasoning outputs.
        output_parser: Parses the output into a TeachingStaffQueryInput object.
        chain: A composed chain for reasoning and data extraction.
    """

    def __init__(self, llm, memory=False):
        """
        Initializes the TeachingStaffReasoningChain with a language model and optional memory.

        Args:
            llm: An instance of the language model.
            memory (bool): Whether to include chat history in the reasoning process.
        """
        super().__init__()
        self.llm = llm
        self.db_path = get_database_path()

        prompt_template = PromptTemplate(
            system_template="""
            You are a chatbot designed to help students retrieve the contact information
            of teaching staff associated with a specific subject.

            **Guidelines:**

            1. Understand user query to identify the subject.
            2. If provided, capture the academic year details.
            3. Query database to fetch teaching staff details.
            4. Handle errors and provide clear feedback.

            **Output Format:** Return the following JSON structure:
            {{
                "subject": "<subject>",
                "academic_year": "<academic_year>",
                "chat_history": "<chat_history>"
            }}
            """,
            human_template="User Input: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory)
        self.output_parser = PydanticOutputParser(
            pydantic_object=TeachingStaffQueryInput
        )
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, input, config=None, **kwargs):
        """
        Processes user input to retrieve teaching staff details.

        Args:
            input (dict): Contains user input and chat history.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            dict: A response containing teaching staff details or an error message.
        """
        try:
            result = self.chain.invoke(
                {
                    "user_input": input["user_input"],
                    "chat_history": input["chat_history"],
                },
                config=config,
            )

            academic_year = result.academic_year or get_default_academic_year()
            staff_info = self.query_teaching_staff(
                subject=result.subject, academic_year=academic_year
            )

            if not staff_info:
                return {
                    "status": "failure",
                    "message": f"No teaching staff found for subject '{result.subject}' "
                               f"in the academic year {academic_year}. Please verify the "
                               f"details and try again.",
                }

            return {
                "status": "success",
                "validated_input": result,
                "staff_info": staff_info,
            }
        except (ValidationError, ValueError) as e:
            return {
                "status": "failure",
                "message": str(e),
            }

    def query_teaching_staff(self, subject, academic_year=None):
        """
        Queries the database for teaching staff details for a specific subject and academic year.

        Args:
            subject (str): The name of the subject.
            academic_year (str): The academic year.

        Returns:
            list: A list of teaching staff records with names and emails, or an empty list if no data is found.
        """
        academic_year = academic_year or get_default_academic_year()
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            cursor.execute(
                "SELECT subject_id FROM Subjects WHERE LOWER(subject_name) = LOWER(?)",
                (subject,),
            )
            subject_row = cursor.fetchone()
            if not subject_row:
                return []

            subject_id = subject_row[0]

            query = "SELECT staff_id FROM Subject_Staff_AcademicTerm WHERE subject_id = " \
                    "? AND academic_year = ?"
            cursor.execute(query, [subject_id, academic_year])
            staff_ids = [row[0] for row in cursor.fetchall()]

            if not staff_ids:
                return []

            cursor.execute(
                f"SELECT name, email FROM Teaching_Staff WHERE staff_id IN "
                f"({','.join(['?'] * len(staff_ids))})",
                staff_ids,
            )
            staff_records = cursor.fetchall()
            connection.close()

            return [
                {"name": record[0], "email": record[1]} for record in staff_records
            ]
        except Exception:
            return []


class TeachingStaffResponseChain(Runnable):
    """
    Handles the generation of user-friendly responses for teaching staff details.

    Attributes:
        llm: The language model for processing input.
        prompt: Chat prompt template for generating responses.
        output_parser: Parses the output into a string format.
        chain: A composed chain for response generation.
    """

    def __init__(self, llm, memory=False):
        """
        Initializes the TeachingStaffResponseChain with a language model and optional memory.

        Args:
            llm: An instance of the language model.
            memory (bool): Whether to include chat history in the response generation.
        """
        super().__init__()
        self.llm = llm
        prompt_template = PromptTemplate(
            system_template="""
            You are a chatbot that generates a user-friendly response summarizing the 
            contact information of teaching staff for a specific subject.

            **Guidelines:**

            1. **Summarize Staff Information:**
            - Provide the names and emails of teaching staff in a clear and concise format.

            2. **Handle Missing Data:**
            - If no staff information is available, politely inform the user.

            3. **User-Friendly Output:**
            - Ensure the response is easy to read and encourages further interaction if 
            needed.

            Here is the user input:
            {user_input}

            Here is the retrieved teaching staff data:
            {staff_info}

            Generate a friendly and accurate response.
            """,
            human_template="User Input: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory)
        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, input, config=None, **kwargs):
        """
        Generates a response summarizing teaching staff contact information.

        Args:
            input (dict): Contains user input, teaching staff data, and chat history.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            str: A user-friendly response summarizing the teaching staff data.
        """
        return self.chain.invoke(
            {
                "user_input": input.get("user_input", ""),
                "staff_info": input.get("staff_info", []),
                "chat_history": input["chat_history"],
            },
            config=config,
        )