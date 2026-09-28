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
Module: Evaluation Chains

This module provides reasoning and response chains for handling queries about upcoming 
evaluations. It integrates with a database to retrieve evaluation details and generates 
user-friendly responses summarizing the evaluation data.

Classes:
    - EvaluationQueryInput: Pydantic model for capturing the number of evaluations requested.
    - EvaluationInfo: Pydantic model for structuring evaluation details.
    - EvaluationReasoningChain: Processes user queries and retrieves evaluation details 
      from the database.
    - EvaluationResponseChain: Generates a summarized response about upcoming evaluations.

Usage:
    Use `EvaluationReasoningChain` to extract evaluation data based on user input. Use 
    `EvaluationResponseChain` to format the data into a friendly response for end-users.
"""

import sqlite3
from pydantic import BaseModel, ValidationError, Field
from langchain.schema.runnable.base import Runnable
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates
from Sophia_Labs.data.loader import get_database_path


class EvaluationQueryInput(BaseModel):
    """
    Represents the query input for fetching upcoming evaluations.

    Attributes:
        num_evaluations (int): The number of evaluations to retrieve.
    """
    num_evaluations: int = Field(
        default=5, description="The number of upcoming evaluations to retrieve."
    )


class EvaluationInfo(BaseModel):
    """
    Represents details about an evaluation.

    Attributes:
        subject (str): The name of the subject.
        evaluation_type (str): The type of evaluation (e.g., Exam, Project).
        evaluation_date (str): The date of the evaluation.
    """
    subject: str = Field(description="The name of the subject.")
    evaluation_type: str = Field(
        description="The type of evaluation (e.g., Exam, Project)."
    )
    evaluation_date: str = Field(description="The date of the evaluation.")


class EvaluationReasoningChain(Runnable):
    """
    Handles the reasoning process for fetching and summarizing upcoming evaluations.

    Attributes:
        llm: The language model for processing input.
        db_path (str): Path to the SQLite database.
        prompt: Chat prompt template for generating reasoning outputs.
        output_parser: Parses the output into an EvaluationQueryInput object.
    """

    def __init__(self, llm, memory=False):
        """
        Initializes the reasoning chain with a language model and database path.

        Args:
            llm: An instance of the language model.
            memory (bool): Whether to include chat history in the prompt generation.
        """
        super().__init__()
        self.llm = llm
        self.db_path = get_database_path()

        prompt_template = PromptTemplate(
            system_template="""
            You are a chatbot designed to help students retrieve upcoming evaluations.

            **Guidelines:**

            1. Understand user query to identify the number of evaluations requested
               (default is 5).
            2. Query the database to fetch the next upcoming evaluations across all
               subjects.
            3. Handle errors and provide clear feedback.

            **Output Format:** Return the following JSON structure:
            {{
                "num_evaluations": <number>
            }}

            User input: {user_input}
            Database Path: {db_path}
            """,
            human_template="User Input: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = PydanticOutputParser(pydantic_object=EvaluationQueryInput)
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, input, config=None, **kwargs):
        """
        Processes the user input and retrieves evaluation data.

        Args:
            input (dict): Contains user input, chat history, and other parameters.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            list: A list of evaluations or an empty list if no evaluations are found.
        """
        try:
            result = self.chain.invoke(
                {
                    "user_input": input["user_input"],
                    "chat_history": input["chat_history"],
                    "db_path": self.db_path,
                },
                config=config,
            )
            print(f"Validated Input: {result}")
            evaluations = self.query_evaluations(num_evaluations=result.num_evaluations)

            if not evaluations:
                return []

            return evaluations
        except (ValidationError, ValueError) as e:
            print(f"Error during reasoning chain: {str(e)}")
            return []

    def query_evaluations(self, num_evaluations=5):
        """
        Queries the database to retrieve upcoming evaluations.

        Args:
            num_evaluations (int): The number of evaluations to fetch.

        Returns:
            list: A list of evaluation details or an empty list if none are found.
        """
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT e.evaluation_type, e.evaluation_date, s.subject_name
                FROM Evaluations e
                JOIN Subjects s ON e.subject_id = s.subject_id
                ORDER BY e.evaluation_date ASC
                LIMIT ?
                """,
                (num_evaluations,),
            )
            evaluation_records = cursor.fetchall()
            connection.close()

            if not evaluation_records:
                print("No upcoming evaluations found.")
                return []

            print(f"Retrieved evaluations: {evaluation_records}")
            return [
                {
                    "evaluation_type": record[0],
                    "evaluation_date": record[1],
                    "subject": record[2],
                }
                for record in evaluation_records
            ]
        except Exception as e:
            print(f"Error querying evaluations: {str(e)}")
            return []


class EvaluationResponseChain(Runnable):
    """
    Generates a user-friendly response summarizing evaluation details.

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
            You are a chatbot that generates a user-friendly response summarizing
            upcoming evaluations.

            **Guidelines:**

            1. Summarize evaluations in a clear and concise format.
            2. Handle cases where no evaluations are available.

            User input: {user_input}
            Evaluation data: {evaluation_data}

            Generate a friendly and accurate response.
            """,
            human_template="User Input: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)
        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, input, config=None, **kwargs):
        """
        Generates a response summarizing the evaluation data.

        Args:
            input (dict): Contains user input and evaluation data.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            str: A user-friendly summary of the evaluation data.
        """
        try:
            response = self.chain.invoke(
                {
                    "user_input": input["user_input"],
                    "chat_history": input["chat_history"],
                    "evaluation_data": input["evaluation_data"],
                },
                config=config,
            )
            print(f"Generated Response: {response}")
            return response
        except Exception as e:
            print(f"Error during response chain: {str(e)}")
            return "Error generating response."