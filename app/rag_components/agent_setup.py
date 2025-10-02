# Path: astoria_open/app/rag_components/agent_setup.py
# Filename: agent_setup.py
# Purpose: Creates the final, production-ready SQL agent for the web application.

import os
import logging
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_vertexai import ChatVertexAI # Corrected: Use Vertex AI for the SQL Agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy import create_engine
# Recommended: Import a centralized function for the DB URI
# from utils.db_utils import get_database_uri 

logger = logging.getLogger(__name__)

# Recommended: Define this once in a shared utility file like utils/db_utils.py
def get_database_uri():
    """Returns the correctly formatted, stable database URI."""
    return "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require".format(
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB')
    )

def create_maritime_agent() -> AgentExecutor:
    """
    Creates the final, specialized SQL agent for the application, using Vertex AI
    and a robust, pooled database connection.
    """
    logger.info("--- Creating the specialized SQL agent for the application... ---")
    load_dotenv()

    # CORRECTED: Use the confirmed-working Vertex AI LLM for the SQL Agent
    llm = ChatVertexAI(
        model_name="gemini-2.5-flash", 
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location="us-central1",
        temperature=0,
    )

    # Use the centralized function to get the database URI
    db_uri = get_database_uri()
    
    # Create a robust, pooled engine to prevent connection drops
    engine = create_engine(
        db_uri,
        pool_pre_ping=True,  # Checks that connections are alive before use
        pool_recycle=3600,   # Recycles connections every hour
    )
    
    db = SQLDatabase(
        engine=engine,
        include_tables=['vessels', 'voyages', 'crew', 'maintenance'],
        sample_rows_in_table_info=False
    )
    
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(script_dir, '..', '..', 'prompts', 'system_prompt.txt')

    with open(prompt_path, "r") as f:
        system_prompt_text = f.read()
    
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
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )

    tool_names = [tool.name for tool in agent_executor.tools]
    print(f"✅ Production Agent initialized with tools: {tool_names}")
    
    return agent_executor

# -- end of file --
