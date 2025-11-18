# Path: astoria_open/app/rag_components/agent_setup.py
# Filename: agent_setup.py
# Purpose: Creates the final, production-ready SQL agent for the web application.
# --- FINAL CORRECTED VERSION: 11/17/2025 ---

import os
import logging
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase

# --- FIX 1: Import the correct, stable Vertex AI library ---
from langchain_google_vertexai import ChatVertexAI
# --- END FIX 1 ---

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

def get_database_uri():
    """Returns the correctly formatted, stable database URI with SSL required."""
    return "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require".format(
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB')
    )

def create_maritime_agent() -> AgentExecutor:
    """
    Creates the final, specialized SQL agent for the application, using Google Gemini
    and a robust, pooled database connection.
    """
    logger.info("--- Creating the specialized SQL agent for the application... ---")
    load_dotenv()

    # --- FIX 2: Instantiate the correct LLM ---
    # This uses the stable VertexAI library and authenticates
    # with your GOOGLE_CLOUD_PROJECT and service account key.
    llm = ChatVertexAI(
        model="gemini-2.0-flash",  # The active model we corroborated
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        temperature=0,
        location="us-east1"      # The valid region we corroborated
    )
    # --- END FIX 2 ---

    db_uri = get_database_uri()
    
    engine = create_engine(
        db_uri,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    
    db = SQLDatabase(
        engine=engine,
        include_tables=['vessels', 'voyages', 'crew', 'maintenance'],
        sample_rows_in_table_info=False
    )
    
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    system_prompt_text = """
    You are an expert maritime history SQL agent. Your goal is to answer questions by generating and executing SQL queries against a PostgreSQL database.

    **Database Schema Context:**
    - The primary table is `vessels`, which contains information about ships, including `name`, `vessel_type`, and `gross_tonnage`.
    - The schema does NOT contain columns like `arrival_port`, `departure_port`, or `port_name`. Do not invent these columns.
    - If you are unsure about the available columns, use the `sql_db_schema` tool first.

    **Querying Rules:**
    1.  For analytical questions about vessel characteristics (e.g., "most common types," "average tonnage"), you MUST query the `vessels` table.
    2.  Pay close attention to the user's question to identify the correct columns and calculations needed. For "average tonnage," use the `AVG()` function on the `gross_tonnage` column.

    **IMPORTANT Rule about Ports:**
    - The user has specified that for this dataset, the only port of relevance is 'Machias'.
    - If a user's question involves voyages, logs, arrivals, or departures, you MUST assume it relates to 'Machias' and structure your query accordingly, likely by querying a `voyages` table if one exists.

    Given an input question, create a syntactically correct PostgreSQL query, execute it, and use the results to answer the question.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt_text),
        HumanMessage(content="{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors="Check your SQL query for syntax errors and ensure you are only using columns that exist in the schema.",
        return_intermediate_steps=True
    )

    tool_names = [tool.name for tool in agent_executor.tools]
    print(f"✅ Production Agent initialized with tools: {tool_names}")
    
#--end-of-file--
    return agent_executor
