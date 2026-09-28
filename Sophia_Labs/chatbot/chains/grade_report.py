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
Module: Grade Report Chains

This module provides reasoning and response chains for handling user queries about 
grade reports. It retrieves grades based on academic year and semester and generates 
user-friendly responses.

Classes:
    - GradeReportQueryInput: Parses user input for grade report requests.
    - GradeReportReasoningChain: Processes user queries and retrieves grades.
    - GradeReportResponseChain: Generates a summarized response about grades.

Usage:
    Use `GradeReportReasoningChain` to query grades based on user input and 
    `GradeReportResponseChain` to format the results into a user-friendly response.
"""

import sqlite3
from pydantic import BaseModel, ValidationError, Field
from langchain.schema.runnable.base import Runnable
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates
from Sophia_Labs.data.loader import get_database_path


class GradeReportQueryInput(BaseModel):
    """
    Model to parse the user's request about their grade report.

    Attributes:
        time_scope (str): Indicates whether the user wants "current" or "previous" year/semester.
    """
    time_scope: str = Field(
        ..., description="Either 'previous' or 'current' to indicate which year/semester the user wants."
    )


class GradeReportReasoningChain(Runnable):
    """
    Handles reasoning for retrieving grade reports based on user input.

    Attributes:
        llm: The language model for processing input.
        db_path (str): Path to the SQLite database.
        user_id (int): The ID of the user interacting with the chain.
        prompt: Chat prompt template for generating reasoning outputs.
        output_parser: Parses the output into a GradeReportQueryInput object.
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

        # Prompt template to parse out "previous" vs "current"
        prompt_template = PromptTemplate(
            system_template="""
            You are a chatbot designed to help students retrieve their grade information.

            **Instructions:**
            1. Check if the user wants the "previous" or "current" year/semester.
            2. Return that strictly in JSON format:
               {{
                 "time_scope": "previous" | "current"
               }}
            """,
            human_template="User Query: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = PydanticOutputParser(pydantic_object=GradeReportQueryInput)
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, input, config=None, **kwargs):
        """
        Processes user input to determine the time scope and query the database for grades.

        Args:
            input (dict): Contains user input and chat history.
            config: Optional configuration for the chain.

        Returns:
            dict: Contains grade information or an error message.
        """
        try:
            parsed_result = self.chain.invoke(
                {
                    "user_input": input["user_input"],
                    "chat_history": input["chat_history"]
                },
                config=config,
            )
            time_scope = parsed_result.time_scope

            # Retrieve user data
            user_data = self.get_user_data(self.user_id)
            if not user_data:
                return {
                    "status": "failure",
                    "message": f"No user data found for user_id={self.user_id}.",
                }

            # Determine academic year and semester
            target_year, target_semester = self.calculate_target_year_and_semester(
                user_data["academic_year"], user_data["semester"], time_scope
            )

            # Query grades
            grade_info = self.query_grades(self.user_id, target_year, target_semester)

            if not grade_info:
                return {
                    "status": "failure",
                    "message": f"No grades found for user_id={self.user_id}, year='{target_year}', semester='{target_semester}'.",
                }

            all_grades = [record["grade"] for record in grade_info]
            average_grade = sum(all_grades) / len(all_grades) if all_grades else 0.0

            return {
                "status": "success",
                "time_scope": time_scope,
                "target_year": target_year,
                "target_semester": target_semester,
                "grade_info": grade_info,
                "average_grade": average_grade,
            }

        except (ValidationError, ValueError) as e:
            return {
                "status": "failure",
                "message": str(e),
            }

    def calculate_target_year_and_semester(self, current_year, current_semester, time_scope):
        """
        Calculate the target academic year and semester based on the current year/semester and time scope.

        Args:
            current_year (str): Current academic year, e.g., "2024/2025".
            current_semester (str): Current semester, e.g., "Fall" or "Spring".
            time_scope (str): Desired time scope: "previous" or "current".

        Returns:
            tuple: (target_year, target_semester) adjusted for the time scope.
        """
        start_year, end_year = map(int, current_year.split("/"))

        if time_scope == "current":
            return current_year, current_semester

        if time_scope == "previous":
            if current_semester.lower() == "spring":
                return f"{start_year}/{end_year}", "Fall"
            else:
                return f"{start_year - 1}/{end_year - 1}", "Spring"

        raise ValueError(f"Invalid time scope: {time_scope}")

    def get_user_data(self, user_id):
        """
        Retrieve user information such as academic year and semester.

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
        except Exception:
            return None

    def query_grades(self, user_id, academic_year, semester):
        """
        Query grades for a specific user, academic year, and semester.

        Args:
            user_id (int): The ID of the user.
            academic_year (str): The academic year.
            semester (str): The semester.

        Returns:
            list: A list of grade records or an empty list if no grades are found.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = """
                SELECT DISTINCT
                    s.subject_name,
                    e.evaluation_type,
                    g.grade,
                    ssa.academic_year,
                    ssa.semester
                FROM Grades g
                JOIN Evaluations e ON g.evaluation_id = e.evaluation_id
                JOIN Subjects s ON e.subject_id = s.subject_id
                JOIN Subject_Staff_AcademicTerm ssa ON s.subject_id = ssa.subject_id
                WHERE g.user_id = ?
                  AND ssa.academic_year = ?
                  AND ssa.semester = ?
            """
            cursor.execute(query, (user_id, academic_year, semester))
            rows = cursor.fetchall()
            conn.close()

            grade_records = []
            for row in rows:
                grade_records.append({
                    "subject_name": row[0],
                    "evaluation_type": row[1],
                    "grade": row[2],
                    "academic_year": row[3],
                    "semester": row[4],
                })

            return grade_records
        except Exception:
            return []


class GradeReportResponseChain(Runnable):
    """
    Handles the generation of user-friendly responses about grade reports.

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
            You are a chatbot that generates a user-friendly response about a student's grade report.

            **Guidelines:**
            1. Summarize all the retrieved grades in a clear format.
            2. Mention the user's overall average grade.
            3. If no grades are found, inform the user.

            Here is the user input:
            {user_input}

            Here is the data returned by the reasoning chain:
            - time_scope: {time_scope}
            - target_year: {target_year}
            - target_semester: {target_semester}
            - grade_info: {grade_info}
            - average_grade: {average_grade}
            """,
            human_template="User Query: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, input, config=None, **kwargs):
        """
        Generates a response summarizing the user's grade report.

        Args:
            input (dict): Contains user input and grade report data.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            str: A user-friendly summary of the grade report.
        """
        return self.chain.invoke(
            {
                "user_input": input.get("user_input", ""),
                "chat_history": input["chat_history"],
                "time_scope": input.get("time_scope", "current"),
                "target_year": input.get("target_year", "N/A"),
                "target_semester": input.get("target_semester", "N/A"),
                "grade_info": input.get("grade_info", []),
                "average_grade": input.get("average_grade", 0.0),
            },
            config=config,
        )