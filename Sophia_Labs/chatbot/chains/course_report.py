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
Module: Course Report Chains

This module provides reasoning and response chains for generating a course report. It 
handles user queries to retrieve and summarize the subjects a student is enrolled in 
for a specific academic year and semester.

Classes:
    - TimeScopeHandler: Utility class for calculating academic year and semester adjustments.
    - CourseReportQueryInput: Pydantic model for parsing course report query inputs.
    - CourseReportReasoningChain: Processes user queries to determine the time scope and 
      retrieve enrolled subjects.
    - CourseReportResponseChain: Generates a user-friendly response summarizing course 
      information.

Usage:
    Use `CourseReportReasoningChain` to retrieve structured course information based on 
    user input. Use `CourseReportResponseChain` to generate a summarized response for 
    end-users.
"""

import sqlite3
from pydantic import BaseModel, ValidationError, Field
from langchain.schema.runnable.base import Runnable
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates

from Sophia_Labs.data.loader import get_database_path


class TimeScopeHandler:
    """
    Handles time scope logic for determining academic year and semester based on input.
    """

    @staticmethod
    def calculate_target_year_and_semester(current_year, current_semester, time_scope):
        """
        Calculate the target academic year and semester based on the current academic
        year/semester and the time scope.

        Args:
            current_year (str): The current academic year, e.g., "2024/2025".
            current_semester (str): The current semester, e.g., "Fall" or "Spring".
            time_scope (str): The desired time scope: "current", "previous", or "future".

        Returns:
            tuple: (target_year, target_semester) representing the adjusted academic
            year and semester.
        """
        start_year, end_year = map(int, current_year.split("/"))

        if time_scope == "current":
            return current_year, current_semester

        if time_scope == "previous":
            if current_semester.lower() == "fall":
                return f"{start_year - 1}/{end_year - 1}", "Spring"
            else:
                return f"{start_year}/{end_year}", "Fall"

        if time_scope == "future":
            if current_semester.lower() == "spring":
                return f"{start_year + 1}/{end_year + 1}", "Fall"
            else:
                return f"{start_year}/{end_year}", "Spring"

        raise ValueError(f"Invalid time scope: {time_scope}")


class CourseReportQueryInput(BaseModel):
    """
    Defines the structure for course report query inputs.

    Attributes:
        time_scope (str): Indicates the desired time scope ("previous", "current", or "future").
    """
    time_scope: str = Field(
        ..., description="Either 'previous', 'current', or 'future' to indicate the desired time scope."
    )


class CourseReportReasoningChain(Runnable):
    """
    Handles user queries for retrieving course reports based on academic year and semester.

    Attributes:
        llm: The language model for processing input.
        db_path (str): Path to the SQLite database.
        user_id (int): ID of the user interacting with the chain.
        prompt: Chat prompt template for generating reasoning outputs.
        output_parser: Parses the output into a structured format.
    """

    def __init__(self, llm, user_id: int, memory=False):
        """
        Initializes the reasoning chain with a language model, user ID, and optional memory.

        Args:
            llm: An instance of the language model.
            user_id (int): The ID of the user interacting with the chain.
            memory (bool): Whether to include chat history in the reasoning process.
        """
        super().__init__()
        self.llm = llm
        self.db_path = get_database_path()
        self.user_id = user_id

        prompt_template = PromptTemplate(
            system_template="""
            You are a chatbot designed to help students retrieve a list of the subjects
            they are enrolled in for a certain year/semester.

            **Instructions:**
            1. Check if the user wants the "previous", "current", or "future" year/semester.
            2. Return that strictly in JSON format:
               {{
                 "time_scope": "previous" | "current" | "future"
               }}
            """,
            human_template="User Query: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = PydanticOutputParser(pydantic_object=CourseReportQueryInput)
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, input, config=None, **kwargs):
        """
        Processes user input and retrieves enrolled subject data.

        Args:
            input (dict): Input containing "user_input" and "chat_history".
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            dict: A response containing the retrieved subjects or an error message.
        """
        try:
            parsed_result = self.chain.invoke(
                {"user_input": input["user_input"], "chat_history": input["chat_history"]},
                config=config,
            )
            time_scope = parsed_result.time_scope
            user_data = self.get_user_data(self.user_id)
            if not user_data:
                return {
                    "status": "failure",
                    "message": f"No user data found for user_id={self.user_id}.",
                }

            target_year, target_semester = TimeScopeHandler.calculate_target_year_and_semester(
                user_data["academic_year"], user_data["semester"], time_scope
            )

            subjects = self.query_subjects_enrolled(
                self.user_id, target_year, target_semester
            )

            if not subjects:
                return {
                    "status": "failure",
                    "message": f"No subjects found for user_id={self.user_id}, year='{target_year}', semester='{target_semester}'."
                }

            total_credits = sum(subject["credits"] for subject in subjects)

            return {
                "status": "success",
                "time_scope": time_scope,
                "target_year": target_year,
                "target_semester": target_semester,
                "subjects": subjects,
                "total_credits": total_credits
            }

        except (ValidationError, ValueError) as e:
            return {
                "status": "failure",
                "message": str(e),
            }

    def get_user_data(self, user_id):
        """
        Retrieves user data from the database.

        Args:
            user_id (int): The ID of the user.

        Returns:
            dict or None: User data if found, otherwise None.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT username, password, course, year_of_study, semester, academic_year
                FROM Users
                WHERE user_id = ?
                """,
                (user_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "username": row[0],
                    "password": row[1],
                    "course": row[2],
                    "year_of_study": row[3],
                    "semester": row[4],
                    "academic_year": row[5],
                }
            else:
                return None
        except Exception as e:
            print(f"Error retrieving user data: {e}")
            return None

    def query_subjects_enrolled(self, user_id, academic_year, semester):
        """
        Retrieves the subjects a user is enrolled in for a specific year and semester.

        Args:
            user_id (int): The ID of the user.
            academic_year (str): The academic year.
            semester (str): The semester.

        Returns:
            list: A list of enrolled subjects with details.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT degree_id FROM Degrees
                WHERE degree_name = (
                    SELECT course FROM Users WHERE user_id = ?
                );
            """, (user_id,))
            degree_ids = [row[0] for row in cursor.fetchall()]
            if not degree_ids:
                conn.close()
                return []

            subjects = []
            for degree_id in degree_ids:
                cursor.execute("""
                    SELECT DISTINCT s.subject_name, s.credits, s.syllabus
                    FROM Subject_Staff_AcademicTerm ssa
                    JOIN Subjects s ON ssa.subject_id = s.subject_id
                    WHERE ssa.degree_id = ? AND ssa.academic_year = ? AND ssa.semester = ?;
                """, (degree_id, academic_year, semester))
                for row in cursor.fetchall():
                    subjects.append({
                        "subject_name": row[0],
                        "credits": row[1],
                        "syllabus": row[2]
                    })

            conn.close()
            return subjects

        except Exception as e:
            print(f"Error in query_subjects_enrolled: {e}")
            return []


class CourseReportResponseChain(Runnable):
    """
    Generates a user-friendly response summarizing enrolled course data.

    Attributes:
        llm: The language model for processing input.
        prompt: Chat prompt template for generating responses.
        output_parser: Parses the output into a string format.
    """

    def __init__(self, llm, memory=True):
        """
        Initializes the response chain with a language model and optional memory.

        Args:
            llm: An instance of the language model.
            memory (bool): Whether to include chat history in the response generation.
        """
        super().__init__()
        self.llm = llm

        prompt_template = PromptTemplate(
            system_template="""
            You are a chatbot that generates a user-friendly response about a student's
            enrolled subjects.

            **Guidelines:**
            1. Summarize all the subjects for the given academic year and semester.
            2. For each subject, include the name, number of credits, and a short description.
            3. Mention the total credits for all subjects combined.
            4. If the user asked for the previous year/semester, mention that in the response.
            5. If no subjects exist, inform the user accordingly.

            Here is the user input:
            {user_input}

            Here is the data returned by the reasoning chain:
            - time_scope: {time_scope}
            - target_year: {target_year}
            - target_semester: {target_semester}
            - subjects: {subjects}
            - total_credits: {total_credits}
            """,
            human_template="User Query: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, input, config=None, **kwargs):
        """
        Generates a user-friendly response summarizing enrolled subjects.

        Args:
            input (dict): Input containing user query and course data.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            str: A user-friendly response summarizing the course data.
        """
        return self.chain.invoke(
            {
                "user_input": input.get("user_input", ""),
                "chat_history": input["chat_history"],
                "time_scope": input.get("time_scope", "current"),
                "target_year": input.get("target_year", "N/A"),
                "target_semester": input.get("target_semester", "N/A"),
                "subjects": input.get("subjects", []),
                "total_credits": input.get("total_credits", 0),
            },
            config=config,
        )