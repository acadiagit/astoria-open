# Path: nl2sql/integrations/langchain_bridge.py
# Filename: langchain_bridge.py
# Purpose: Bridge to integrate with existing LangChain agent system

"""
LangChain Bridge

Provides seamless integration with the existing LangChain-based
maritime agent system for fallback processing.
"""

import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BridgeResult:
    """Result from LangChain bridge processing"""
    success: bool
    sql_query: Optional[str]
    nl_response: str
    execution_time: float
    confidence: float
    errors: list
    raw_result: Dict[str, Any]

class LangChainBridge:
    """Bridge to existing LangChain maritime agent"""
    
    def __init__(self, agent_factory: Callable = None):
        """
        Initialize bridge with agent factory function
        
        Args:
            agent_factory: Function that creates/returns the LangChain agent
                          (should be your create_maritime_agent function)
        """
        self.agent_factory = agent_factory
        self._agent_cache = None
        self.call_count = 0
        self.error_count = 0
        
    def process_query(self, nl_query: str, context: Dict[str, Any] = None) -> BridgeResult:
        """
        Process query using existing LangChain agent
        
        Args:
            nl_query: Natural language query
            context: Additional context for processing
            
        Returns:
            BridgeResult with processing outcome
        """
        import time
        start_time = time.time()
        
        try:
            self.call_count += 1
            logger.info(f"Processing query via LangChain bridge: {nl_query[:50]}...")
            
            # Get or create agent
            agent_executor = self._get_agent()
            
            # Invoke the agent with the query
            result = agent_executor.invoke({"input": nl_query})
            
            # Extract information from result
            sql_query = self._extract_sql_query(result)
            nl_response = result.get("output", "No response generated")
            
            execution_time = time.time() - start_time
            
            # Determine success and confidence
            success = self._determine_success(result, sql_query)
            confidence = self._calculate_confidence(result, success, execution_time)
            
            logger.info(f"LangChain processing completed in {execution_time:.2f}s")
            
            return BridgeResult(
                success=success,
                sql_query=sql_query,
                nl_response=nl_response,
                execution_time=execution_time,
                confidence=confidence,
                errors=[],
                raw_result=result
            )
            
        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time
            error_msg = f"LangChain bridge error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return BridgeResult(
                success=False,
                sql_query=None,
                nl_response=f"Error processing query: {str(e)}",
                execution_time=execution_time,
                confidence=0.0,
                errors=[error_msg],
                raw_result={}
            )
    
    def _get_agent(self):
        """Get agent instance (cached or new)"""
        if self._agent_cache is None:
            if self.agent_factory is None:
                raise ValueError("No agent factory provided to LangChain bridge")
            
            logger.debug("Creating new LangChain agent instance")
            self._agent_cache = self.agent_factory()
        
        return self._agent_cache
    
    def _extract_sql_query(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract generated SQL query from agent result"""
        sql_query = "No SQL query was generated for this request."
        
        # Check intermediate steps for SQL queries
        if "intermediate_steps" in result and result["intermediate_steps"]:
            for action, observation in result["intermediate_steps"]:
                if hasattr(action, 'tool') and action.tool == "sql_db_query":
                    sql_query = action.tool_input
                    break
        
        # Return None if no actual SQL was found
        if sql_query == "No SQL query was generated for this request.":
            return None
        
        return sql_query
    
    def _determine_success(self, result: Dict[str, Any], sql_query: Optional[str]) -> bool:
        """Determine if the processing was successful"""
        # Check if we got a meaningful response
        output = result.get("output", "")
        if not output or "error" in output.lower():
            return False
        
        # Check if SQL was generated when expected
        if sql_query is None and "query" in result.get("input", "").lower():
            return False
        
        # Check for error indicators in intermediate steps
        if "intermediate_steps" in result:
            for action, observation in result["intermediate_steps"]:
                if observation and "error" in str(observation).lower():
                    return False
        
        return True
    
    def _calculate_confidence(self, result: Dict[str, Any], success: bool, execution_time: float) -> float:
        """Calculate confidence score for the result"""
        confidence = 0.5  # Base confidence
        
        if success:
            confidence += 0.3
        
        # Boost confidence if SQL was generated
        if self._extract_sql_query(result):
            confidence += 0.15
        
        # Adjust for execution time (faster = more confident for LLM)
        if execution_time < 1.0:
            confidence += 0.05
        elif execution_time > 5.0:
            confidence -= 0.1
        
        # Check response quality
        output = result.get("output", "")
        if len(output) > 50 and "sorry" not in output.lower():
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def validate_integration(self) -> Dict[str, Any]:
        """Validate that the LangChain integration is working"""
        validation_result = {
            'agent_factory_available': self.agent_factory is not None,
            'agent_creation_successful': False,
            'test_query_successful': False,
            'errors': []
        }
        
        try:
            # Test agent creation
            if self.agent_factory:
                test_agent = self.agent_factory()
                validation_result['agent_creation_successful'] = test_agent is not None
                
                # Test simple query
                if test_agent:
                    test_result = self.process_query("How many vessels are there?")
                    validation_result['test_query_successful'] = test_result.success
                    if not test_result.success:
                        validation_result['errors'].extend(test_result.errors)
            else:
                validation_result['errors'].append("No agent factory provided")
                
        except Exception as e:
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def get_bridge_statistics(self) -> Dict[str, Any]:
        """Get statistics about bridge usage"""
        success_rate = ((self.call_count - self.error_count) / self.call_count) if self.call_count > 0 else 0
        
        return {
            'total_calls': self.call_count,
            'error_count': self.error_count,
            'success_rate': success_rate,
            'agent_cached': self._agent_cache is not None
        }
    
    def reset_cache(self):
        """Reset cached agent instance"""
        self._agent_cache = None
        logger.info("LangChain agent cache reset")
    
    def warmup(self):
        """Warm up the bridge by creating agent instance"""
        try:
            self._get_agent()
            logger.info("LangChain bridge warmed up successfully")
        except Exception as e:
            logger.error(f"Bridge warmup failed: {e}")
    
    def set_agent_factory(self, agent_factory: Callable):
        """Set or update the agent factory"""
        self.agent_factory = agent_factory
        self._agent_cache = None  # Reset cache
        logger.info("Agent factory updated")

#end-of-script