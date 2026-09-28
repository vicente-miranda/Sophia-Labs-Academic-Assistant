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
Module: Intent Classification Router

This module provides a router chain for classifying user intents in a university chatbot. 
It identifies the user's query intent based on the input and context provided by the 
conversation history.

Classes:
    - IntentClassification: Pydantic model for representing the classified user intent.
    - RouterChain: Processes user input to classify the intent and route it to the 
      appropriate handler.

Usage:
    Use `RouterChain` to classify user queries into predefined intents for a university chatbot.
"""

from typing import Literal
from langchain import callbacks
from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable.base import Runnable
from pydantic import BaseModel, Field

from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates


class IntentClassification(BaseModel):
    """
    Represents the classification of user intent.

    Attributes:
        intent (Literal): The classified intent of the user query. Supported intents include:
            - Course Report
            - Grade Report
            - Deadlines
            - Profile Update
            - Teaching Staff
            - University Policies
            - IT Configuration Support
            - Notes
    """
    intent: Literal[
        "Course Report",
        "Grade Report",
        "Deadlines",
        "Profile Update",
        "Teaching Staff",
        "University Policies",
        "IT Configuration Support",
        "Notes",
    ] = Field(
        ..., description="The classified intent of the user query",
    )


class RouterChain(Runnable):
    """
    A chain for classifying user intents in a university chatbot.

    Attributes:
        llm: The language model for processing input.
        prompt: Chat prompt template for generating classification outputs.
        output_parser: Parses the output into an IntentClassification object.
        format_instructions: Format instructions for the output parser.
        chain: Composed chain to handle prompt generation, processing, and parsing.
    """

    def __init__(self, llm, memory=True):
        """
        Initializes the RouterChain with a language model and optional memory.

        Args:
            llm: An instance of the language model.
            memory (bool): Whether to include chat history in the classification process.
        """
        super().__init__()

        self.llm = llm
        prompt_template = PromptTemplate(
            system_template="""
            You are an expert classifier of user intentions for a university chatbot.
            Your role is to accurately identify the user's intent based on their query
            and the context provided by the conversation history. Analyze the user's 
            query in the conversation history context and classify it into one of the intents.
            You'll use the following detailed descriptions to classify the user's intent:

            1. **Course Report:**  
            The user requests a report of their courses for a specific semester or academic year.  

            2. **Grade Report:**  
            The user requests a report of their grades for a specific subject or semester.  

            3. **Deadlines:**  
            The user is looking for information about deadlines for assignments, projects, or exams.  

            4. **Profile Update:**  
            The user requests to update their profile information, such as username or password.  

            5. **Teaching Staff:**  
            The user is looking for contact information for teaching staff associated with a specific subject.  

            6. **University Policies:**  
            The user is looking for information about university policies, such as academic integrity or grading.  

            7. **IT Configuration Support:**  
            The user is seeking guidance on setting up or troubleshooting IT services like Eduroam or VPNs.  

            8. **Notes:**  
            The user requests to create, update, or delete personal notes.  

            **Input:**  
            - User Input: {user_input}  
            - Conversation History: {chat_history}  

            **Output Format:**  

            - Intent: {format_instructions}
            """,
            human_template="User Query: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)

        self.output_parser = PydanticOutputParser(pydantic_object=IntentClassification)
        self.format_instructions = self.output_parser.get_format_instructions()
        self.chain = (self.prompt | self.llm | self.output_parser).with_config(
            {"run_name": self.__class__.__name__}
        )  # Add a run name to the chain on LangSmith

    def invoke(self, input, config=None, **kwargs):
        """
        Processes the user input and classifies their intent.

        Args:
            input (dict): Contains user input and conversation history.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            IntentClassification: The classified intent of the user's query.
        """
        with callbacks.collect_runs() as cb:
            return self.chain.invoke(
                {
                    "user_input": input["user_input"],
                    "chat_history": input.get("chat_history", ""),
                    "format_instructions": self.format_instructions,
                },
            )