# Path: /astoria-open/app/rag_components/agent_setup.py
# Filename: agent_setup.py

import os
import logging
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_groq import ChatGroq
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import ChatPromptTemplate

from app.rag_components.vector_store import get_vector_store

logger = logging.getLogger(__name__)

def create_maritime_agent() -> AgentExecutor:
    """
    Creates the main LangChain agent with access to the SQL database
    and the RAG vector store.
    """
    logger.info("Creating the maritime agent...")

    llm = ChatGroq(
        model_name="llama3-8b-8192",
        temperature=0,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    db_uri = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}".format(
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB')
    )
    db = SQLDatabase.from_uri(db_uri)

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    sql_tool = tools[0] # The main query tool

    vector_store = get_vector_store()
    retriever = vector_store.as_retriever()
    retriever_tool = create_retriever_tool(
        retriever,
        "unstructured_vector_database_tool",
        "Use this for queries about historical context, descriptions, events, and interpretive questions."
    )

    prompt_template = """
    You are a helpful maritime history research assistant.
    Your goal is to answer the user's question directly and concisely.

    You have access to the following tools:
    {tools}

    IMPORTANT SCHEMA HINTS:
    - The 'vessels' table contains a column named 'name' for the vessel's official name.
    - The 'vessels' table contains a column named 'vessel_type' to describe the type of vessel (e.g., 'schooner').

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the SQL query to execute
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought:{agent_scratchpad}
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)

    all_tools = [sql_tool, retriever_tool]
    agent = create_react_agent(llm, all_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)

    logger.info("Maritime agent created successfully.")
    return agent_executor

#end-of-file
