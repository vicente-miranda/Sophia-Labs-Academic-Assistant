# Import necessary classes and modules for chatbot functionality
from typing import Any, Callable, Dict, Optional, Tuple
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from Sophia_Labs.chatbot.memory import MemoryManager
from langchain.schema.runnable.base import Runnable
from langchain_core.messages.ai import AIMessage
from Sophia_Labs.chatbot.router.loader import load_intention_classifier
from Sophia_Labs.chatbot.rag.rag import RAGPipeline
from Sophia_Labs.chatbot.chains.generic_chat import (
    GenericChatClassifierChain,
    GenericChatResponseChain,
)
from Sophia_Labs.chatbot.chains.router import RouterChain
from Sophia_Labs.chatbot.agents.notes_agent import NotesAgent
from Sophia_Labs.chatbot.chains.course_report import (
    CourseReportQueryInput,
    CourseReportReasoningChain,
    CourseReportResponseChain,
)
from Sophia_Labs.chatbot.chains.deadlines import (
    EvaluationQueryInput,
    EvaluationInfo,
    EvaluationReasoningChain,
    EvaluationResponseChain,
)
from Sophia_Labs.chatbot.chains.course_report import (
    CourseReportQueryInput,
    CourseReportReasoningChain,
    CourseReportResponseChain,
)
from Sophia_Labs.chatbot.chains.create_note import NoteInformation, CreateNoteChain
from Sophia_Labs.chatbot.chains.grade_report import (
    GradeReportQueryInput,
    GradeReportReasoningChain,
    GradeReportResponseChain,
)
from Sophia_Labs.chatbot.chains.teaching_staff import (
    TeachingStaffQueryInput,
    TeachingStaffReasoningChain,
    TeachingStaffResponseChain,
)
class SophiaChatbot:
    """A bot that handles customer service interactions by processing user inputs and
    routing them through configured reasoning and response chains.
    """
    def __init__(self, user_id: str, conversation_id: str):
        """Initialize the bot with session and language model configurations."""
        # Initialize the memory manager to manage session history
        self.memory = MemoryManager()
        self.user_id = user_id
        self.conversation_id = conversation_id
        # Configure the language model with specific parameters for response generation
        self.llm = ChatOpenAI(temperature=0.0, model="gpt-4o-mini")
        # Map intent names to their corresponding reasoning and response chains
        self.memory_config = {
            "configurable": {
                "user_id": self.user_id,
                "conversation_id": self.conversation_id,
            }
        }
        self.chain_map = {
            "evaluation": {
                "reasoning": EvaluationReasoningChain(llm=self.llm),
                "response": self.add_memory_to_runnable(
                    EvaluationResponseChain(llm=self.llm)
                ),
            },
            "course_report": {
                "reasoning": CourseReportReasoningChain(
                    llm=self.llm, user_id=self.user_id
                ),
                "response": self.add_memory_to_runnable(
                    CourseReportResponseChain(llm=self.llm)
                ),
            },
            "grade_report": {
                "reasoning": GradeReportReasoningChain(
                    llm=self.llm, user_id=self.user_id
                ),
                "response": self.add_memory_to_runnable(
                    GradeReportResponseChain(llm=self.llm)
                ),
            },
            "teaching_staff": {
                "reasoning": TeachingStaffReasoningChain(llm=self.llm),
                "response": self.add_memory_to_runnable(
                    TeachingStaffResponseChain(llm=self.llm)
                ),
            },
            "generic_chat": {
                "reasoning": GenericChatClassifierChain(llm=self.llm),
                "response": self.add_memory_to_runnable(
                    GenericChatResponseChain(llm=self.llm)
                ),
            },
            "router": {
                "reasoning": RouterChain(llm=self.llm),
            },
        }
        self.agent_map = {
            "notes": self.add_memory_to_runnable(
                NotesAgent(llm=self.llm, user_id=self.user_id).agent_executor
            )
        }
        self.rag = self.add_memory_to_runnable(
            RAGPipeline(
                index_name="sophia-labs",
                embeddings_model="text-embedding-3-small",
                llm=self.llm,
                memory=True,
            ).rag_chain
        )
        # Load the intention classifier to determine user intents
        self.intention_classifier = load_intention_classifier()
        # Map of intentions to their corresponding handlers
        self.intent_handlers: Dict[str, Callable[[Dict[str, str]], str]] = {
            "generic_chat": self.handle_generic_chat,
            "Course Report": self.handle_course_report,
            "Grade Report": self.handle_grade_report,
            "Deadlines": self.handle_deadline,
            "Teaching Staff": self.handle_teaching_staff,
            "University Policies": self.handle_policy,
            "IT Configuration Support": self.handle_it_support,
            "Note Creation": self.handle_notes,
            "Note Reading": self.handle_notes,
            "Note Update": self.handle_notes,
            "Note Deletion": self.handle_notes,
        }
    def user_login(self, user_id: str, conversation_id: str) -> None:
        """Log in a user by setting the user and conversation identifiers.
        Args:
            user_id: Identifier for the user.
            conversation_id: Identifier for the conversation.
        """
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.memory_config = {
            "configurable": {
                "user_id": self.user_id,
                "conversation_id": self.conversation_id,
            }
        }
    def add_memory_to_runnable(
        self, original_runnable: Runnable[Any, Any]
    ) -> RunnableWithMessageHistory:
        """Wrap a runnable with session history functionality.
        Args:
            original_runnable: The runnable instance to which session history will be added.
        Returns:
            An instance of RunnableWithMessageHistory that incorporates session history.
        """
        return RunnableWithMessageHistory(
            runnable=original_runnable,
            get_session_history=self.memory.get_session_history,  # Retrieve session history
            input_messages_key="user_input",  # Key for user inputs
            history_messages_key="chat_history",  # Key for chat history
            history_factory_config=self.memory.get_history_factory_config(),  # Config for history factory
        ).with_config(
            {
                "run_name": original_runnable.__class__.__name__
            }  # Add runnable name for tracking
        )
    def get_chain(self, intent: str) -> Tuple[Optional[Runnable], Optional[Runnable]]:
        """Retrieve the reasoning and response chains based on user intent.
        Args:
            intent: The identified intent of the user input.
        Returns:
            A tuple containing the reasoning and response chain instances for the intent.
        """
        reasoning_chain: Optional[Runnable] = self.chain_map[intent].get(
            "reasoning", None
        )
        response_chain: Optional[Runnable] = self.chain_map[intent].get(
            "response", None
        )
        return reasoning_chain, response_chain
    def get_agent(self, intent: str):
        """Retrieve the agent based on user intent.
        Args:
            intent: The identified intent of the user input.
        Returns:
            The agent instance for the intent.
        """
        return self.agent_map[intent]
    def get_user_intent(self, user_input: Dict):
        """Classify the user intent based on the input text.
        Args:
            user_input: The input text from the user.
        Returns:
            The classified intent of the user input.
        """
        # Retrieve possible routes for the user's input using the classifier
        intent_routes = self.intention_classifier.retrieve_multiple_routes(
            user_input["user_input"]
        )
        # Handle cases where no intent is identified
        if len(intent_routes) == 0:
            return None
        else:
            intention = intent_routes[0].name  # Use the first matched intent
        # Validate the retrieved intention and handle unexpected types
        if intention is None:
            return None
        elif isinstance(intention, str):
            return intention
        else:
            # Log the intention type for unexpected cases
            intention_type = type(intention).__name__
            print(
                f"I'm sorry, I didn't understand that. The intention type is {intention_type}."
            )
            return None
    def handle_it_support(self, user_input: Dict[str, str]) -> str:
        response = self.rag.invoke(user_input, config=self.memory_config)
        return response
    def handle_policy(self, user_input: Dict[str, str]) -> str:
        response = self.rag.invoke(user_input, config=self.memory_config)
        return response
    def handle_course_report(self, user_input: Dict[str, str]) -> str:
        reasoning_chain, response_chain = self.get_chain("course_report")
        if not reasoning_chain:
            return "Course Report chain not configured."

        reasoning_output: AIMessage = reasoning_chain.invoke(
            {"user_input": user_input["user_input"], "chat_history": self.memory.get_session_history(self.user_id, self.conversation_id).messages}
        )

        if response_chain:
            response: AIMessage = response_chain.invoke(
                {"user_input": user_input["user_input"], "chat_history": self.memory.get_session_history(self.user_id, self.conversation_id).messages, **reasoning_output}, config=self.memory_config
            )
            return response
    def handle_deadline(self, user_input: Dict[str, str]) -> str:
        # Get the reasoning and response chains
        reasoning_chain, response_chain = self.get_chain("evaluation")
        # Invoke the reasoning chain
        reasoning_output: AIMessage = reasoning_chain.invoke(
            {"user_input": user_input["user_input"], "chat_history": self.memory.get_session_history(self.user_id, self.conversation_id).messages}
        )

        # Prepare input for the response chain
        response_input = {
            "user_input": user_input.get("user_input", ""),  # Original user input
            "chat_history": self.memory.get_session_history(self.user_id, self.conversation_id).messages,
            "evaluation_data": reasoning_output.content
            if isinstance(reasoning_output, AIMessage)
            else reasoning_output,
        }
        # Invoke the response chain
        response: AIMessage = response_chain.invoke(
            response_input, config=self.memory_config
        )
        # Return the content of the response
        return response
    def handle_teaching_staff(self, user_input: Dict[str, str]) -> str:
        reasoning_chain, response_chain = self.get_chain("teaching_staff")

        reasoning_output: AIMessage = reasoning_chain.invoke(
            {"user_input": user_input["user_input"], "chat_history": self.memory.get_session_history(self.user_id, self.conversation_id).messages}
        )

        response: AIMessage = response_chain.invoke(
            {"user_input": user_input["user_input"], "chat_history": self.memory.get_session_history(self.user_id, self.conversation_id).messages, **reasoning_output}, config=self.memory_config
        )
        return response
    def handle_grade_report(self, user_input: Dict[str, str]) -> str:
        reasoning_chain, response_chain = self.get_chain("grade_report")

        reasoning_output: AIMessage = reasoning_chain.invoke(
            {"user_input": user_input["user_input"], "chat_history": self.memory.get_session_history(self.user_id, self.conversation_id).messages}
        )

        response: AIMessage = response_chain.invoke(
            {"user_input": user_input["user_input"], "chat_history": self.memory.get_session_history(self.user_id, self.conversation_id).messages, **reasoning_output}, config=self.memory_config
        )
        return response
    def handle_generic_chat(self, user_input: Dict[str, str]) -> str:
        _, response_chain = self.get_chain("generic_chat")

        response = response_chain.invoke(
            {"user_input": user_input["user_input"], "chat_history": self.memory.get_session_history(self.user_id, self.conversation_id).messages}, config=self.memory_config
        )
        return response
    def handle_notes(self, user_input: Dict[str, str]) -> str:
        agent = self.get_agent("notes")
        response = agent.invoke(
            {
                "user_input": user_input["user_input"],
                "user_id": self.user_id,
                "chat_history": self.memory.get_session_history(self.user_id, self.conversation_id).messages,
            },
            config=self.memory_config,
        )
        return response["output"]
    def handle_unknown_intent(self, user_input: Dict[str, str]) -> str:
        """Handle unknown intents by providing a generic response.
        Args:
            user_input: The input text from the user.
        Returns:
            The content of the response after processing through the new chain.
        """
        possible_intention = [
            "Generic Chat",
            "Course Report",
            "Deadline",
            "Create Note",
            "Read Note",
            "Update Note",
            "Delete Note",
            "Grade Report",
            "IT Support",
            "Policy",
            "Teaching Staff",
        ]
        generic_chat_reasoning_chain, _ = self.get_chain("generic_chat")
        input_message = {}
        input_message["user_input"] = user_input["user_input"]
        input_message["possible_intentions"] = possible_intention
        input_message["chat_history"] = self.memory.get_session_history(
            self.user_id, self.conversation_id
        ).messages
        reasoning_output1 = generic_chat_reasoning_chain.invoke(input_message)
        if reasoning_output1.generic_chat:
            print("Generic Chat")
            return self.handle_generic_chat(user_input)
        else:
            router_reasoning_chain2, _ = self.get_chain("router")
            reasoning_output2 = router_reasoning_chain2.invoke(input_message)
            new_intention = reasoning_output2.intent
            print("New Intention:", new_intention)
            new_handler = self.intent_handlers.get(new_intention)
            return new_handler(user_input)
    def save_memory(self) -> None:
        """Save the current memory state of the bot."""
        self.memory.save_session_history(self.user_id, self.conversation_id)
    def process_user_input(self, user_input: Dict[str, str]) -> str:
        """Process user input by routing through the appropriate intention pipeline."""
        
        # Add chat history to user input
        user_input["chat_history"] = self.memory.get_session_history(
            self.user_id, self.conversation_id
        ).messages

        # Classify intent
        intention = self.get_user_intent(user_input)
        print("Intent:", intention)

        # Route to handler
        handler = self.intent_handlers.get(intention, self.handle_unknown_intent)
        return handler(user_input)