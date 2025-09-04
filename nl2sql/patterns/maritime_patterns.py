# Path: nl2sql/patterns/maritime_patterns.py
# Filename: maritime_patterns.py
# Purpose: Domain-specific maritime query patterns for optimized processing

"""
Maritime Query Patterns

Defines domain-specific patterns for common maritime database queries
to enable fast, accurate processing without LLM overhead.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PatternType(Enum):
    VESSEL_LISTING = "vessel_listing"
    VESSEL_FILTERING = "vessel_filtering"
    VOYAGE_QUERY = "voyage_query"
    CREW_QUERY = "crew_query"
    MAINTENANCE_QUERY = "maintenance_query"
    COUNT_QUERY = "count_query"
    AGGREGATION = "aggregation"
    COMPARISON = "comparison"

@dataclass
class QueryPattern:
    """Represents a maritime query pattern"""
    name: str
    pattern_type: PatternType
    regex_pattern: str
    sql_template: str
    parameter_mapping: Dict[str, str]
    confidence_score: float
    examples: List[str]
    description: str

@dataclass
class PatternMatch:
    """Result of pattern matching"""
    pattern: QueryPattern
    matched_groups: Dict[str, str]
    confidence: float
    sql_query: str
    parameters: List[Any]

class MaritimePatterns:
    """Manages maritime-specific query patterns"""
    
    def __init__(self):
        self.patterns = self._build_maritime_patterns()
        self.pattern_index = self._build_pattern_index()
        
    def _build_maritime_patterns(self) -> List[QueryPattern]:
        """Build comprehensive maritime query patterns"""
        patterns = []
        
        # Vessel listing patterns
        patterns.extend(self._build_vessel_patterns())
        
        # Voyage patterns
        patterns.extend(self._build_voyage_patterns())
        
        # Crew patterns
        patterns.extend(self._build_crew_patterns())
        
        # Maintenance patterns
        patterns.extend(self._build_maintenance_patterns())
        
        # Count patterns
        patterns.extend(self._build_count_patterns())
        
        # Aggregation patterns
        patterns.extend(self._build_aggregation_patterns())
        
        return patterns
    
    def _build_vessel_patterns(self) -> List[QueryPattern]:
        """Build vessel-related query patterns"""
        return [
            QueryPattern(
                name="list_all_vessels",
                pattern_type=PatternType.VESSEL_LISTING,
                regex_pattern=r'^(?:list|show|display|get)\s+(?:all\s+)?(?:vessels?|ships?|boats?)(?:\s+(?:in\s+(?:the\s+)?(?:database|system)))?$',
                sql_template="SELECT name, vessel_type, year_built FROM vessels ORDER BY name",
                parameter_mapping={},
                confidence_score=0.95,
                examples=[
                    "list all vessels",
                    "show ships",
                    "display all boats",
                    "get vessels in the database"
                ],
                description="Lists all vessels with basic information"
            ),
            
            QueryPattern(
                name="vessels_by_type",
                pattern_type=PatternType.VESSEL_FILTERING,
                regex_pattern=r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:all\s+)?(?P<vessel_type>schooners?|brigs?|barks?|sloops?|ships?|cargo\s+ships?|passenger\s+ships?|tankers?|fishing\s+boats?|steamships?)$',
                sql_template="SELECT name, vessel_type, year_built, gross_tonnage FROM vessels WHERE vessel_type ILIKE %s ORDER BY name LIMIT %s",
                parameter_mapping={"vessel_type": "vessel_type", "limit": "limit"},
                confidence_score=0.90,
                examples=[
                    "list all schooners",
                    "show cargo ships", 
                    "find tankers",
                    "get fishing boats",
                    "list 4 brigs",
                    "show 10 schooners"
                ],
                description="Lists vessels of a specific type with optional limit"
            ),
            
            QueryPattern(
                name="vessels_built_before_year",
                pattern_type=PatternType.VESSEL_FILTERING,
                regex_pattern=r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:all\s+)?(?:vessels?|ships?|boats?)\s+built\s+before\s+(?P<year>\d{4})$',
                sql_template="SELECT name, vessel_type, year_built FROM vessels WHERE year_built < %s ORDER BY year_built ASC LIMIT %s",
                parameter_mapping={"year": "year", "limit": "limit"},
                confidence_score=0.92,
                examples=[
                    "list ships built before 1900",
                    "show vessels built before 1850",
                    "find boats built before 1800",
                    "list 5 ships built before 1900"
                ],
                description="Lists vessels built before a specific year"
            ),
            
            QueryPattern(
                name="vessels_built_after_year",
                pattern_type=PatternType.VESSEL_FILTERING,
                regex_pattern=r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:all\s+)?(?:vessels?|ships?|boats?)\s+built\s+after\s+(?P<year>\d{4})$',
                sql_template="SELECT name, vessel_type, year_built FROM vessels WHERE year_built > %s ORDER BY year_built ASC LIMIT %s",
                parameter_mapping={"year": "year", "limit": "limit"},
                confidence_score=0.92,
                examples=[
                    "list ships built after 1900",
                    "show vessels built after 1950",
                    "find 10 boats built after 1880"
                ],
                description="Lists vessels built after a specific year"
            ),
            
            QueryPattern(
                name="largest_vessels",
                pattern_type=PatternType.VESSEL_FILTERING,
                regex_pattern=r'^(?:show|list|find|get)\s+(?:the\s+)?(?P<limit>\d+)?\s*(?:largest|biggest)\s+(?:vessels?|ships?|boats?)$',
                sql_template="SELECT name, vessel_type, gross_tonnage, year_built FROM vessels WHERE gross_tonnage IS NOT NULL ORDER BY gross_tonnage DESC LIMIT %s",
                parameter_mapping={"limit": "limit"},
                confidence_score=0.90,
                examples=[
                    "show largest vessels",
                    "list 5 biggest ships",
                    "find the largest boats",
                    "show 10 largest vessels"
                ],
                description="Lists the largest vessels by gross_tonnage"
            ),
            
            QueryPattern(
                name="oldest_vessels",
                pattern_type=PatternType.VESSEL_FILTERING,
                regex_pattern=r'^(?:show|list|find|get)\s+(?:the\s+)?(?P<limit>\d+)?\s*oldest\s+(?:vessels?|ships?|boats?)$',
                sql_template="SELECT name, vessel_type, year_built FROM vessels WHERE year_built IS NOT NULL ORDER BY year_built ASC LIMIT %s",
                parameter_mapping={"limit": "limit"},
                confidence_score=0.90,
                examples=[
                    "show oldest vessels",
                    "list 10 oldest ships",
                    "find the oldest boats",
                    "show 5 oldest vessels"
                ],
                description="Lists the oldest vessels by construction year"
            )
        ]
    
    def _build_voyage_patterns(self) -> List[QueryPattern]:
        """Build voyage-related query patterns"""
        return [
            QueryPattern(
                name="voyages_from_port",
                pattern_type=PatternType.VOYAGE_QUERY,
                regex_pattern=r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:all\s+)?voyages?\s+from\s+(?P<port>[\w\s]+)$',
                sql_template="SELECT v.name, vo.departure_port, vo.arrival_port, vo.departure_date FROM vessels v JOIN voyages vo ON v.vessel_id = vo.vessel_id WHERE vo.departure_port ILIKE %s ORDER BY vo.departure_date LIMIT %s",
                parameter_mapping={"port": "port", "limit": "limit"},
                confidence_score=0.88,
                examples=[
                    "list voyages from Boston",
                    "show voyages from New York",
                    "find voyages from Machias",
                    "list 5 voyages from Boston"
                ],
                description="Lists voyages departing from a specific port"
            ),
            
            QueryPattern(
                name="voyages_to_port",
                pattern_type=PatternType.VOYAGE_QUERY,
                regex_pattern=r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:all\s+)?voyages?\s+to\s+(?P<port>[\w\s]+)$',
                sql_template="SELECT v.name, vo.departure_port, vo.arrival_port, vo.arrival_date FROM vessels v JOIN voyages vo ON v.vessel_id = vo.vessel_id WHERE vo.arrival_port ILIKE %s ORDER BY vo.arrival_date LIMIT %s",
                parameter_mapping={"port": "port", "limit": "limit"},
                confidence_score=0.88,
                examples=[
                    "list voyages to Liverpool",
                    "show voyages to Portland",
                    "find voyages to Boston",
                    "show 10 voyages to Liverpool"
                ],
                description="Lists voyages arriving at a specific port"
            ),
            
            QueryPattern(
                name="voyages_by_vessel",
                pattern_type=PatternType.VOYAGE_QUERY,
                regex_pattern=r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:all\s+)?voyages?\s+(?:of|for|by)\s+(?:the\s+)?(?P<vessel_name>[\w\s]+)$',
                sql_template="SELECT vo.departure_port, vo.arrival_port, vo.departure_date, vo.cargo_type FROM vessels v JOIN voyages vo ON v.vessel_id = vo.vessel_id WHERE v.name ILIKE %s ORDER BY vo.departure_date LIMIT %s",
                parameter_mapping={"vessel_name": "vessel_name", "limit": "limit"},
                confidence_score=0.85,
                examples=[
                    "list voyages of ABBIE",
                    "show voyages for the ATLANTIC",
                    "find voyages by ANNIE",
                    "list 5 voyages of ABBIE"
                ],
                description="Lists all voyages for a specific vessel"
            )
        ]
    
    def _build_crew_patterns(self) -> List[QueryPattern]:
        """Build crew-related query patterns"""
        return [
            QueryPattern(
                name="crew_by_position",
                pattern_type=PatternType.CREW_QUERY,
                regex_pattern=r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:all\s+)?(?P<position>captains?|first\s+mates?|engineers?|cooks?|sailors?)$',
                sql_template="SELECT c.first_name, c.last_name, c.position, v.name as vessel_name FROM crew c JOIN vessels v ON c.vessel_id = v.vessel_id WHERE c.position ILIKE %s ORDER BY c.last_name LIMIT %s",
                parameter_mapping={"position": "position", "limit": "limit"},
                confidence_score=0.90,
                examples=[
                    "list all captains",
                    "show first mates",
                    "find engineers",
                    "get sailors",
                    "list 10 captains"
                ],
                description="Lists crew members by their position"
            ),
            
            QueryPattern(
                name="crew_of_vessel",
                pattern_type=PatternType.CREW_QUERY,
                regex_pattern=r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:the\s+)?crew\s+(?:of|for|on)\s+(?:the\s+)?(?P<vessel_name>[\w\s]+)$',
                sql_template="SELECT c.first_name, c.last_name, c.position, c.hire_date FROM crew c JOIN vessels v ON c.vessel_id = v.vessel_id WHERE v.name ILIKE %s ORDER BY c.position LIMIT %s",
                parameter_mapping={"vessel_name": "vessel_name", "limit": "limit"},
                confidence_score=0.88,
                examples=[
                    "list crew of ABBIE",
                    "show the crew for ATLANTIC",
                    "find crew on the LIBERTY",
                    "list 5 crew of ABBIE"
                ],
                description="Lists crew members of a specific vessel"
            )
        ]
    
    def _build_maintenance_patterns(self) -> List[QueryPattern]:
        """Build maintenance-related query patterns"""
        return [
            QueryPattern(
                name="maintenance_by_vessel",
                pattern_type=PatternType.MAINTENANCE_QUERY,
                regex_pattern=r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:all\s+)?maintenance\s+(?:records?\s+)?(?:of|for|on)\s+(?:the\s+)?(?P<vessel_name>[\w\s]+)$',
                sql_template="SELECT m.maintenance_date, m.maintenance_type, m.description, m.cost FROM maintenance m JOIN vessels v ON m.vessel_id = v.vessel_id WHERE v.name ILIKE %s ORDER BY m.maintenance_date DESC LIMIT %s",
                parameter_mapping={"vessel_name": "vessel_name", "limit": "limit"},
                confidence_score=0.90,
                examples=[
                    "list maintenance of ABBIE",
                    "show maintenance records for ATLANTIC",
                    "find maintenance on the LIBERTY",
                    "list 5 maintenance of ABBIE"
                ],
                description="Lists maintenance records for a specific vessel"
            ),
            
            QueryPattern(
                name="maintenance_by_type",
                pattern_type=PatternType.MAINTENANCE_QUERY,
                regex_pattern=r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:all\s+)?(?P<maintenance_type>hull\s+repairs?|engine\s+overhauls?|annual\s+inspections?|mast\s+replacements?)$',
                sql_template="SELECT v.name, m.maintenance_date, m.description, m.cost FROM maintenance m JOIN vessels v ON m.vessel_id = v.vessel_id WHERE m.maintenance_type ILIKE %s ORDER BY m.maintenance_date DESC LIMIT %s",
                parameter_mapping={"maintenance_type": "maintenance_type", "limit": "limit"},
                confidence_score=0.85,
                examples=[
                    "list hull repairs",
                    "show engine overhauls",
                    "find annual inspections",
                    "list 10 hull repairs"
                ],
                description="Lists maintenance records by type"
            )
        ]
    
    def _build_count_patterns(self) -> List[QueryPattern]:
        """Build count query patterns"""
        return [
            QueryPattern(
                name="count_all_vessels",
                pattern_type=PatternType.COUNT_QUERY,
                regex_pattern=r'^(?:how\s+many|count)\s+(?:vessels?|ships?|boats?)\s+(?:are\s+(?:there|in\s+the\s+database)?)?$',
                sql_template="SELECT COUNT(*) as count FROM vessels",
                parameter_mapping={},
                confidence_score=0.95,
                examples=[
                    "how many vessels are there",
                    "count ships",
                    "how many boats are in the database"
                ],
                description="Counts total number of vessels"
            ),
            
            QueryPattern(
                name="count_vessels_by_type",
                pattern_type=PatternType.COUNT_QUERY,
                regex_pattern=r'^(?:how\s+many|count)\s+(?P<vessel_type>schooners?|brigs?|barks?|sloops?|ships?|cargo\s+ships?|passenger\s+ships?|tankers?|fishing\s+boats?)$',
                sql_template="SELECT COUNT(*) as count FROM vessels WHERE vessel_type ILIKE %s",
                parameter_mapping={"vessel_type": "vessel_type"},
                confidence_score=0.92,
                examples=[
                    "how many schooners",
                    "count cargo ships",
                    "how many fishing boats",
                    "count brigs"
                ],
                description="Counts vessels of a specific type"
            ),
            
            QueryPattern(
                name="count_active_vessels",
                pattern_type=PatternType.COUNT_QUERY,
                regex_pattern=r'^(?:how\s+many|count)\s+active\s+(?:vessels?|ships?|boats?)$',
                sql_template="SELECT COUNT(*) as count FROM vessels WHERE current_status = 'Active'",
                parameter_mapping={},
                confidence_score=0.90,
                examples=[
                    "how many active vessels",
                    "count active ships"
                ],
                description="Counts active vessels"
            )
        ]
    
    def _build_aggregation_patterns(self) -> List[QueryPattern]:
        """Build aggregation query patterns"""
        return [
            QueryPattern(
                name="average_vessel_gross_tonnage",
                pattern_type=PatternType.AGGREGATION,
                regex_pattern=r'^(?:what\s+is\s+the\s+)?average\s+(?:gross_tonnage|size|weight)\s+of\s+(?:vessels?|ships?|boats?)$',
                sql_template="SELECT AVG(gross_tonnage) as average_gross_tonnage FROM vessels WHERE gross_tonnage IS NOT NULL",
                parameter_mapping={},
                confidence_score=0.88,
                examples=[
                    "average gross_tonnage of vessels",
                    "what is the average size of ships"
                ],
                description="Calculates average vessel gross_tonnage"
            ),
            
            QueryPattern(
                name="total_maintenance_cost",
                pattern_type=PatternType.AGGREGATION,
                regex_pattern=r'^(?:what\s+is\s+the\s+)?total\s+maintenance\s+cost\s+(?:for\s+(?:all\s+)?(?:vessels?|ships?|boats?))?$',
                sql_template="SELECT SUM(cost) as total_cost FROM maintenance WHERE cost IS NOT NULL",
                parameter_mapping={},
                confidence_score=0.85,
                examples=[
                    "total maintenance cost",
                    "what is the total maintenance cost for all vessels"
                ],
                description="Calculates total maintenance costs"
            )
        ]
    
    def _build_pattern_index(self) -> Dict[PatternType, List[QueryPattern]]:
        """Build an index of patterns by type for faster lookup"""
        index = {}
        for pattern in self.patterns:
            if pattern.pattern_type not in index:
                index[pattern.pattern_type] = []
            index[pattern.pattern_type].append(pattern)
        return index
    
    def match_pattern(self, nl_query: str) -> Optional[PatternMatch]:
        """Find the best matching pattern for a query"""
        query = nl_query.lower().strip()
        best_match = None
        best_confidence = 0.0
        
        for pattern in self.patterns:
            match = re.search(pattern.regex_pattern, query, re.IGNORECASE)
            if match:
                # Calculate confidence based on pattern confidence and match quality
                match_confidence = pattern.confidence_score
                
                # Adjust confidence based on match completeness
                matched_length = len(match.group(0))
                query_length = len(query)
                coverage = matched_length / query_length
                adjusted_confidence = match_confidence * coverage
                
                if adjusted_confidence > best_confidence:
                    # Extract parameters from match
                    matched_groups = match.groupdict()
                    
                    # Generate SQL and parameters
                    sql_query, parameters = self._generate_sql_from_pattern(pattern, matched_groups)
                    
                    best_match = PatternMatch(
                        pattern=pattern,
                        matched_groups=matched_groups,
                        confidence=adjusted_confidence,
                        sql_query=sql_query,
                        parameters=parameters
                    )
                    best_confidence = adjusted_confidence
        
        return best_match
    
    def _generate_sql_from_pattern(self, pattern: QueryPattern, 
                                  matched_groups: Dict[str, str]) -> Tuple[str, List[Any]]:
        """Generate SQL query and parameters from pattern and matched groups"""
        sql_query = pattern.sql_template
        parameters = []
        
        for param_name, group_name in pattern.parameter_mapping.items():
            if group_name in matched_groups:
                value = matched_groups[group_name]
                processed_value = self._process_parameter_value(param_name, value, pattern)
                parameters.append(processed_value)
            else:
                # Handle missing parameters with defaults
                default_value = self._get_default_parameter_value(param_name, pattern)
                if default_value is not None:
                    parameters.append(default_value)
        
        return sql_query, parameters
    
    def _process_parameter_value(self, param_name: str, value: str, pattern: QueryPattern) -> Any:
        """Process parameter values based on their semantic meaning"""
        # Handle None values
        if value is None:
            return self._get_default_parameter_value(param_name, pattern)
        
        value = str(value).strip()
        
        if param_name == 'year':
            try:
                return int(value)
            except (ValueError, TypeError):
                return 2000  # Default year
        elif param_name == 'limit':
            try:
                if value is None or value == '':
                    return 10  # Default limit
                limit_val = int(value)
                # Handle edge cases
                if limit_val <= 0:
                    return 1  # Minimum limit
                elif limit_val > 1000:
                    return 1000  # Maximum limit
                return limit_val
            except (ValueError, TypeError):
                return 10  # Default limit
        elif param_name in ['vessel_type', 'maintenance_type']:
            return f'%{value}%'
        elif param_name in ['port', 'vessel_name']:
            return f'%{value}%'
        elif param_name == 'status':
            return value.title() if value else 'Active'
        elif param_name == 'position':
            # Handle position variations
            position_map = {
                'captains': 'captain',
                'first mates': 'first mate',
                'engineers': 'engineer',
                'cooks': 'cook',
                'sailors': 'sailor'
            }
            return f'%{position_map.get(value, value)}%'
        else:
            return value
    
    def _get_default_parameter_value(self, param_name: str, pattern: QueryPattern) -> Any:
        """Get default value for missing parameters"""
        if param_name == 'limit':
            return 10  # Default limit
        elif param_name == 'year':
            return None
        elif param_name in ['vessel_type', 'maintenance_type', 'port', 'vessel_name', 'position']:
            return None
        else:
            return None
    
    def get_patterns_by_type(self, pattern_type: PatternType) -> List[QueryPattern]:
        """Get all patterns of a specific type"""
        return self.pattern_index.get(pattern_type, [])
    
    def get_pattern_examples(self, limit: int = 5) -> Dict[str, List[str]]:
        """Get example queries for each pattern type"""
        examples = {}
        for pattern_type in PatternType:
            examples[pattern_type.value] = []
            patterns = self.get_patterns_by_type(pattern_type)
            for pattern in patterns[:limit]:
                examples[pattern_type.value].extend(pattern.examples[:2])
        return examples
    
    def validate_pattern_coverage(self, test_queries: List[str]) -> Dict[str, Any]:
        """Validate how well patterns cover a set of test queries"""
        total_queries = len(test_queries)
        matched_queries = 0
        pattern_usage = {}
        unmatched_queries = []
        
        for query in test_queries:
            match = self.match_pattern(query)
            if match and match.confidence > 0.7:
                matched_queries += 1
                pattern_name = match.pattern.name
                pattern_usage[pattern_name] = pattern_usage.get(pattern_name, 0) + 1
            else:
                unmatched_queries.append(query)
        
        coverage_percentage = (matched_queries / total_queries) * 100 if total_queries > 0 else 0
        
        return {
            'total_queries': total_queries,
            'matched_queries': matched_queries,
            'coverage_percentage': coverage_percentage,
            'pattern_usage': pattern_usage,
            'unmatched_queries': unmatched_queries,
            'most_used_patterns': sorted(pattern_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def add_custom_pattern(self, pattern: QueryPattern):
        """Add a custom pattern to the collection"""
        self.patterns.append(pattern)
        if pattern.pattern_type not in self.pattern_index:
            self.pattern_index[pattern.pattern_type] = []
        self.pattern_index[pattern.pattern_type].append(pattern)
        logger.info(f"Added custom pattern: {pattern.name}")
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about the pattern collection"""
        stats = {
            'total_patterns': len(self.patterns),
            'patterns_by_type': {},
            'average_confidence': 0.0,
            'high_confidence_patterns': 0
        }
        
        confidence_sum = 0.0
        for pattern in self.patterns:
            pattern_type = pattern.pattern_type.value
            stats['patterns_by_type'][pattern_type] = stats['patterns_by_type'].get(pattern_type, 0) + 1
            confidence_sum += pattern.confidence_score
            if pattern.confidence_score >= 0.9:
                stats['high_confidence_patterns'] += 1
        
        if self.patterns:
            stats['average_confidence'] = confidence_sum / len(self.patterns)
        
        return stats

#end-of-file