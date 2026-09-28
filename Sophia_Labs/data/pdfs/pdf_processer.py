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

import os
from typing import List

from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents.base import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Index, Pinecone

# Load environment variables from a .env file
load_dotenv()

def get_text_from_pdf(pdf_file: str) -> List[Document]:
    """
    Extracts text from a PDF file and returns it as a list of Document objects.

    Args:
        pdf_file (str): Path to the PDF file to be processed.

    Returns:
        List[Document]: A list of Document objects, where each represents a page in the PDF.
    """
    # Initialize the PyMuPDFLoader with the given PDF file
    loader = PyMuPDFLoader(pdf_file)

    # Initialize an empty list to store the pages
    pages: List[Document] = []

    # Iterate over each loaded page and add it to the list
    for page in loader.load():
        pages.append(page)

    # Return the list of extracted pages
    return pages


def create_embeddings():
    """
    Processes all PDF files in the current directory, splits their text into chunks,
    and stores their embeddings in a Pinecone vector database.

    Steps:
    1. Finds all PDF files in the current directory.
    2. Extracts text from each PDF file.
    3. Splits the text into manageable chunks for embedding.
    4. Stores the resulting embeddings in a Pinecone vector database.
    """
    # Get a list of all PDF files in the current directory
    pdf_files = [f for f in os.listdir() if f.endswith(".pdf")]

    # Initialize a list to store all extracted documents
    docs: List[Document] = []

    # Extract text from each PDF file and add to the docs list
    for pdf_file in pdf_files:
        docs.extend(get_text_from_pdf(pdf_file))

    # Define a text splitter to split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Maximum size of each chunk
        chunk_overlap=250,  # Overlap between chunks to preserve context
        add_start_index=True,  # Include the starting index of each chunk
    )

    # Split all documents into smaller chunks
    all_splits = text_splitter.split_documents(docs)

    # Initialize a connection to Pinecone
    pc = Pinecone()
    index: Index = pc.Index("sophia-labs") 
    # Initialize a Pinecone vector store with OpenAI embeddings
    vector_store = PineconeVectorStore(
        index=index, embedding=OpenAIEmbeddings(model="text-embedding-3-small")
    )

    # Generate unique IDs for each chunk
    ids = [str(i) for i in range(len(all_splits))]

    # Add the documents and their embeddings to the vector store
    vector_store.add_documents(documents=all_splits, ids=ids)


create_embeddings()