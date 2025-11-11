# filename: nl2sql/routing/query_router.py
# Purpose: Routes queries based on complexity analysis.

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .complexity_analyzer import ComplexityAnalyzer, QueryComplexity, ComplexityMetrics

logger = logging.getLogger(__name__)

class RoutingStrategy(Enum):
    HYBRID_PREFER_RULES = "HYBRID_PREFER_RULES"
    HYBRID_PREFER_LLM = "HYBRID_PREFER_LLM"
    RULES_ONLY = "RULES_ONLY"
    LLM_ONLY = "LLM_ONLY"

@dataclass
class RoutingDecision:
    processing_method: str
    confidence: float
    reasoning: str
    fallback_method: Optional[str] = None
    complexity_metrics: Optional[ComplexityMetrics] = None

class QueryRouter:
    """Intelligently routes queries to the appropriate processing system."""
    
    def __init__(self, complexity_analyzer: ComplexityAnalyzer, 
                 strategy: RoutingStrategy = RoutingStrategy.HYBRID_PREFER_RULES,
                 config: Dict[str, Any] = None):
        self.complexity_analyzer = complexity_analyzer
        self.strategy = strategy
        self.config = config or {}
        self.routing_stats = {'rule_based': 0, 'llm_based': 0}
        logger.info(f"QueryRouter initialized with strategy: {self.strategy.name}")

    def route_query(self, nl_query: str, context: Dict = None) -> RoutingDecision:
        """
        Determines the best processing method for a given query.
        
        --- CORRECTED LOGIC ---
        This now correctly calls the simplified analyze() method and uses its
        direct output, instead of calling a non-existent method.
        """
        # The new analyze() method directly returns the complexity level Enum
        complexity_level = self.complexity_analyzer.analyze(nl_query)
        
        if self.strategy == RoutingStrategy.RULES_ONLY:
            self.routing_stats['rule_based'] += 1
            return RoutingDecision("rule_based", 1.0, "Strategy is RULES_ONLY")

        if self.strategy == RoutingStrategy.LLM_ONLY:
            self.routing_stats['llm_based'] += 1
            return RoutingDecision("llm_based", 1.0, "Strategy is LLM_ONLY")

        # For hybrid strategies, use the complexity level
        if complexity_level == QueryComplexity.COMPLEX:
            self.routing_stats['llm_based'] += 1
            return RoutingDecision(
                "llm_based", 0.95, 
                "Query contains analytical keywords.",
                fallback_method="rule_based"
            )
        else: # SIMPLE or MODERATE
            self.routing_stats['rule_based'] += 1
            return RoutingDecision(
                "rule_based", 0.90, 
                "Query appears to be a simple, factual question.",
                fallback_method="llm_based"
            )

    def should_use_fallback(self, result, decision):
        # Placeholder for more complex fallback logic
        return True

    def record_performance(self, nl_query, method, success, time, metrics):
        # Placeholder for performance logging
        pass

    def get_routing_statistics(self):
        return self.routing_stats

    def update_config(self, new_config):
        self.config.update(new_config)

    def update_strategy(self, new_strategy: RoutingStrategy):
        self.strategy = new_strategy
        logger.info(f"QueryRouter strategy updated to: {self.strategy.name}")
#--end-of-file--
