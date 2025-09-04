# Path: nl2sql/routing/query_router.py
# Filename: query_router.py
# Purpose: Intelligent query routing between rule-based and LLM processing

"""
Query Router

Routes natural language queries to the most appropriate processing method
based on complexity analysis and system configuration.
"""

import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from .complexity_analyzer import ComplexityAnalyzer, QueryComplexity

logger = logging.getLogger(__name__)

class RoutingStrategy(Enum):
    RULE_BASED_ONLY = "rule_based_only"
    LLM_ONLY = "llm_only"
    HYBRID_PREFER_RULES = "hybrid_prefer_rules"
    HYBRID_PREFER_LLM = "hybrid_prefer_llm"
    AUTO_ADAPTIVE = "auto_adaptive"

@dataclass
class RoutingDecision:
    """Decision made by the router"""
    processing_method: str
    confidence: float
    reasoning: str
    fallback_method: Optional[str] = None
    complexity_metrics: Optional[Any] = None
    estimated_performance: Optional[Dict[str, Any]] = None

class QueryRouter:
    """Routes queries to appropriate processing methods"""
    
    def __init__(self, complexity_analyzer: ComplexityAnalyzer, 
                 strategy: RoutingStrategy = RoutingStrategy.AUTO_ADAPTIVE,
                 config: Dict[str, Any] = None):
        self.complexity_analyzer = complexity_analyzer
        self.strategy = strategy
        self.config = config or {}
        self.performance_history = {}
        self.routing_rules = self._build_routing_rules()
        
    def _build_routing_rules(self) -> Dict[str, Any]:
        """Build routing rules based on configuration"""
        default_thresholds = {
            'simple_threshold': 0.3,
            'moderate_threshold': 0.6,
            'ambiguity_threshold': 0.4,
            'confidence_threshold': 0.7,
            'performance_weight': 0.3,
            'accuracy_weight': 0.7
        }
        
        # Override defaults with config
        thresholds = {**default_thresholds, **self.config.get('thresholds', {})}
        
        return {
            'thresholds': thresholds,
            'fallback_enabled': self.config.get('fallback_enabled', True),
            'performance_tracking': self.config.get('performance_tracking', True),
            'adaptive_learning': self.config.get('adaptive_learning', True)
        }
    
    def route_query(self, nl_query: str, context: Dict[str, Any] = None) -> RoutingDecision:
        """Main routing method - decides how to process the query"""
        logger.debug(f"Routing query with strategy: {self.strategy.value}")
        
        # Analyze query complexity
        metrics = self.complexity_analyzer.analyze(nl_query)
        complexity_level = self.complexity_analyzer.get_complexity_level(metrics)
        
        # Get routing decision based on strategy
        if self.strategy == RoutingStrategy.RULE_BASED_ONLY:
            decision = self._route_rule_based_only(metrics, complexity_level)
        elif self.strategy == RoutingStrategy.LLM_ONLY:
            decision = self._route_llm_only(metrics, complexity_level)
        elif self.strategy == RoutingStrategy.HYBRID_PREFER_RULES:
            decision = self._route_hybrid_prefer_rules(metrics, complexity_level)
        elif self.strategy == RoutingStrategy.HYBRID_PREFER_LLM:
            decision = self._route_hybrid_prefer_llm(metrics, complexity_level)
        else:  # AUTO_ADAPTIVE
            decision = self._route_auto_adaptive(metrics, complexity_level, context)
        
        # Add complexity metrics to decision
        decision.complexity_metrics = metrics
        
        # Estimate performance
        decision.estimated_performance = self._estimate_performance(
            decision.processing_method, metrics
        )
        
        logger.info(f"Routed to {decision.processing_method} (confidence: {decision.confidence:.2f})")
        logger.debug(f"Reasoning: {decision.reasoning}")
        
        return decision
    
    def _route_rule_based_only(self, metrics, complexity_level) -> RoutingDecision:
        """Route everything to rule-based processing"""
        confidence = 1.0 - metrics.overall_score  # Lower complexity = higher confidence
        
        if complexity_level in [QueryComplexity.COMPLEX, QueryComplexity.AMBIGUOUS]:
            reasoning = f"Forced rule-based processing for {complexity_level.value} query - may have limitations"
            confidence *= 0.5  # Reduce confidence for complex queries
        else:
            reasoning = f"Rule-based processing suitable for {complexity_level.value} query"
        
        return RoutingDecision(
            processing_method="rule_based",
            confidence=confidence,
            reasoning=reasoning,
            fallback_method=None if not self.routing_rules['fallback_enabled'] else "llm_based"
        )
    
    def _route_llm_only(self, metrics, complexity_level) -> RoutingDecision:
        """Route everything to LLM processing"""
        confidence = min(0.8 + metrics.overall_score * 0.2, 1.0)  # Higher complexity = higher confidence
        
        reasoning = f"LLM processing for {complexity_level.value} query - high accuracy expected"
        
        return RoutingDecision(
            processing_method="llm_based",
            confidence=confidence,
            reasoning=reasoning,
            fallback_method=None
        )
    
    def _route_hybrid_prefer_rules(self, metrics, complexity_level) -> RoutingDecision:
        """Prefer rule-based with LLM fallback"""
        thresholds = self.routing_rules['thresholds']
        
        if complexity_level == QueryComplexity.SIMPLE:
            return RoutingDecision(
                processing_method="rule_based",
                confidence=0.9,
                reasoning="Simple query - rule-based processing preferred",
                fallback_method="llm_based"
            )
        elif complexity_level == QueryComplexity.MODERATE and metrics.ambiguity_score < thresholds['ambiguity_threshold']:
            return RoutingDecision(
                processing_method="rule_based",
                confidence=0.7,
                reasoning="Moderate complexity but low ambiguity - trying rule-based first",
                fallback_method="llm_based"
            )
        else:
            return RoutingDecision(
                processing_method="llm_based",
                confidence=0.8,
                reasoning=f"Complex or ambiguous query ({complexity_level.value}) - using LLM",
                fallback_method=None
            )
    
    def _route_hybrid_prefer_llm(self, metrics, complexity_level) -> RoutingDecision:
        """Prefer LLM with rule-based for simple cases"""
        if complexity_level == QueryComplexity.SIMPLE and metrics.overall_score < 0.2:
            return RoutingDecision(
                processing_method="rule_based",
                confidence=0.8,
                reasoning="Very simple query - rule-based processing sufficient",
                fallback_method="llm_based"
            )
        else:
            confidence = 0.85 if complexity_level in [QueryComplexity.COMPLEX, QueryComplexity.AMBIGUOUS] else 0.75
            return RoutingDecision(
                processing_method="llm_based",
                confidence=confidence,
                reasoning=f"Using LLM for {complexity_level.value} query - preferred method",
                fallback_method="rule_based" if complexity_level == QueryComplexity.MODERATE else None
            )
    
    def _route_auto_adaptive(self, metrics, complexity_level, context) -> RoutingDecision:
        """Adaptive routing based on complexity and performance history"""
        thresholds = self.routing_rules['thresholds']
        
        # Get performance history for similar queries
        historical_performance = self._get_historical_performance(metrics, context)
        
        # Base decision on complexity
        base_decision = self._get_base_routing_decision(metrics, complexity_level, thresholds)
        
        # Adjust based on historical performance
        if historical_performance:
            adjusted_decision = self._adjust_for_performance(base_decision, historical_performance)
        else:
            adjusted_decision = base_decision
        
        return adjusted_decision
    
    def _get_base_routing_decision(self, metrics, complexity_level, thresholds) -> RoutingDecision:
        """Get base routing decision based on complexity"""
        if complexity_level == QueryComplexity.SIMPLE:
            return RoutingDecision(
                processing_method="rule_based",
                confidence=0.9,
                reasoning="Simple query - rule-based processing optimal",
                fallback_method="llm_based"
            )
        elif complexity_level == QueryComplexity.MODERATE:
            if (metrics.ambiguity_score < thresholds['ambiguity_threshold'] and
                metrics.semantic_complexity < thresholds['moderate_threshold']):
                return RoutingDecision(
                    processing_method="rule_based",
                    confidence=0.7,
                    reasoning="Moderate complexity with low ambiguity - rule-based suitable",
                    fallback_method="llm_based"
                )
            else:
                return RoutingDecision(
                    processing_method="llm_based",
                    confidence=0.8,
                    reasoning="Moderate complexity with high ambiguity - LLM preferred",
                    fallback_method="rule_based"
                )
        elif complexity_level == QueryComplexity.COMPLEX:
            return RoutingDecision(
                processing_method="llm_based",
                confidence=0.85,
                reasoning="Complex query requiring sophisticated understanding",
                fallback_method=None
            )
        else:  # AMBIGUOUS
            return RoutingDecision(
                processing_method="llm_based",
                confidence=0.9,
                reasoning="Ambiguous query requiring clarification and context understanding",
                fallback_method=None
            )
    
    def _get_historical_performance(self, metrics, context) -> Optional[Dict[str, Any]]:
        """Get historical performance for similar queries"""
        if not self.routing_rules['performance_tracking']:
            return None
        
        # Create a key based on complexity characteristics
        complexity_key = (
            round(metrics.overall_score, 1),
            round(metrics.ambiguity_score, 1),
            round(metrics.semantic_complexity, 1)
        )
        
        return self.performance_history.get(complexity_key)
    
    def _adjust_for_performance(self, base_decision, historical_performance) -> RoutingDecision:
        """Adjust routing decision based on historical performance"""
        rule_based_success = historical_performance.get('rule_based_success_rate', 0.5)
        llm_success = historical_performance.get('llm_success_rate', 0.8)
        rule_based_speed = historical_performance.get('rule_based_avg_time', 0.1)
        llm_speed = historical_performance.get('llm_avg_time', 2.0)
        
        # Calculate performance scores
        rule_based_score = (
            rule_based_success * self.routing_rules['thresholds']['accuracy_weight'] +
            (1.0 / rule_based_speed) * self.routing_rules['thresholds']['performance_weight']
        )
        
        llm_score = (
            llm_success * self.routing_rules['thresholds']['accuracy_weight'] +
            (1.0 / llm_speed) * self.routing_rules['thresholds']['performance_weight']
        )
        
        # Adjust decision if performance history suggests a different approach
        if base_decision.processing_method == "rule_based" and llm_score > rule_based_score * 1.2:
            return RoutingDecision(
                processing_method="llm_based",
                confidence=base_decision.confidence * 0.9,
                reasoning=f"{base_decision.reasoning} - Adjusted to LLM based on performance history",
                fallback_method="rule_based"
            )
        elif base_decision.processing_method == "llm_based" and rule_based_score > llm_score * 1.2:
            return RoutingDecision(
                processing_method="rule_based",
                confidence=base_decision.confidence * 0.9,
                reasoning=f"{base_decision.reasoning} - Adjusted to rule-based based on performance history",
                fallback_method="llm_based"
            )
        
        return base_decision
    
    def _estimate_performance(self, processing_method: str, metrics) -> Dict[str, Any]:
        """Estimate performance characteristics for the chosen method"""
        if processing_method == "rule_based":
            return {
                'estimated_time': 0.05 + metrics.overall_score * 0.1,  # 50ms to 150ms
                'estimated_accuracy': max(0.7, 1.0 - metrics.ambiguity_score),
                'resource_usage': 'low',
                'scalability': 'high'
            }
        else:  # llm_based
            return {
                'estimated_time': 1.0 + metrics.overall_score * 2.0,  # 1s to 3s
                'estimated_accuracy': min(0.95, 0.8 + metrics.overall_score * 0.15),
                'resource_usage': 'high',
                'scalability': 'medium'
            }
    
    def record_performance(self, nl_query: str, processing_method: str, 
                          success: bool, execution_time: float, metrics=None):
        """Record performance for adaptive learning"""
        if not self.routing_rules['adaptive_learning']:
            return
        
        if metrics is None:
            metrics = self.complexity_analyzer.analyze(nl_query)
        
        complexity_key = (
            round(metrics.overall_score, 1),
            round(metrics.ambiguity_score, 1),
            round(metrics.semantic_complexity, 1)
        )
        
        if complexity_key not in self.performance_history:
            self.performance_history[complexity_key] = {
                'rule_based_attempts': 0,
                'rule_based_successes': 0,
                'rule_based_total_time': 0.0,
                'llm_attempts': 0,
                'llm_successes': 0,
                'llm_total_time': 0.0
            }
        
        history = self.performance_history[complexity_key]
        
        if processing_method == "rule_based":
            history['rule_based_attempts'] += 1
            history['rule_based_total_time'] += execution_time
            if success:
                history['rule_based_successes'] += 1
        else:
            history['llm_attempts'] += 1
            history['llm_total_time'] += execution_time
            if success:
                history['llm_successes'] += 1
        
        # Update derived metrics
        if history['rule_based_attempts'] > 0:
            history['rule_based_success_rate'] = history['rule_based_successes'] / history['rule_based_attempts']
            history['rule_based_avg_time'] = history['rule_based_total_time'] / history['rule_based_attempts']
        
        if history['llm_attempts'] > 0:
            history['llm_success_rate'] = history['llm_successes'] / history['llm_attempts']
            history['llm_avg_time'] = history['llm_total_time'] / history['llm_attempts']
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get statistics about routing decisions and performance"""
        total_rule_based = sum(h.get('rule_based_attempts', 0) for h in self.performance_history.values())
        total_llm = sum(h.get('llm_attempts', 0) for h in self.performance_history.values())
        total_queries = total_rule_based + total_llm
        
        if total_queries == 0:
            return {'total_queries': 0, 'message': 'No queries processed yet'}
        
        rule_based_successes = sum(h.get('rule_based_successes', 0) for h in self.performance_history.values())
        llm_successes = sum(h.get('llm_successes', 0) for h in self.performance_history.values())
        
        rule_based_time = sum(h.get('rule_based_total_time', 0) for h in self.performance_history.values())
        llm_time = sum(h.get('llm_total_time', 0) for h in self.performance_history.values())
        
        return {
            'total_queries': total_queries,
            'rule_based_percentage': (total_rule_based / total_queries) * 100,
            'llm_percentage': (total_llm / total_queries) * 100,
            'rule_based_success_rate': (rule_based_successes / total_rule_based) if total_rule_based > 0 else 0,
            'llm_success_rate': (llm_successes / total_llm) if total_llm > 0 else 0,
            'rule_based_avg_time': (rule_based_time / total_rule_based) if total_rule_based > 0 else 0,
            'llm_avg_time': (llm_time / total_llm) if total_llm > 0 else 0,
            'performance_history_size': len(self.performance_history)
        }
    
    def should_use_fallback(self, primary_result: Dict[str, Any], 
                           decision: RoutingDecision) -> bool:
        """Determine if fallback method should be used"""
        if not decision.fallback_method:
            return False
        
        # Use fallback if primary method failed
        if not primary_result.get('success', False):
            return True
        
        # Use fallback if confidence is very low
        if primary_result.get('confidence', 1.0) < 0.3:
            return True
        
        # Use fallback if result seems incomplete
        if primary_result.get('sql') and len(primary_result['sql'].strip()) < 20:
            return True
        
        # Use fallback if there are critical errors
        if primary_result.get('errors') and any('critical' in str(error).lower() for error in primary_result['errors']):
            return True
        
        return False
    
    def explain_routing_decision(self, decision: RoutingDecision) -> str:
        """Generate detailed explanation of routing decision"""
        explanation = [
            f"Query routed to: {decision.processing_method}",
            f"Confidence: {decision.confidence:.2f}",
            f"Reasoning: {decision.reasoning}"
        ]
        
        if decision.fallback_method:
            explanation.append(f"Fallback method: {decision.fallback_method}")
        
        if decision.complexity_metrics:
            metrics = decision.complexity_metrics
            explanation.extend([
                f"Complexity Analysis:",
                f"  - Overall complexity: {metrics.overall_score:.2f}",
                f"  - Lexical complexity: {metrics.lexical_complexity:.2f}",
                f"  - Syntactic complexity: {metrics.syntactic_complexity:.2f}",
                f"  - Semantic complexity: {metrics.semantic_complexity:.2f}",
                f"  - Ambiguity score: {metrics.ambiguity_score:.2f}"
            ])
            
            if metrics.reasoning:
                explanation.append("Reasoning factors:")
                for reason in metrics.reasoning:
                    explanation.append(f"  - {reason}")
        
        if decision.estimated_performance:
            perf = decision.estimated_performance
            explanation.extend([
                f"Estimated Performance:",
                f"  - Time: {perf['estimated_time']:.2f}s",
                f"  - Accuracy: {perf['estimated_accuracy']:.2f}",
                f"  - Resource usage: {perf['resource_usage']}"
            ])
        
        return "\n".join(explanation)
    
    def update_strategy(self, new_strategy: RoutingStrategy):
        """Update routing strategy"""
        old_strategy = self.strategy
        self.strategy = new_strategy
        logger.info(f"Routing strategy changed from {old_strategy.value} to {new_strategy.value}")
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update router configuration"""
        self.config.update(new_config)
        self.routing_rules = self._build_routing_rules()
        logger.info("Router configuration updated")
    
    def reset_performance_history(self):
        """Reset performance history for fresh learning"""
        self.performance_history.clear()
        logger.info("Performance history reset")
    
    def export_performance_data(self) -> Dict[str, Any]:
        """Export performance data for analysis"""
        return {
            'strategy': self.strategy.value,
            'config': self.config,
            'performance_history': self.performance_history,
            'statistics': self.get_routing_statistics()
        }
    
    def import_performance_data(self, data: Dict[str, Any]):
        """Import performance data from previous sessions"""
        if 'performance_history' in data:
            self.performance_history = data['performance_history']
        if 'config' in data:
            self.config.update(data['config'])
            self.routing_rules = self._build_routing_rules()
        logger.info("Performance data imported")

#end-of-script