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
Module: Generic Chat Chains

This module provides chains for handling generic chat responses and classifying user 
messages as generic or academic/transactional queries in a university context.

Classes:
    - GenericChatResponseChain: Generates friendly and concise responses to university-related queries.
    - GenericChatClassifier: Classifies user messages as generic chat or not.
    - GenericChatClassifierChain: Processes user input to classify messages based on their nature.

Usage:
    Use `GenericChatResponseChain` to generate chatbot responses for general queries. Use 
    `GenericChatClassifierChain` to classify user messages as generic or academic.
"""

from langchain.schema.runnable.base import Runnable
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates


class GenericChatResponseChain(Runnable):
    """
    A chain for generating responses to generic university-related queries.

    Attributes:
        llm: The language model for processing input.
        prompt: Chat prompt template for generating responses.
        output_parser: Parses the output into a string format.
    """

    def __init__(self, llm, memory=True):
        """
        Initializes the GenericChatResponseChain with a language model and optional memory.

        Args:
            llm: An instance of the language model.
            memory (bool): Whether to include chat history in the response generation.
        """
        super().__init__()

        self.llm = llm
        prompt_template = PromptTemplate(
            system_template=""" 
            You are a chatbot that provides generic, friendly, and helpful responses for university-related queries.
            Your objectives are to maintain an engaging tone and ensure accurate, concise responses.
            Limit your answer to a maximum of 30 words.

            Guidelines:

            1. **Tone and Engagement:**
            - Use a professional yet friendly tone to make users feel comfortable and valued.
            - Provide clear, concise responses to the user's query.

            2. **Context Awareness:**
            - Leverage previous conversation history to personalize responses and maintain context.
            - Show an understanding of the user's academic environment and related topics.

            3. **University-Centric Focus:**
            - Focus on queries related to university life, academics, and resources.
            - Redirect unrelated topics politely, emphasizing your specialization in academic support.

            4. **Handling General Questions:**
            - If the query is outside the chatbot's scope, suggest university resources or guide the user back to relevant topics.

            Your ultimate goal is to provide valuable assistance while encouraging further interaction within the university ecosystem.
            
            Here is the user input:
            {user_input}
            """,
            human_template="User Query: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory)
        self.output_parser = StrOutputParser()

        self.chain = self.prompt | self.llm | self.output_parser

    def invoke(self, input, config=None, **kwargs):
        """
        Generates a concise and friendly response to the user's query.

        Args:
            input (dict): Contains user input and chat history.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            str: A concise and friendly response to the user's query.
        """
        return self.chain.invoke(
            {
                "user_input": input["user_input"],
                "chat_history": input["chat_history"],
            },
            config=config,
        )


class GenericChatClassifier(BaseModel):
    """
    Represents the classification of a user message as generic chat or not.

    Attributes:
        generic_chat (bool): Indicates whether the message is generic chat.
    """
    generic_chat: bool = Field(
        description="""Generic chat is defined as:
        - Conversations that are informal, social, or casual in nature.
        - Topics that do not directly relate to academic or university topics.
        - Examples include greetings, jokes, small talk, or personal inquiries unrelated to university or profile update (username or password).
        If the user message falls under this category, set 'generic_chat' to True.""",
    )


class GenericChatClassifierChain(Runnable):
    """
    A chain for classifying user messages as generic chat or academic/transactional queries.

    Attributes:
        llm: The language model for processing input.
        prompt: Chat prompt template for generating classification outputs.
        output_parser: Parses the output into a GenericChatClassifier object.
    """

    def __init__(self, llm, memory=True):
        """
        Initializes the GenericChatClassifierChain with a language model and optional memory.

        Args:
            llm: An instance of the language model.
            memory (bool): Whether to include chat history in the classification process.
        """
        super().__init__()

        self.llm = llm
        prompt_template = PromptTemplate(
            system_template=""" 
            You specialize in distinguishing between generic chat and academic/transactional queries in a university setting.
            Your task is to analyze each user message and determine if it is a generic chat.

            Guidelines:
            - Consider the context of the entire conversation.
            - Check if prior messages provide context for borderline cases.

            Here is the user input:
            {user_input}

            Here is the chat history:
            {chat_history}

            Output your results in the following format:  
            {format_instructions}
            """,
            human_template="User Query: {user_input}",
        )

        self.prompt = generate_prompt_templates(prompt_template, memory=memory)

        self.output_parser = PydanticOutputParser(pydantic_object=GenericChatClassifier)
        self.format_instructions = self.output_parser.get_format_instructions()
        self.chain = (self.prompt | self.llm | self.output_parser).with_config(
            {"run_name": self.__class__.__name__}
        )

    def invoke(self, input, config=None, **kwargs) -> GenericChatClassifier:
        """
        Classifies the user message as generic chat or not.

        Args:
            input (dict): Contains user input, chat history, and other parameters.
            config: Optional configuration for the chain.
            **kwargs: Additional arguments.

        Returns:
            GenericChatClassifier: The classification result.
        """
        result = self.chain.invoke(
            {
                "user_input": input["user_input"],
                "chat_history": input["chat_history"],
                "format_instructions": self.format_instructions,
            },
        )
        return result