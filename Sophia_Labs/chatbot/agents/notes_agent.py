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
Module: NotesAgent

This module provides the implementation of the `NotesAgent` class, which manages
interactions with a university's student database. It uses tools for CRUD operations on 
student notes and integrates them with a chatbot powered by LangChain and OpenAI.

Classes:
    - NotesAgent: Handles note-related operations using LangChain tools and acts as a chatbot.

Dependencies:
    - LangChain for agent creation and tool integration.
    - Pydantic for data modeling.
    - SQLite for database path retrieval.

Usage:
    The `NotesAgent` is designed for note management operations such as creating,
    reading, updating, and deleting student notes.
"""

from typing import List, Type
import sqlite3
from pydantic import BaseModel
from Sophia_Labs.data.loader import get_database_path

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool

from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_agent_prompt_template
from Sophia_Labs.chatbot.tools.create_note import *
from Sophia_Labs.chatbot.tools.update_note import *
from Sophia_Labs.chatbot.tools.delete_note import *
from Sophia_Labs.chatbot.tools.read_note import *


class NotesAgent:
    """
    A chatbot agent designed to manage student notes within a university system.
    
    This agent utilizes LangChain tools to perform create, read, update, and delete 
    operations on student notes and responds to user queries accordingly.
    
    Attributes:
        llm (ChatOpenAI): The language model used to power the chatbot.
        user_id (int): The ID of the user interacting with the agent.
        tools (List): A list of tools available to the agent for note management.
        prompt (str): The prompt template used to guide the agent's behavior.
        agent (LangChain Agent): The LangChain-based agent for managing operations.
        agent_executor (AgentExecutor): Executes the agent's operations.
    """

    def __init__(self, llm: ChatOpenAI, user_id: int):
        """
        Initializes the NotesAgent with the specified language model and user ID.

        Args:
            llm (ChatOpenAI): An instance of the ChatOpenAI language model.
            user_id (int): The ID of the user interacting with the agent.
        """
        self.llm = llm
        self.user_id = user_id
        self._agent_executor = None  # Placeholder for lazy initialization

        # Initialize tools
        read_note_tool = ReadNoteTool()
        update_note_tool = UpdateNoteTool()
        create_note_tool = CreateNoteTool()
        delete_note_tool = DeleteNoteTool()
        self.tools: List = [
            update_note_tool, create_note_tool, delete_note_tool, read_note_tool
        ]

        # Define the prompt template for profile updates
        prompt_template = PromptTemplate(
            system_template="""
            You are a chatbot connected to the university's student database.

            You have access to the following tools to help the user update their profile:

            1. Create a new note for a student.
            2. Update an existing note for a student.
            3. Delete a note for a student.
            4. Read notes for a student.

            The user's ID is {user_id}.

            If none of the above tools are needed, you can respond politely and inform the user about the available operations.
            """,
            human_template="User Query: {user_input}",
        )

        self.prompt = generate_agent_prompt_template(prompt_template)
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)

    @property
    def agent_executor(self):
        """
        Lazily initializes and returns the agent_executor.
        
        This ensures the `AgentExecutor` is only created when accessed for the first time,
        optimizing resource usage.

        Returns:
            AgentExecutor: The executor that manages agent operations.
        """
        if self._agent_executor is None:
            self._agent_executor = AgentExecutor(
                agent=self.agent, tools=self.tools
            )
        return self._agent_executor