# Path: /astoria_rag_hub/app/services/nl_query_service.py
# Filename: nl_query_service.py
# Purpose: Handles natural language queries by invoking the LangChain maritime agent.

import logging
from app.rag_components.agent_setup import create_maritime_agent

logger = logging.getLogger(__name__)

def process_nl_query(nl_query: str):
    """
    Processes a natural language query using the LangChain maritime agent,
    which has access to both the SQL database and the RAG vector store.
    
    Args:
        nl_query (str): The user's question in plain English.
        
    Returns:
        dict: A dictionary containing the status and the final response.
    """
    logger.info(f"Processing query with LangChain agent: '{nl_query}'")
    try:
        # 1. Create the agent executor. This function builds the agent,
        #    the LLM, and all its tools.
        agent_executor = create_maritime_agent()

        # 2. Invoke the agent with the user's query. The agent will decide
        #    which tools to use (SQL, RAG, or both).
        result = agent_executor.invoke({"input": nl_query})
        
        # 3. Extract the final answer from the agent's output.
        nl_response = result.get("output", "No definitive answer could be generated.")

        # 4. Return a success response. The intermediate steps (like the SQL query)
        #    will be visible in the server log because of the 'verbose=True' setting.
        return {
            'status': 'success',
            'nl_query': nl_query,
            'nl_response': nl_response,
        }

    except Exception as e:
        logger.error(f"An error occurred during agent execution: {e}", exc_info=True)
        return {
            'status': 'error',
            'message': 'An error occurred while processing your query with the AI agent.'
        }

#end-of-file
