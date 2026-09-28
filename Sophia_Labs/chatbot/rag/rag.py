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
Module: RAG Pipeline for Chatbot

This module implements a Retrieval-Augmented Generation (RAG) pipeline for a university 
chatbot. It integrates with Pinecone for vector-based document retrieval and uses a 
language model to generate responses based on the retrieved context.

Classes:
    - RAGPipeline: Combines vector retrieval and language model inference into a unified 
      pipeline for answering user queries.

Usage:
    Use `RAGPipeline` to handle user queries, retrieve relevant documents from the vector 
    store, and generate responses tailored to specific intents such as university policies 
    or IT support.
"""

from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from typing import List
from langchain_core.documents.base import Document
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Index, Pinecone
from dotenv import load_dotenv
from Sophia_Labs.chatbot.chains.base import PromptTemplate, generate_prompt_templates


class RAGPipeline:
    """
    A pipeline that combines document retrieval and language model inference to handle 
    user queries effectively.

    Attributes:
        index (Index): Pinecone index for vector-based document retrieval.
        vector_store (PineconeVectorStore): Vector store abstraction over Pinecone.
        retriever: Retrieves relevant documents based on query similarity.
        llm: The language model for generating responses.
        policy_prompt_template: Prompt template for university policies and regulations.
        it_support_prompt_template: Prompt template for IT configuration support.
        policy_prompt: Configured prompt for policies.
        it_support_prompt: Configured prompt for IT support.
        _rag_chain: Unified chain combining retrieval and generation steps.
    """

    def __init__(
        self,
        index_name: str,
        embeddings_model: str,
        llm: ChatOpenAI,
        memory: bool = False,
    ):
        """
        Initializes the RAGPipeline with vector store and language model.

        Args:
            index_name (str): Name of the Pinecone index.
            embeddings_model (str): Model for generating embeddings.
            llm (ChatOpenAI): Instance of the language model.
            memory (bool): Whether to include memory in the reasoning process.
        """
        load_dotenv()

        self.pc = Pinecone()
        self.index: Index = self.pc.Index(index_name)

        self.vector_store = PineconeVectorStore(
            index=self.index,
            embedding=OpenAIEmbeddings(model=embeddings_model),
        )

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 3, "score_threshold": 0.5},
        )

        # Initialize the language model
        self.llm = llm

        # Define dynamic prompt templates
        self.policy_prompt_template = PromptTemplate(
            system_template="""You are a chatbot that helps users find information about university policies, academic regulations,
            student rules, or official documents. Answer the question concisely based on relevant documents.

            {context}

            Question: {user_input}

            Helpful Answer:""",
            human_template="Customer Query: {user_input}",
        )

        self.it_support_prompt_template = PromptTemplate(
            system_template="""You are a chatbot that provides IT configuration support for students, focusing on devices, VPNs, and services like Eduroam.
            Answer the question concisely based on relevant documents.

            {context}

            Question: {user_input}

            Helpful Answer:""",
            human_template="Customer Query: {user_input}",
        )

        self.policy_prompt = generate_prompt_templates(self.policy_prompt_template, memory=False)
        self.it_support_prompt = generate_prompt_templates(self.it_support_prompt_template, memory=False)

        # Combine components into a RAG chain
        self._rag_chain = self._build_chain()

    def determine_prompt_type(self, user_input: str) -> str:
        """
        Determines the prompt type based on user input.

        Args:
            user_input (str): The user's query.

        Returns:
            str: The determined prompt type ("policies_and_regulations", "it_support", or "generic").
        """
        policy_keywords = ["policy", "regulation", "academic", "charter", "evaluation", "student rules"]
        if any(keyword in user_input.lower() for keyword in policy_keywords):
            return "policies_and_regulations"

        it_keywords = ["eduroam", "VPN", "mac", "windows", "android", "ios", "configuration", "device", "setup"]
        if any(keyword in user_input.lower() for keyword in it_keywords):
            return "it_support"

        return "generic"

    def _build_chain(self):
        """
        Builds the unified RAG chain by combining retrieval and generation steps.

        Returns:
            RunnableChain: A composed chain for processing queries.
        """
        return (
            RunnablePassthrough()
            | RunnableLambda(lambda x: {"user_input": x["user_input"], "prompt_type": self.determine_prompt_type(x["user_input"])} )
            | RunnableLambda(self._retrieve_context)  # Retrieve and format context
            | RunnableLambda(self._select_prompt)  # Select appropriate prompt
            | self.llm  # Generate response using LLM
            | StrOutputParser()  # Parse output as string
        )

    def _retrieve_context(self, inputs: dict) -> dict:
        """
        Retrieves and formats context from the vector store.

        Args:
            inputs (dict): The input query.

        Returns:
            dict: The input augmented with formatted context.
        """
        query = inputs["user_input"]
        documents = self.retriever.get_relevant_documents(query)
        formatted_context = self._format_docs(documents)
        inputs["context"] = formatted_context
        return inputs

    def _select_prompt(self, inputs: dict) -> dict:
        """
        Selects the prompt template based on the query type.

        Args:
            inputs (dict): The input containing prompt type and context.

        Returns:
            dict: Generated prompt with the selected template.
        """
        prompt_type = inputs["prompt_type"]
        if prompt_type == "policies_and_regulations":
            return self.policy_prompt.invoke({"context": inputs["context"], "user_input": inputs["user_input"]})
        elif prompt_type == "it_support":
            return self.it_support_prompt.invoke({"context": inputs["context"], "user_input": inputs["user_input"]})
        else:
            # Default to policy prompt
            return self.policy_prompt.invoke({"context": inputs["context"], "user_input": inputs["user_input"]})

    @staticmethod
    def _format_docs(documents: List[Document]) -> str:
        """
        Formats retrieved documents into a single string for context input to the model.

        Args:
            documents (List[Document]): List of documents retrieved from the vector store.

        Returns:
            str: Concatenated document contents.
        """
        return "\n\n".join(doc.page_content for doc in documents)

    @property
    def rag_chain(self):
        """
        Returns the constructed RAG chain.

        Returns:
            RunnableChain: The unified RAG chain.
        """
        return self._rag_chain