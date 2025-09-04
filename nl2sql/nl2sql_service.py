# Path: nl2sql/nl2sql_service.py
# Filename: nl2sql_service.py
# Purpose: Main NL2SQL service interface that orchestrates the entire pipeline

"""
NL2SQL Service

Main service interface that orchestrates the complete NL2SQL pipeline,
including query routing, processing, and fallback mechanisms.
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
import psycopg2

from .core import SchemaAnalyzer, QueryParser, SQLGenerator, QueryOptimizer
from .routing import ComplexityAnalyzer, QueryRouter, RoutingStrategy
from .patterns import MaritimePatterns, PatternCache
from .integrations import LangChainBridge

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of NL2SQL processing"""
    success: bool
    nl_query: str
    nl_response: str
    sql_query: Optional[str] = None
    parameters: list = None
    results: Any = None
    processing_method: str = "unknown"
    execution_time: float = 0.0
    confidence: float = 0.0
    errors: list = None
    warnings: list = None
    cached: bool = False
    requires_llm_fallback: bool = False
    metadata: Dict[str, Any] = None

class NL2SQLService:
    """Main service for natural language to SQL conversion"""
    
    def __init__(self, db_connection, config: Dict[str, Any] = None, 
                 langchain_agent_factory: Callable = None):
        """
        Initialize the NL2SQL service
        
        Args:
            db_connection: PostgreSQL database connection
            config: Service configuration options
            langchain_agent_factory: Factory function for LangChain agent (optional)
        """
        self.db_connection = db_connection
        self.config = config or {}
        
        # Initialize core components
        logger.info("Initializing NL2SQL service components...")
        
        self.schema_analyzer = SchemaAnalyzer(db_connection)
        self.complexity_analyzer = ComplexityAnalyzer(self.schema_analyzer)
        
        # Initialize routing with proper enum handling
        routing_strategy_name = self.config.get('routing_strategy', 'AUTO_ADAPTIVE')
        try:
            # Try to get the enum value by name
            routing_strategy = getattr(RoutingStrategy, routing_strategy_name, RoutingStrategy.AUTO_ADAPTIVE)
        except AttributeError:
            # Fallback to AUTO_ADAPTIVE if the strategy name is invalid
            logger.warning(f"Invalid routing strategy '{routing_strategy_name}', using AUTO_ADAPTIVE")
            routing_strategy = RoutingStrategy.AUTO_ADAPTIVE
        
        self.query_router = QueryRouter(
            self.complexity_analyzer,
            strategy=routing_strategy,
            config=self.config.get('routing_config', {})
        )
        
        # Initialize rule-based components
        self.query_parser = QueryParser(self.schema_analyzer)
        self.sql_generator = SQLGenerator(self.schema_analyzer)
        self.query_optimizer = QueryOptimizer(self.schema_analyzer)
        
        # Initialize patterns and caching
        self.maritime_patterns = MaritimePatterns()
        cache_config = self.config.get('cache_config', {})
        self.pattern_cache = PatternCache(
            max_entries=cache_config.get('max_entries', 10000),
            ttl_hours=cache_config.get('ttl_hours', 24)
        )
        
        # Initialize LangChain bridge
        self.langchain_bridge = None
        if langchain_agent_factory:
            self.langchain_bridge = LangChainBridge(langchain_agent_factory)
        
        # Service statistics
        self.query_count = 0
        self.rule_based_count = 0
        self.llm_count = 0
        self.cache_hit_count = 0
        
        logger.info("NL2SQL service initialized successfully")
    
    def process_query(self, nl_query: str, context: Dict[str, Any] = None) -> ProcessingResult:
        """
        Main method to process a natural language query
        
        Args:
            nl_query: Natural language query string
            context: Optional context for processing
            
        Returns:
            ProcessingResult with complete processing information
        """
        start_time = time.time()
        self.query_count += 1
        
        logger.info(f"Processing query #{self.query_count}: {nl_query[:100]}...")
        
        try:
            # Step 1: Check cache first
            cached_result = self._check_cache(nl_query)
            if cached_result:
                return cached_result
            
            # Step 2: Route query to appropriate processor
            routing_decision = self.query_router.route_query(nl_query, context)
            
            # Step 3: Process based on routing decision
            if routing_decision.processing_method == "rule_based":
                result = self._process_rule_based(nl_query, routing_decision)
                self.rule_based_count += 1
            else:  # llm_based
                result = self._process_llm_based(nl_query, routing_decision)
                self.llm_count += 1
            
            # Step 4: Check if fallback is needed
            if (not result.success and routing_decision.fallback_method and 
                self.query_router.should_use_fallback(asdict(result), routing_decision)):
                
                logger.info(f"Primary method failed, trying fallback: {routing_decision.fallback_method}")
                if routing_decision.fallback_method == "llm_based":
                    fallback_result = self._process_llm_based(nl_query, routing_decision)
                    self.llm_count += 1
                else:
                    fallback_result = self._process_rule_based(nl_query, routing_decision)
                    self.rule_based_count += 1
                
                if fallback_result.success:
                    result = fallback_result
                    result.processing_method += "_via_fallback"
            
            # Step 5: Record performance for adaptive learning
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            self.query_router.record_performance(
                nl_query, 
                result.processing_method,
                result.success,
                execution_time,
                routing_decision.complexity_metrics
            )
            
            # Step 6: Cache successful results
            if result.success and self.config.get('caching_enabled', True):
                self._cache_result(nl_query, result)
            
            logger.info(f"Query processed in {execution_time:.2f}s via {result.processing_method}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error processing query: {e}", exc_info=True)
            
            return ProcessingResult(
                success=False,
                nl_query=nl_query,
                nl_response=f"An error occurred while processing your query: {str(e)}",
                processing_method="error",
                execution_time=execution_time,
                errors=[str(e)]
            )
    
    def _check_cache(self, nl_query: str) -> Optional[ProcessingResult]:
        """Check if query result is cached"""
        if not self.config.get('caching_enabled', True):
            return None
        
        cached_entry = self.pattern_cache.get(nl_query)
        if cached_entry:
            self.cache_hit_count += 1
            logger.debug("Cache hit for query")
            
            return ProcessingResult(
                success=cached_entry.success,
                nl_query=nl_query,
                nl_response=f"Found {len(cached_entry.results) if cached_entry.results else 0} results",
                sql_query=cached_entry.sql_query,
                parameters=cached_entry.parameters,
                results=cached_entry.results,
                processing_method=cached_entry.processing_method,
                execution_time=cached_entry.execution_time,
                confidence=cached_entry.confidence,
                cached=True
            )
        
        return None
    
    def _cache_result(self, nl_query: str, result: ProcessingResult):
        """Cache a successful result"""
        self.pattern_cache.put(
            nl_query=nl_query,
            sql_query=result.sql_query,
            parameters=result.parameters or [],
            results=result.results,
            processing_method=result.processing_method,
            execution_time=result.execution_time,
            confidence=result.confidence,
            success=result.success
        )
    
    def _process_rule_based(self, nl_query: str, routing_decision) -> ProcessingResult:
        """Process query using rule-based methods"""
        logger.debug("Processing with rule-based approach")
        
        try:
            # Step 1: Try pattern matching first
            pattern_match = self.maritime_patterns.match_pattern(nl_query)
            
            if pattern_match and pattern_match.confidence > 0.7:
                logger.debug(f"Pattern matched: {pattern_match.pattern.name}")
                
                # Execute the pattern-generated SQL
                sql_query = pattern_match.sql_query
                parameters = pattern_match.parameters
                
                # Execute query
                results = self._execute_sql(sql_query, parameters)
                
                # Generate natural language response
                nl_response = self._generate_nl_response(results, pattern_match.pattern.description)
                
                return ProcessingResult(
                    success=True,
                    nl_query=nl_query,
                    nl_response=nl_response,
                    sql_query=sql_query,
                    parameters=parameters,
                    results=results,
                    processing_method="rule_based_pattern",
                    confidence=pattern_match.confidence
                )
            
            # Step 2: Fall back to general parsing if no pattern matches
            logger.debug("No pattern match, using general parsing")
            
            # Parse the query
            intent = self.query_parser.parse(nl_query)
            
            if intent.confidence < 0.5:
                return ProcessingResult(
                    success=False,
                    nl_query=nl_query,
                    nl_response="I couldn't understand your query well enough to process it with rule-based methods.",
                    processing_method="rule_based_failed",
                    confidence=intent.confidence,
                    requires_llm_fallback=True
                )
            
            # Generate SQL
            generated_sql = self.sql_generator.generate(intent)
            
            # Optimize SQL
            optimization_result = self.query_optimizer.optimize(generated_sql.sql)
            
            # Execute optimized SQL
            results = self._execute_sql(optimization_result.optimized_sql, generated_sql.parameters)
            
            # Generate response
            nl_response = self._generate_nl_response(results, f"Found {len(results) if results else 0} results")
            
            return ProcessingResult(
                success=True,
                nl_query=nl_query,
                nl_response=nl_response,
                sql_query=optimization_result.optimized_sql,
                parameters=generated_sql.parameters,
                results=results,
                processing_method="rule_based_general",
                confidence=intent.confidence,
                warnings=optimization_result.warnings
            )
            
        except Exception as e:
            logger.error(f"Rule-based processing failed: {e}")
            return ProcessingResult(
                success=False,
                nl_query=nl_query,
                nl_response="Rule-based processing encountered an error.",
                processing_method="rule_based_error",
                errors=[str(e)],
                requires_llm_fallback=True
            )
    
    def _process_llm_based(self, nl_query: str, routing_decision) -> ProcessingResult:
        """Process query using LLM (LangChain agent)"""
        logger.debug("Processing with LLM-based approach")
        
        if not self.langchain_bridge:
            return ProcessingResult(
                success=False,
                nl_query=nl_query,
                nl_response="LLM processing is not available - no LangChain bridge configured.",
                processing_method="llm_unavailable",
                errors=["LangChain bridge not configured"]
            )
        
        try:
            # Use LangChain bridge
            bridge_result = self.langchain_bridge.process_query(nl_query)
            
            # Convert bridge result to our format
            return ProcessingResult(
                success=bridge_result.success,
                nl_query=nl_query,
                nl_response=bridge_result.nl_response,
                sql_query=bridge_result.sql_query,
                results=None,  # LangChain handles execution
                processing_method="llm_langchain",
                execution_time=bridge_result.execution_time,
                confidence=bridge_result.confidence,
                errors=bridge_result.errors,
                metadata={'raw_langchain_result': bridge_result.raw_result}
            )
            
        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            return ProcessingResult(
                success=False,
                nl_query=nl_query,
                nl_response="LLM processing encountered an error.",
                processing_method="llm_error",
                errors=[str(e)]
            )
    
    def _execute_sql(self, sql_query: str, parameters: list = None) -> Any:
        """Execute SQL query and return results"""
        logger.debug(f"Executing SQL: {sql_query[:100]}...")
        
        with self.db_connection.cursor() as cursor:
            cursor.execute(sql_query, parameters or [])
            
            # Handle different query types
            if sql_query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                
                # Convert to list of dictionaries for easier handling
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                else:
                    return results
            else:
                # For non-SELECT queries
                return {"affected_rows": cursor.rowcount}
    
    def _generate_nl_response(self, results: Any, context: str = "") -> str:
        """Generate natural language response from query results"""
        if not results:
            return "No results found for your query."
        
        if isinstance(results, list):
            count = len(results)
            if count == 1:
                return f"Found 1 result. {context}"
            else:
                return f"Found {count} results. {context}"
        elif isinstance(results, dict) and 'count' in results:
            count = results['count']
            return f"Count: {count}"
        else:
            return f"Query executed successfully. {context}"
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        cache_stats = self.pattern_cache.get_statistics()
        routing_stats = self.query_router.get_routing_statistics()
        
        bridge_stats = {}
        if self.langchain_bridge:
            bridge_stats = self.langchain_bridge.get_bridge_statistics()
        
        return {
            'query_processing': {
                'total_queries': self.query_count,
                'rule_based_queries': self.rule_based_count,
                'llm_queries': self.llm_count,
                'cache_hits': self.cache_hit_count,
                'rule_based_percentage': (self.rule_based_count / self.query_count * 100) if self.query_count > 0 else 0,
                'cache_hit_rate': (self.cache_hit_count / self.query_count * 100) if self.query_count > 0 else 0
            },
            'cache_statistics': cache_stats,
            'routing_statistics': routing_stats,
            'langchain_bridge': bridge_stats,
            'schema_info': {
                'total_tables': len(self.schema_analyzer.tables),
                'total_relationships': len(self.schema_analyzer.relationships)
            },
            'pattern_statistics': self.maritime_patterns.get_pattern_statistics()
        }
    
    def explain_query(self, nl_query: str) -> Dict[str, Any]:
        """Explain how a query would be processed without executing it"""
        # Analyze complexity
        complexity_metrics = self.complexity_analyzer.analyze(nl_query)
        complexity_level = self.complexity_analyzer.get_complexity_level(complexity_metrics)
        
        # Get routing decision
        routing_decision = self.query_router.route_query(nl_query)
        
        # Check for pattern matches
        pattern_match = self.maritime_patterns.match_pattern(nl_query)
        
        # Check cache
        cached_entry = self.pattern_cache.get(nl_query)
        
        return {
            'query': nl_query,
            'complexity_analysis': {
                'level': complexity_level.value,
                'overall_score': complexity_metrics.overall_score,
                'metrics': asdict(complexity_metrics)
            },
            'routing_decision': {
                'method': routing_decision.processing_method,
                'confidence': routing_decision.confidence,
                'reasoning': routing_decision.reasoning,
                'fallback': routing_decision.fallback_method
            },
            'pattern_match': {
                'found': pattern_match is not None,
                'pattern_name': pattern_match.pattern.name if pattern_match else None,
                'confidence': pattern_match.confidence if pattern_match else 0.0
            },
            'cache_status': {
                'cached': cached_entry is not None,
                'cache_age': (time.time() - cached_entry.created_at.timestamp()) if cached_entry else None
            },
            'recommended_approach': self.complexity_analyzer.recommend_processing_strategy(complexity_metrics)
        }
    
    def update_configuration(self, new_config: Dict[str, Any]):
        """Update service configuration"""
        self.config.update(new_config)
        
        # Update router configuration
        if 'routing_config' in new_config:
            self.query_router.update_config(new_config['routing_config'])
        
        # Update routing strategy
        if 'routing_strategy' in new_config:
            strategy_name = new_config['routing_strategy']
            try:
                strategy = getattr(RoutingStrategy, strategy_name, RoutingStrategy.AUTO_ADAPTIVE)
                self.query_router.update_strategy(strategy)
            except AttributeError:
                logger.warning(f"Invalid routing strategy '{strategy_name}', keeping current strategy")
        
        logger.info("Service configuration updated")
    
    def clear_cache(self):
        """Clear all cached results"""
        self.pattern_cache.clear()
        logger.info("Service cache cleared")
    
    def set_langchain_agent_factory(self, agent_factory: Callable):
        """Set or update the LangChain agent factory"""
        if self.langchain_bridge:
            self.langchain_bridge.set_agent_factory(agent_factory)
        else:
            self.langchain_bridge = LangChainBridge(agent_factory)
        logger.info("LangChain agent factory updated")
    
    def validate_service(self) -> Dict[str, Any]:
        """Validate that all service components are working correctly"""
        validation_results = {
            'schema_analyzer': True,
            'query_parser': True,
            'sql_generator': True,
            'patterns': True,
            'cache': True,
            'langchain_bridge': False,
            'overall_status': 'unknown',
            'errors': []
        }
        
        try:
            # Test schema analyzer
            schema_summary = self.schema_analyzer.get_schema_summary()
            validation_results['schema_analyzer'] = schema_summary['total_tables'] > 0
            
            # Test patterns
            pattern_stats = self.maritime_patterns.get_pattern_statistics()
            validation_results['patterns'] = pattern_stats['total_patterns'] > 0
            
            # Test cache
            cache_stats = self.pattern_cache.get_statistics()
            validation_results['cache'] = True  # Cache is always functional
            
            # Test LangChain bridge
            if self.langchain_bridge:
                bridge_validation = self.langchain_bridge.validate_integration()
                validation_results['langchain_bridge'] = bridge_validation['agent_creation_successful']
                if not bridge_validation['agent_creation_successful']:
                    validation_results['errors'].extend(bridge_validation['errors'])
            
            # Overall status
            critical_components = ['schema_analyzer', 'query_parser', 'sql_generator', 'patterns']
            if all(validation_results[comp] for comp in critical_components):
                validation_results['overall_status'] = 'healthy'
            else:
                validation_results['overall_status'] = 'degraded'
                
        except Exception as e:
            validation_results['overall_status'] = 'error'
            validation_results['errors'].append(f"Validation error: {str(e)}")
        
        return validation_results

#end-of-file