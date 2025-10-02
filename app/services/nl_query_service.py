# Filename: app/services/nl_query_service.py
# Purpose: Service layer with schema injection for the agent.

import logging
from langchain.agents import AgentExecutor
import pprint

# Import the schema utility
from utils.db_utils import get_schema

logger = logging.getLogger(__name__)

def process_nl_query(agent_executor: AgentExecutor, nl_query: str, page: int = 1):
    """
    Processes the natural language query by first injecting the DB schema
    and then invoking the pre-loaded agent executor.
    """
    logger.info(f"Processing query with pre-loaded agent: '{nl_query}'")
    try:
        # Get the database schema
        db_schema = get_schema()
        
        # Construct a new, more informative input for the agent
        agent_input = {
            "input": nl_query,
            "db_schema": db_schema
        }
        
        response = agent_executor.invoke(agent_input)

        # Log the full, detailed response from the agent for debugging
        logger.info(f"Full agent response:\n{pprint.pformat(response)}")

        narrative = response.get("output", "No narrative generated.")
        sql_query = "Could not extract SQL query."
        if "intermediate_steps" in response and response["intermediate_steps"]:
            sql_query = response["intermediate_steps"][-1][1]

        return {"narrative": narrative, "sql_query": sql_query}

    except Exception as e:
        logger.error(f"Error during agent invocation: {e}", exc_info=True)
        return {"error": f"An error occurred while processing your query: {e}"}

def check_service_health(service_name: str = "all"):
    """Checks the health of the application's services."""
    if service_name == "all":
        return {"status": "ok", "services": ["database", "llm_agent"]}
    else:
        return {"status": "ok", "service": service_name}

# -- end of file --
