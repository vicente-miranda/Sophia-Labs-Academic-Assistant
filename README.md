# Sophia Labs

Sophia Labs is a chat assistant for students. It brings course and grade information, deadlines, teaching staff details, personal notes, and policy questions into one Streamlit interface.

An intent router sends each request to a dedicated LangChain flow. SQLite stores academic records and notes. For questions about policies and technical setup, the assistant retrieves passages from reference documents through Pinecone before generating an answer.

This is a source snapshot of the prototype. The private data, documents, and credentials are omitted. Running the full application requires replacement data and OpenAI and Pinecone services.
