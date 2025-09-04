# Path: nl2sql/routing/complexity_analyzer.py
# Filename: complexity_analyzer.py
# Purpose: Analyze query complexity to determine optimal processing method

"""
Query Complexity Analyzer

Analyzes natural language queries to determine their complexity level
and recommend appropriate processing strategies (rule-based vs LLM).
"""

import re
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QueryComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    AMBIGUOUS = "ambiguous"

@dataclass
class ComplexityMetrics:
    """Metrics used to assess query complexity"""
    lexical_complexity: float
    syntactic_complexity: float
    semantic_complexity: float
    domain_specificity: float
    ambiguity_score: float
    overall_score: float
    reasoning: List[str]

class ComplexityAnalyzer:
    """Analyzes query complexity for routing decisions"""
    
    def __init__(self, schema_analyzer):
        self.schema = schema_analyzer
        self.simple_patterns = self._build_simple_patterns()
        self.complex_indicators = self._build_complex_indicators()
        self.domain_terms = self._build_domain_terms()
        self.ambiguous_phrases = self._build_ambiguous_phrases()
    
    def _build_simple_patterns(self) -> List[str]:
        """Build patterns that indicate simple queries"""
        return [
            # Basic listing patterns
            r'^(list|show|display|get)\s+(all\s+)?(\w+)s?$',
            r'^(how many|count)\s+(\w+)s?\s*(are|were)?',
            r'^(what|which)\s+(\w+)s?\s+(are|were)\s+(\w+)',
            
            # Simple filtering patterns
            r'^(find|get|show)\s+(\w+)s?\s+(built|made|from|in)\s+(\w+)$',
            r'^(\w+)s?\s+(with|having)\s+(\w+)\s+(\w+)$',
            r'^(oldest|newest|largest|smallest)\s+(\w+)s?$',
            
            # Basic aggregation patterns
            r'^(average|total|sum|maximum|minimum)\s+(\w+)\s+of\s+(\w+)s?$',
            r'^(\w+)\s+of\s+(the\s+)?(oldest|newest|largest)\s+(\w+)$',
        ]
    
    def _build_complex_indicators(self) -> List[str]:
        """Build patterns that indicate complex queries"""
        return [
            # Multiple conditions
            r'\b(and|or|but)\b.*\b(and|or|but)\b',
            
            # Temporal relationships
            r'\b(before|after|during|while|when)\b.*\b(before|after|during|while|when)\b',
            
            # Comparative analysis
            r'\b(compare|comparison|versus|vs|against)\b',
            r'\b(better|worse|more|less)\s+than\b',
            
            # Complex aggregations
            r'\b(percentage|ratio|proportion|rate)\b',
            r'\bgrouped?\s+by\b',
            r'\bper\s+\w+\b',
            
            # Nested concepts
            r'\b(ships?\s+that\s+\w+|vessels?\s+which\s+\w+)\b',
            r'\b(crew\s+members?\s+who\s+\w+)\b',
            
            # Business logic
            r'\b(profitable|efficient|optimal|best|worst)\b',
            r'\b(trend|pattern|correlation)\b',
            
            # Multiple tables implied
            r'\b(voyages?\s+of\s+ships?|crew\s+of\s+vessels?)\b',
            r'\b(maintenance\s+records?\s+for\s+ships?)\b'
        ]
    
    def _build_domain_terms(self) -> Dict[str, List[str]]:
        """Build domain-specific terminology"""
        return {
            'vessel_types': [
                'schooner', 'brig', 'frigate', 'corvette', 'sloop', 'bark',
                'steamship', 'paddle wheeler', 'trawler', 'yacht', 'cutter'
            ],
            'maritime_roles': [
                'captain', 'first mate', 'second mate', 'bosun', 'boatswain',
                'cook', 'steward', 'engineer', 'pilot', 'navigator'
            ],
            'maritime_terms': [
                'tonnage', 'displacement', 'beam', 'draft', 'rigging',
                'cargo', 'freight', 'ballast', 'port', 'starboard',
                'bow', 'stern', 'mast', 'sail', 'anchor'
            ],
            'temporal_terms': [
                'voyage', 'journey', 'passage', 'sailing', 'departure',
                'arrival', 'docking', 'mooring', 'anchorage'
            ],
            'business_terms': [
                'profit', 'cost', 'revenue', 'cargo value', 'freight rate',
                'insurance', 'charter', 'commission'
            ]
        }
    
    def _build_ambiguous_phrases(self) -> List[str]:
        """Build phrases that indicate potential ambiguity"""
        return [
            # Pronouns without clear antecedents
            r'\b(it|they|them|those|these)\b(?!\s+(are|were|is|was))',
            
            # Vague quantifiers
            r'\b(some|many|few|several|most|various)\b',
            
            # Unclear temporal references
            r'\b(recently|lately|soon|earlier|later)\b',
            r'\b(old|new|modern|ancient)\b(?!\s+\w+)',
            
            # Subjective terms
            r'\b(good|bad|better|worse|best|worst)\b(?!\s+(than|for))',
            r'\b(large|small|big|little)\b(?!\s+(than|er))',
            
            # Context-dependent terms
            r'\b(here|there|this|that)\b(?!\s+\w+)',
            r'\b(current|previous|next|last)\b(?!\s+(year|month|day))',
        ]
    
    def analyze(self, nl_query: str) -> ComplexityMetrics:
        """Analyze query complexity and return detailed metrics"""
        query = nl_query.lower().strip()
        
        # Calculate individual complexity scores
        lexical_score = self._calculate_lexical_complexity(query)
        syntactic_score = self._calculate_syntactic_complexity(query)
        semantic_score = self._calculate_semantic_complexity(query)
        domain_score = self._calculate_domain_specificity(query)
        ambiguity_score = self._calculate_ambiguity_score(query)
        
        # Calculate overall complexity score
        weights = {
            'lexical': 0.15,
            'syntactic': 0.25,
            'semantic': 0.30,
            'domain': 0.15,
            'ambiguity': 0.15
        }
        
        overall_score = (
            lexical_score * weights['lexical'] +
            syntactic_score * weights['syntactic'] +
            semantic_score * weights['semantic'] +
            domain_score * weights['domain'] +
            ambiguity_score * weights['ambiguity']
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            query, lexical_score, syntactic_score, semantic_score,
            domain_score, ambiguity_score
        )
        
        return ComplexityMetrics(
            lexical_complexity=lexical_score,
            syntactic_complexity=syntactic_score,
            semantic_complexity=semantic_score,
            domain_specificity=domain_score,
            ambiguity_score=ambiguity_score,
            overall_score=overall_score,
            reasoning=reasoning
        )
    
    def get_complexity_level(self, metrics: ComplexityMetrics) -> QueryComplexity:
        """Determine complexity level from metrics"""
        score = metrics.overall_score
        
        if metrics.ambiguity_score > 0.7:
            return QueryComplexity.AMBIGUOUS
        elif score <= 0.3:
            return QueryComplexity.SIMPLE
        elif score <= 0.6:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.COMPLEX
    
    def _calculate_lexical_complexity(self, query: str) -> float:
        """Calculate lexical complexity based on vocabulary"""
        score = 0.0
        words = query.split()
        
        # Word count factor
        if len(words) > 15:
            score += 0.3
        elif len(words) > 10:
            score += 0.2
        elif len(words) > 5:
            score += 0.1
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        if avg_word_length > 6:
            score += 0.2
        elif avg_word_length > 4:
            score += 0.1
        
        # Rare or technical words
        technical_words = 0
        for category, terms in self.domain_terms.items():
            if category in ['maritime_terms', 'business_terms']:
                for term in terms:
                    if term in query:
                        technical_words += 1
        
        score += min(technical_words * 0.1, 0.3)
        
        # Numbers and dates increase complexity
        if re.search(r'\b\d{4}\b', query):  # Years
            score += 0.1
        if re.search(r'\b\d+\.\d+\b', query):  # Decimals
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_syntactic_complexity(self, query: str) -> float:
        """Calculate syntactic complexity based on structure"""
        score = 0.0
        
        # Check for simple patterns first
        for pattern in self.simple_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return 0.1  # Very simple syntax
        
        # Count clauses and conjunctions
        conjunctions = len(re.findall(r'\b(and|or|but|however|although|because|since|while|when|where|which|that)\b', query, re.IGNORECASE))
        score += min(conjunctions * 0.2, 0.4)
        
        # Nested structures
        nested_patterns = [
            r'\b\w+\s+that\s+\w+',  # Relative clauses
            r'\b\w+\s+which\s+\w+',
            r'\b\w+\s+who\s+\w+',
            r'\(\s*[^)]+\s*\)',  # Parenthetical expressions
        ]
        
        for pattern in nested_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                score += 0.15
        
        # Question complexity
        question_words = len(re.findall(r'\b(what|which|where|when|why|how|who)\b', query, re.IGNORECASE))
        if question_words > 1:
            score += 0.2
        
        # Conditional structures
        if re.search(r'\b(if|unless|provided|assuming)\b', query, re.IGNORECASE):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_semantic_complexity(self, query: str) -> float:
        """Calculate semantic complexity based on meaning"""
        score = 0.0
        
        # Check for complex indicators
        for pattern in self.complex_indicators:
            if re.search(pattern, query, re.IGNORECASE):
                score += 0.2
        
        # Multiple entity types
        entity_types = set()
        for category, terms in self.domain_terms.items():
            for term in terms:
                if term in query:
                    entity_types.add(category)
        
        if len(entity_types) > 2:
            score += 0.3
        elif len(entity_types) > 1:
            score += 0.15
        
        # Implicit relationships
        relationship_indicators = [
            r'\bof\s+the\b', r'\bfor\s+each\b', r'\bper\s+\w+\b',
            r'\bbetween\s+\w+\s+and\s+\w+\b', r'\bamong\s+\w+\b'
        ]
        
        for pattern in relationship_indicators:
            if re.search(pattern, query, re.IGNORECASE):
                score += 0.1
        
        # Abstract concepts
        abstract_terms = [
            'efficiency', 'profitability', 'optimization', 'correlation',
            'trend', 'pattern', 'relationship', 'impact', 'influence'
        ]
        
        for term in abstract_terms:
            if term in query:
                score += 0.15
        
        # Negations
        if re.search(r'\b(not|no|never|without|except|excluding)\b', query, re.IGNORECASE):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_domain_specificity(self, query: str) -> float:
        """Calculate how domain-specific the query is"""
        score = 0.0
        total_terms = 0
        domain_terms_found = 0
        
        for category, terms in self.domain_terms.items():
            for term in terms:
                total_terms += 1
                if term in query:
                    domain_terms_found += 1
                    if category == 'business_terms':
                        score += 0.15  # Business terms are more complex
                    else:
                        score += 0.1
        
        # Bonus for using multiple domain terms
        if domain_terms_found > 3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_ambiguity_score(self, query: str) -> float:
        """Calculate potential ambiguity in the query"""
        score = 0.0
        
        # Check for ambiguous phrases
        for pattern in self.ambiguous_phrases:
            matches = re.findall(pattern, query, re.IGNORECASE)
            score += len(matches) * 0.15
        
        # Incomplete references
        if re.search(r'\b(the|that|this)\s+\w+\b', query) and not re.search(r'\b(vessels?|ships?|crew|voyages?)\b', query):
            score += 0.2
        
        # Multiple possible interpretations
        if 'or' in query:
            score += 0.1
        
        # Unclear scope
        scope_indicators = ['all', 'some', 'any', 'each', 'every']
        if not any(indicator in query for indicator in scope_indicators):
            if not re.search(r'\b(the|a|an)\b', query):
                score += 0.15
        
        return min(score, 1.0)
    
    def _generate_reasoning(self, query: str, lexical: float, syntactic: float, 
                          semantic: float, domain: float, ambiguity: float) -> List[str]:
        """Generate human-readable reasoning for complexity assessment"""
        reasoning = []
        
        if lexical > 0.5:
            reasoning.append("High lexical complexity due to technical vocabulary or long words")
        elif lexical < 0.2:
            reasoning.append("Simple vocabulary and short query")
        
        if syntactic > 0.5:
            reasoning.append("Complex sentence structure with multiple clauses")
        elif syntactic < 0.2:
            reasoning.append("Simple sentence structure matching basic patterns")
        
        if semantic > 0.5:
            reasoning.append("Complex semantic relationships or abstract concepts")
        elif semantic < 0.2:
            reasoning.append("Straightforward semantic content")
        
        if domain > 0.5:
            reasoning.append("High domain specificity with specialized maritime terminology")
        elif domain < 0.2:
            reasoning.append("General vocabulary without specialized terms")
        
        if ambiguity > 0.5:
            reasoning.append("High potential for ambiguity or multiple interpretations")
        elif ambiguity < 0.2:
            reasoning.append("Clear and unambiguous query")
        
        # Check for specific patterns
        for pattern in self.simple_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                reasoning.append("Matches simple query pattern")
                break
        
        for pattern in self.complex_indicators:
            if re.search(pattern, query, re.IGNORECASE):
                reasoning.append("Contains complex query indicators")
                break
        
        return reasoning
    
    def is_rule_based_suitable(self, metrics: ComplexityMetrics) -> bool:
        """Determine if query is suitable for rule-based processing"""
        complexity_level = self.get_complexity_level(metrics)
        
        # Rule-based is suitable for simple and some moderate queries
        if complexity_level == QueryComplexity.SIMPLE:
            return True
        elif complexity_level == QueryComplexity.MODERATE:
            # Check specific metrics
            return (metrics.ambiguity_score < 0.4 and 
                   metrics.semantic_complexity < 0.6)
        else:
            return False
    
    def recommend_processing_strategy(self, metrics: ComplexityMetrics) -> str:
        """Recommend processing strategy based on complexity"""
        complexity_level = self.get_complexity_level(metrics)
        
        if complexity_level == QueryComplexity.SIMPLE:
            return "rule_based"
        elif complexity_level == QueryComplexity.MODERATE:
            if self.is_rule_based_suitable(metrics):
                return "rule_based_with_validation"
            else:
                return "hybrid"
        elif complexity_level == QueryComplexity.COMPLEX:
            return "llm_based"
        else:  # AMBIGUOUS
            return "llm_with_clarification"

#end-of-file