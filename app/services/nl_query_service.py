# Filename: app/services/nl_query_service.py
# Purpose: Service layer for handling natural language queries.

import logging
from langchain.agents import AgentExecutor

logger = logging.getLogger(__name__)

def process_nl_query(agent_executor: AgentExecutor, nl_query: str, page: int = 1):
    """
    Processes the natural language query using the pre-loaded agent executor.
    """
    logger.info(f"Processing query with pre-loaded agent: '{nl_query}'")
    try:
        # This is the core logic that uses the agent.
        # Ensure this matches how you want to call the agent and handle its response.
        response = agent_executor.invoke({"input": nl_query})

        # Example of how you might extract the final answer and intermediate SQL
        # You may need to adjust this based on your agent's specific return format.
        narrative = response.get("output", "No narrative generated.")
        sql_query = "Could not extract SQL query."
        if "intermediate_steps" in response and response["intermediate_steps"]:
            # This attempts to get the second element (the SQL query) from the last tool call tuple
            sql_query = response["intermediate_steps"][-1][1]

        return {"narrative": narrative, "sql_query": sql_query}

    except Exception as e:
        logger.error(f"Error during agent invocation: {e}", exc_info=True)
        return {"error": f"An error occurred while processing your query: {e}"}

def check_service_health(service_name: str = "all"):
    """Checks the health of the application's services."""
    # This is a placeholder for your actual health check logic.
    if service_name == "all":
        return {"status": "ok", "services": ["database", "llm_agent"]}
    else:
        return {"status": "ok", "service": service_name}

# -- end of file --
