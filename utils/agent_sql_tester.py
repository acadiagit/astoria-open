# [utils/agent_sql_tester.py]
# Purpose: A standalone script to test the agent's ability to handle multi-step, conversational SQL queries.

import os
import pprint
import sys
from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def run_conversational_test():
    """
    Tests the agent's ability to deconstruct a conversational query into a
    multi-step plan, now with the added context of database table comments.
    """
    print("--- Loading environment variables from .env file... ---")
    load_dotenv()

    print("--- Initializing LLM and Database connection... ---")
    # Using a current, powerful Llama 3 model from Groq.
    try:
        llm = ChatGroq(
            model_name="llama3-70b-8192", # Using Llama 3 70B
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            max_retries=2,
            request_timeout=30
        )
    except Exception as e:
        print(f"🛑 FAILED to initialize Groq LLM: {e}")
        return

    # Added "?sslmode=require" for a stable Supabase connection with SQLAlchemy.
    try:
        db_uri = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require".format(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        
        db = SQLDatabase.from_uri(
            db_uri, 
            include_tables=['vessels', 'voyages', 'crew', 'maintenance'] # Hardcoded for this test
        )
        
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    except Exception as e:
        print(f"🛑 FAILED to connect to SQL database: {e}")
        return

    system_prompt = """
    You are a powerful SQL agent. Your job is to interact with a PostgreSQL database to answer user questions.
    Given a user's input, you must create a logical plan, use your tools, and then respond with the result.
    Always inspect the schema of a table before you try to query it.

    Here are examples of how to use your tools:

    ---
    EXAMPLE 1
    Question: List all tables in the database.
    Thought: The user wants to see all the tables. The `sql_db_list_tables` tool is designed for this. I should call it.
    Action: sql_db_list_tables
    Action Input: ""
    ---
    EXAMPLE 2
    Question: Which 3 vessels are schooners?
    Thought: The user is asking for specific data about vessels. I need to query the database.
    First, I need to see what tables are available to find one related to 'vessels'.
    Action: sql_db_list_tables
    Action Input: ""
    Observation: crew, documents, maintenance, maritime_data, profiles, query_history, simple_test, vessels, voyages
    Thought: The 'vessels' table seems most relevant. Now I need to inspect its schema to find a column related to vessel type.
    Action: sql_db_schema
    Action Input: "vessels"
    Observation: CREATE TABLE vessels (id SERIAL PRIMARY KEY, name TEXT NOT NULL, vessel_type TEXT, ...)
    Thought: The schema shows a 'vessel_type' column. I can now write a SQL query to find the schooners.
    Action: sql_db_query
    Action Input: "SELECT name, vessel_type FROM vessels WHERE vessel_type = 'Schooner' LIMIT 3"
    ---
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    print("--- Creating the specialized SQL agent with enhanced prompt... ---")
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        prompt=prompt,
        verbose=True,
        agent_type="openai-tools", # This is a standard agent type, not specific to OpenAI
        handle_parsing_errors=True
    )

    test_query = "Which 3 vessels are schooners?"
    print(f"\n--- Running conversational test query: '{test_query}' ---")

    try:
        result = agent_executor.invoke({"input": test_query})

        print("\n--- Full Agent Result ---")
        pprint.pprint(result)
        print("-------------------------\n")
    except Exception as e:
        print(f"🛑 FAILED during agent execution: {e}")


if __name__ == "__main__":
    run_conversational_test()

[#--end-of-file--]
