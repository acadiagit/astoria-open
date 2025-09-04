# Path: nl2sql/routing/__init__.py
# Filename: __init__.py
# Purpose: Query routing package initialization for intelligent query distribution

"""
Query Routing Components

Handles intelligent routing of queries between rule-based NL2SQL processing
and LLM-based fallback systems based on query complexity analysis.
"""

from .complexity_analyzer import ComplexityAnalyzer, QueryComplexity, ComplexityMetrics
from .query_router import QueryRouter, RoutingDecision, RoutingStrategy

__all__ = [
    'ComplexityAnalyzer',
    'QueryComplexity', 
    'ComplexityMetrics',
    'QueryRouter',
    'RoutingDecision',
    'RoutingStrategy'
]

#end-of-script