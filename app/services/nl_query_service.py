# filename: app/services/nl_query_service.py
# Purpose: Service to handle orchestration of NL queries.

import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def process_nl_query(nl_service, agent_executor, nl_query: str, page: int = 1):
    """
    Orchestrates processing a natural language query.
    It uses the NL2SQLService which can route to rule-based methods or fall back to an LLM agent.
    """
    logger.info(f"Processing query with NL2SQL Service: '{nl_query}'")
    try:
        # The NL2SQL Service will handle routing, processing, and caching.
        # We pass the agent_executor to it in case it needs to fall back to the agent.
        # Note: This requires a small modification to your NL2SQLService to accept the agent.
        # For now, we assume it decides between its internal rule-based and LLM methods.
        
        # Let's assume the nl_service has access to the agent if needed, 
        # or we decide here based on its initial analysis.
        
        # Here, we directly use the powerful nl_service to handle the entire flow.
        result = nl_service.process_query(nl_query)
        
        if not result.success and not result.results:
            logger.warning(f"NL2SQL processing failed for query: {nl_query}. Errors: {result.errors}")
            # Optionally, you could try the agent directly here as a final fallback
            # response = agent_executor.invoke({"input": nl_query})
            # return {"source": "agent_fallback", "response": response}
            raise HTTPException(status_code=500, detail=f"Failed to process query. Errors: {result.errors}")

        return {
            "source": result.processing_method,
            "nl_query": result.nl_query,
            "sql_query": result.sql_query,
            "results": result.results,
            "nl_response": result.nl_response,
            "cached": result.cached
        }

    except Exception as e:
        logger.error(f"Error in process_nl_query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def check_service_health():
    """Placeholder for a more detailed health check."""
    # This could be expanded to check DB connection, LLM connectivity, etc.
    return {"status": "ok", "services": ["nl_query_service"]}
#--end-of-file
