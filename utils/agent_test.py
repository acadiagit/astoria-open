# Filename: agent_test.py
# Purpose: A standalone script to test the LangChain SQL agent in isolation.

import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os

# LangChain Imports
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_agent_test():
    """
    Initializes and runs the SQL agent with a test query.
    """
    # --- 1. Load Environment Variables ---
    load_dotenv()
    logging.info("Loaded environment variables from .env file.")

    # --- 2. Create Database Connection ---
    try:
        db_uri = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        db_engine = create_engine(db_uri)
        logging.info("Successfully created SQLAlchemy database engine.")
    except Exception as e:
        logging.error(f"Failed to create database engine: {e}")
        return

    # --- 3. Define the Custom Prompt for the Agent ---
    CUSTOM_PROMPT = ChatPromptTemplate.from_messages(
        [
            ("system",
             """You are an expert PostgreSQL writer. Your ONLY job is to convert a user's question into a syntactically correct PostgreSQL query.

             - The primary table you will be querying is named "vessels".
             - Given a question, create a PostgreSQL query against the "vessels" table.
             - ONLY return the SQL query. Do not add any explanation, commentary, or markdown.
             """),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    logging.info("Custom prompt for agent is defined.")

    # --- 4. Initialize the Agent ---
    try:
        llm = ChatOllama(model="codellama", temperature=0)
        db = SQLDatabase(db_engine)
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        
        agent_executor = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=True, # Set to True to see the agent's thoughts
            agent_type="openai-tools",
            handle_parsing_errors=True,
            prompt=CUSTOM_PROMPT
        )
        logging.info("SQL Agent created successfully.")
    except Exception as e:
        logging.error(f"Failed to create agent: {e}")
        return

    # --- 5. Run the Test Query ---
    # We use the query that we know generates perfect SQL.
    test_query = "tell all you know about vessels type brig"
    logging.info(f"Invoking agent with query: '{test_query}'")
    
    try:
        result = agent_executor.invoke({"input": test_query})
        print("\n--- AGENT RESULT ---")
        print(result)
        print("--- END OF RESULT ---")
    except Exception as e:
        logging.error(f"Agent invocation failed: {e}", exc_info=True)


if __name__ == "__main__":
    run_agent_test()

#--end-of-file
