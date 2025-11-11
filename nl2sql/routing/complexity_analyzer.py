# filename: nl2sql/routing/complexity_analyzer.py
# Purpose: Analyzes the complexity of a natural language query.

import re
from dataclasses import dataclass
from enum import Enum

# --- FIX: Re-introduce the QueryComplexity Enum that __init__.py depends on ---
class QueryComplexity(Enum):
    SIMPLE = "SIMPLE"
    MODERATE = "MODERATE"
    COMPLEX = "COMPLEX"

# --- Keywords to identify complex analytical queries ---
ANALYTICAL_KEYWORDS = [
    'average', 'avg', 'mean',
    'total', 'sum',
    'count', 'how many',
    'max', 'maximum', 'min', 'minimum', 'largest', 'smallest',
    'most common', 'least common',
    'distribution', 'trend', 'analyze', 'compare', 'correlation'
]

@dataclass
class ComplexityMetrics:
    keyword_score: int = 0
    length_score: int = 0
    overall_score: float = 0.0

class ComplexityAnalyzer:
    """
    Analyzes an NL query to determine if it should be handled by the simple
    rule-based system or the complex LLM agent.
    """
    def __init__(self, schema_analyzer):
        self.schema_analyzer = schema_analyzer

    def analyze(self, nl_query: str) -> QueryComplexity:
        """
        Calculates a complexity score and returns the complexity level as an Enum.
        """
        metrics = ComplexityMetrics()
        lower_query = nl_query.lower()

        # Check for analytical keywords (the most important signal)
        found_keywords = [kw for kw in ANALYTICAL_KEYWORDS if kw in lower_query]
        metrics.keyword_score = len(found_keywords) * 5  # Weight keywords heavily

        # A high keyword score is a definitive sign of a complex query.
        if metrics.keyword_score > 0:
            return QueryComplexity.COMPLEX
            
        # Factor in query length for queries without obvious analytical keywords
        word_count = len(lower_query.split())
        if word_count > 10:
            metrics.length_score = 5
        elif word_count > 5:
            metrics.length_score = 2
            
        total_score = metrics.keyword_score + metrics.length_score
        
        # Decide based on a score threshold.
        if total_score > 8:
            return QueryComplexity.MODERATE # Could be complex, but let rules try first
        else:
#--end=-of-file--
            return QueryComplexity.SIMPLE
