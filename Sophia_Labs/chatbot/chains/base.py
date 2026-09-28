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
Module: Prompt Templates

This module defines classes and functions for creating prompt templates used in 
conversation flows. These templates are essential for defining the structure of system 
and user messages, as well as enabling functionality like memory and agent scratchpad.

Classes:
    - PromptTemplate: A model for defining system and human message templates.

Functions:
    - generate_prompt_templates: Configures chat prompt templates with optional memory.
    - generate_agent_prompt_template: Generates prompt templates for use with an agent 
      scratchpad.

Usage:
    This module is designed to provide reusable components for configuring prompt 
    templates in chatbot systems.
"""

# Import necessary modules and classes
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """
    Defines templates for system and human messages used in a conversation.

    Attributes:
        system_template (str): Template for system messages, typically instructions or setup.
        human_template (str): Template for human messages, containing placeholders for user input.
    """
    system_template: str = Field(
        description="Template for system messages, e.g., 'You are a student support assistant.'"
    )
    human_template: str = Field(
        description="Template for human messages, e.g., 'User says: {user_input}'"
    )


def generate_prompt_templates(
    prompt_template: PromptTemplate, memory: bool
) -> ChatPromptTemplate:
    """
    Generate a chat prompt template based on given templates and memory setting.

    Args:
        prompt_template (PromptTemplate): An instance of PromptTemplate containing system and human templates.
        memory (bool): A flag indicating whether to include chat history in the prompt.

    Returns:
        ChatPromptTemplate: A configured chat prompt template with specified message structure.
    """
    if memory:
        # Create prompt template including chat history if memory is enabled
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    prompt_template.system_template
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template(
                    prompt_template.human_template
                ),
            ]
        )
    else:
        # Create prompt template without chat history
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    prompt_template.system_template
                ),
                HumanMessagePromptTemplate.from_template(
                    prompt_template.human_template
                ),
            ]
        )

    return prompt


def generate_agent_prompt_template(
    prompt_template: PromptTemplate,
) -> ChatPromptTemplate:
    """
    Generate a chat prompt template based on given templates and memory setting.

    Args:
        prompt_template (PromptTemplate): An instance of PromptTemplate containing system and human templates.

    Returns:
        ChatPromptTemplate: A configured chat prompt template with agent scratchpad structure.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(prompt_template.system_template),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template(prompt_template.human_template),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    return prompt