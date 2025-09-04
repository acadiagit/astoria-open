# Path: astoria_open/app/rag_components/agent_setup.py
# Filename: agent_setup.py
# Purpose: Creates the final, production-ready SQL agent for the web application.

import os
import logging
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

def create_maritime_agent() -> AgentExecutor:
    """
    Creates the final, specialized SQL agent with a rule-based prompt that
    is loaded from an external file.
    """
    logger.info("--- Creating the specialized SQL agent for the application... ---")
    load_dotenv()

    llm = ChatGroq(
        model_name="llama3-70b-8192", 
        temperature=0,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        max_retries=2,
        request_timeout=30
    )

    db_uri = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}".format(
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB')
    )
    
    db = SQLDatabase.from_uri(
        db_uri, 
        include_tables=['vessels', 'voyages', 'crew', 'maintenance']
    )
    
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    # Load the system prompt from the external text file
    prompt_path = "/Users/hugodiaz/Astoria/hf_spaces/astoria_open/prompts/system_prompt.txt"
    with open(prompt_path, "r") as f:
        system_prompt_text = f.read()
    
    system_message = SystemMessage(content=system_prompt_text)
    
    prompt = ChatPromptTemplate.from_messages([
        system_message,
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
        return_intermediate_steps=True # Crucial for extracting the SQL query
    )

    tool_names = [tool.name for tool in agent_executor.tools]
    print(f"✅ Production Agent initialized with tools: {tool_names}")
    
    return agent_executor

#end-of-script
