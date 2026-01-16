# Path: nl2sql/core/query_parser.py
# Filename: query_parser.py
# Purpose: Natural language query parser for extracting structured intent

"""
Natural Language Query Parser

Analyzes natural language queries to extract structured intent
for maritime database operations.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class QueryType(Enum):
    SELECT = "select"
    COUNT = "count"
    AGGREGATE = "aggregate"
    EXISTS = "exists"
    COMPARISON = "comparison"

class AggregateFunction(Enum):
    COUNT = "COUNT"
    SUM = "SUM" 
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"

class FilterOperator(Enum):
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    LIKE = "LIKE"
    ILIKE = "ILIKE"
    IN = "IN"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"

@dataclass
class FilterCondition:
    column: str
    operator: FilterOperator
    value: Any
    table: Optional[str] = None
    
@dataclass
class AggregateExpression:
    function: AggregateFunction
    column: str
    alias: Optional[str] = None
    table: Optional[str] = None

@dataclass
class OrderClause:
    column: str
    direction: str = "ASC"  # ASC or DESC
    table: Optional[str] = None

@dataclass
class JoinClause:
    table: str
    on_condition: str
    join_type: str = "INNER"  # INNER, LEFT, RIGHT, FULL

@dataclass
class QueryIntent:
    """Structured representation of parsed query intent"""
    query_type: QueryType
    target_tables: List[str] = field(default_factory=list)
    select_columns: List[str] = field(default_factory=list)
    filters: List[FilterCondition] = field(default_factory=list)
    aggregates: List[AggregateExpression] = field(default_factory=list)
    joins: List[JoinClause] = field(default_factory=list)
    order_by: List[OrderClause] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    confidence: float = 0.0
    raw_query: str = ""

class QueryParser:
    """Parses natural language queries into structured intent"""
    
    def __init__(self, schema_analyzer):
        self.schema = schema_analyzer
        self.entity_mappings = self._build_entity_mappings()
        self.keyword_patterns = self._build_keyword_patterns()
        self.date_patterns = self._build_date_patterns()
        
    def _build_entity_mappings(self) -> Dict[str, Dict[str, str]]:
        """Build mappings from natural language to database entities"""
        return {
            'tables': {
                # Vessels
                'ship': 'vessels',
                'ships': 'vessels',
                'vessel': 'vessels',
                'vessels': 'vessels',
                'boat': 'vessels',
                'boats': 'vessels',
                'craft': 'vessels',
                
                # Voyages  
                'voyage': 'voyages',
                'voyages': 'voyages',
                'trip': 'voyages',
                'trips': 'voyages',
                'journey': 'voyages',
                'journeys': 'voyages',
                'sailing': 'voyages',
                'travel': 'voyages',
                
                # Crew
                'crew': 'crew',
                'sailor': 'crew',
                'sailors': 'crew',
                'seaman': 'crew',
                'seamen': 'crew',
                'person': 'crew',
                'people': 'crew',
                'staff': 'crew',
                'member': 'crew',
                'members': 'crew',
                
                # Maintenance
                'maintenance': 'maintenance',
                'repair': 'maintenance',
                'repairs': 'maintenance',
                'service': 'maintenance',
                'work': 'maintenance',
                'fix': 'maintenance'
            },
            'columns': {
                # Common columns
                'name': 'name',
                'names': 'name',
                'title': 'name',
                'called': 'name',
                
                # Vessel attributes
                'type': 'vessel_type',
                'kind': 'vessel_type',
                'category': 'vessel_type',
                'class': 'vessel_type',
                'built': 'year_built',
                'constructed': 'year_built',
                'made': 'year_built',
                'year': 'year_built',
                'age': 'year_built',
                'size': 'gross_tonnage',
                'weight': 'gross_tonnage',
                'tonnage': 'gross_tonnage',
                'displacement': 'gross_tonnage',
                'length': 'length',
                'beam': 'beam',
                'width': 'beam',
                'draft': 'draft',
                'depth': 'draft',
                'flag': 'flag',
                'nationality': 'flag',
                'country': 'flag',
                'status': 'current_status',
                'condition': 'current_status',
                'state': 'current_status',
                
                # Voyage attributes
                'departure': 'departure_port',
                'origin': 'departure_port',
                'from': 'departure_port',
                'left': 'departure_port',
                'arrival': 'arrival_port',
                'destination': 'arrival_port',
                'to': 'arrival_port',
                'arrived': 'arrival_port',
                'cargo': 'cargo_type',
                'load': 'cargo_type',
                'freight': 'cargo_type',
                'goods': 'cargo_type',
                'carrying': 'cargo_type',
                
                # Crew attributes
                'position': 'position',
                'role': 'position',
                'job': 'position',
                'title': 'position',
                'rank': 'position',
                'joined': 'hire_date',
                'started': 'hire_date',
                'hired': 'hire_date',
                'left': 'date_left',
                'departed': 'date_left',
                'quit': 'date_left',
                
                # Maintenance attributes
                'cost': 'cost',
                'price': 'cost',
                'expense': 'cost',
                'spent': 'cost',
                'completed': 'completed',
                'finished': 'completed',
                'done': 'completed',
                'description': 'description',
                'details': 'description',
                'notes': 'notes'
            }
        }
    
    def _build_keyword_patterns(self) -> Dict[str, Any]:
        """Build patterns for different query types and operations"""
        return {
            'count_keywords': [
                'how many', 'count', 'number of', 'total number', 
                'how much', 'quantity', 'amount'
            ],
            'list_keywords': [
                'list', 'show', 'display', 'get', 'find', 'what are',
                'give me', 'tell me', 'which', 'what'
            ],
            'aggregate_keywords': {
                'average': ['average', 'avg', 'mean'],
                'sum': ['sum', 'total', 'add up'],
                'max': ['maximum', 'max', 'largest', 'biggest', 'highest'],
                'min': ['minimum', 'min', 'smallest', 'lowest']
            },
            'filter_keywords': {
                'time_before': ['before', 'prior to', 'earlier than'],
                'time_after': ['after', 'later than', 'since'],
                'time_between': ['between', 'from', 'during'],
                'comparison_greater': ['larger than', 'bigger than', 'greater than', 'more than', 'over'],
                'comparison_less': ['smaller than', 'less than', 'under', 'below'],
                'equality': ['is', 'equals', 'named', 'called'],
                'like': ['contains', 'includes', 'with', 'having']
            },
            'order_keywords': {
                'oldest': ('year_built', 'ASC'),
                'newest': ('year_built', 'DESC'),
                'largest': ('gross_tonnage', 'DESC'),
                'smallest': ('gross_tonnage', 'ASC'),
                'biggest': ('gross_tonnage', 'DESC'),
                'first': ('year_built', 'ASC'),
                'last': ('year_built', 'DESC'),
                'alphabetical': ('name', 'ASC')
            },
            'vessel_types': {
                # Map canonical forms to variations - FIXED: prevents duplicates
                'schooner': ['schooner', 'schooners'],
                'brig': ['brig', 'brigs'],
                'bark': ['bark', 'barks'],
                'sloop': ['sloop', 'sloops'],
                'ship': ['ship', 'ships'],
                'cargo': ['cargo', 'cargo ship', 'cargo ships'],
                'passenger': ['passenger', 'passenger ship', 'passenger ships'],
                'tanker': ['tanker', 'tankers'],
                'fishing': ['fishing', 'fishing boat', 'fishing boats'],
                'steamship': ['steamship', 'steamships', 'steamer', 'steamers']
            },
            'status_values': ['active', 'retired', 'decommissioned', 'lost'],
            'positions': [
                'captain', 'first mate', 'second mate', 'engineer', 'cook',
                'sailor', 'boatswain', 'pilot'
            ]
        }
    
    def _build_date_patterns(self) -> List[str]:
        """Build regex patterns for date recognition"""
        return [
            r'\b(\d{4})\b',  # Year only (1872)
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',  # MM/DD/YYYY
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',  # YYYY-MM-DD
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})\b'
        ]
    
    def parse(self, nl_query: str) -> QueryIntent:
        """Main parsing method - converts NL query to structured intent"""
        query = nl_query.lower().strip()
        
        intent = QueryIntent(
            query_type=QueryType.SELECT,
            raw_query=nl_query
        )
        
        # Step 1: Identify query type
        intent.query_type = self._identify_query_type(query)
        
        # Step 2: Extract target tables
        intent.target_tables = self._extract_tables(query)
        
        # Step 3: Extract columns to select/aggregate
        if intent.query_type == QueryType.AGGREGATE:
            intent.aggregates = self._extract_aggregates(query, intent.target_tables)
        else:
            intent.select_columns = self._extract_select_columns(query, intent.target_tables)
        
        # Step 4: Extract filters - FIXED VERSION
        intent.filters = self._extract_filters_fixed(query, intent.target_tables)
        
        # Step 5: Extract ordering
        intent.order_by = self._extract_ordering(query, intent.target_tables)
        
        # Step 6: Extract limit/offset
        intent.limit = self._extract_limit(query)
        intent.offset = self._extract_offset(query)
        
        # Step 7: Determine necessary joins
        intent.joins = self._determine_joins(intent.target_tables)
        
        # Step 8: Calculate confidence score
        intent.confidence = self._calculate_confidence(intent, query)
        
        logger.debug(f"Parsed query: {nl_query}")
        logger.debug(f"Intent: {intent}")
        
        return intent
    
    def _identify_query_type(self, query: str) -> QueryType:
        """Identify the primary type of query"""
        # Count queries
        for keyword in self.keyword_patterns['count_keywords']:
            if keyword in query:
                return QueryType.COUNT
        
        # Aggregate queries
        for agg_type, keywords in self.keyword_patterns['aggregate_keywords'].items():
            for keyword in keywords:
                if keyword in query:
                    return QueryType.AGGREGATE
        
        # Existence queries (does X exist, is there a Y)
        if any(phrase in query for phrase in ['does', 'is there', 'exists', 'any']):
            return QueryType.EXISTS
        
        # Comparison queries (which is larger, what's bigger)
        if any(word in query for word in ['which', 'what']) and \
           any(word in query for word in ['larger', 'bigger', 'smaller', 'better']):
            return QueryType.COMPARISON
        
        return QueryType.SELECT
    
    def _extract_tables(self, query: str) -> List[str]:
        """Extract relevant tables from the query"""
        tables = set()
        
        # Check for explicit table mentions
        for entity, table in self.entity_mappings['tables'].items():
            if entity in query:
                tables.add(table)
        
        # Check for implicit table references
        if any(word in query for word in ['voyage', 'trip', 'sailing', 'travel']):
            tables.add('voyages')
        
        if any(word in query for word in ['crew', 'captain', 'sailor', 'position']):
            tables.add('crew')
            
        if any(word in query for word in ['repair', 'maintenance', 'cost', 'service']):
            tables.add('maintenance')
        
        # Default to vessels if no specific table identified
        if not tables:
            tables.add('vessels')
        
        return list(tables)
    
    def _extract_select_columns(self, query: str, tables: List[str]) -> List[str]:
        """Extract columns to select based on query intent"""
        columns = []
        
        # Map natural language terms to columns
        for term, column in self.entity_mappings['columns'].items():
            if term in query:
                for table in tables:
                    table_info = self.schema.get_table_info(table)
                    if table_info and column in table_info.columns:
                        col_ref = f"{table}.{column}" if len(tables) > 1 else column
                        if col_ref not in columns:
                            columns.append(col_ref)
        
        # If no specific columns requested, use default for query type
        if not columns:
            if 'vessels' in tables:
                columns = ['name', 'vessel_type', 'year_built']
            elif 'voyages' in tables:
                columns = ['departure_port', 'arrival_port', 'departure_date']
            elif 'crew' in tables:
                columns = ['first_name', 'last_name', 'position']
            elif 'maintenance' in tables:
                columns = ['maintenance_date', 'maintenance_type', 'cost']
            else:
                columns = ['*']
        
        return columns
    
    def _extract_aggregates(self, query: str, tables: List[str]) -> List[AggregateExpression]:
        """Extract aggregation expressions"""
        aggregates = []
        
        # Count queries
        if any(keyword in query for keyword in self.keyword_patterns['count_keywords']):
            aggregates.append(AggregateExpression(
                function=AggregateFunction.COUNT,
                column='*',
                alias='count'
            ))
        
        # Other aggregations
        for agg_type, keywords in self.keyword_patterns['aggregate_keywords'].items():
            for keyword in keywords:
                if keyword in query:
                    if agg_type == 'average':
                        # Try to find what to average
                        if any(word in query for word in ['tonnage', 'size', 'weight']):
                            aggregates.append(AggregateExpression(
                                function=AggregateFunction.AVG,
                                column='gross_tonnage',
                                alias='avg_tonnage'
                            ))
                        elif any(word in query for word in ['cost', 'price']):
                            aggregates.append(AggregateExpression(
                                function=AggregateFunction.AVG,
                                column='cost',
                                alias='avg_cost'
                            ))
                    elif agg_type == 'sum':
                        if any(word in query for word in ['cost', 'price']):
                            aggregates.append(AggregateExpression(
                                function=AggregateFunction.SUM,
                                column='cost',
                                alias='total_cost'
                            ))
                    elif agg_type == 'max':
                        if any(word in query for word in ['tonnage', 'size']):
                            aggregates.append(AggregateExpression(
                                function=AggregateFunction.MAX,
                                column='gross_tonnage',
                                alias='max_tonnage'
                            ))
                    elif agg_type == 'min':
                        if any(word in query for word in ['tonnage', 'size']):
                            aggregates.append(AggregateExpression(
                                function=AggregateFunction.MIN,
                                column='gross_tonnage',
                                alias='min_tonnage'
                            ))
        
        return aggregates
    
    def _extract_filters_fixed(self, query: str, tables: List[str]) -> List[FilterCondition]:
        """FIXED VERSION: Extract filter conditions from query without duplicates"""
        filters = []
        
        # Year-based filters
        year_matches = re.findall(r'\b(\d{4})\b', query)
        for year_str in year_matches:
            year = int(year_str)
            if 1800 <= year <= 2030:  # Reasonable year range for maritime history
                if any(word in query for word in self.keyword_patterns['filter_keywords']['time_before']):
                    filters.append(FilterCondition(
                        column='year_built',
                        operator=FilterOperator.LESS_THAN,
                        value=year
                    ))
                elif any(word in query for word in self.keyword_patterns['filter_keywords']['time_after']):
                    filters.append(FilterCondition(
                        column='year_built',
                        operator=FilterOperator.GREATER_THAN,
                        value=year
                    ))
                elif 'in' in query:
                    filters.append(FilterCondition(
                        column='year_built',
                        operator=FilterOperator.EQUALS,
                        value=year
                    ))
        
        # FIXED: Vessel type filters - no more duplicates
        matched_vessel_type = self._find_best_vessel_type_match(query)
        if matched_vessel_type:
            filters.append(FilterCondition(
                column='vessel_type',
                operator=FilterOperator.ILIKE,
                value=f'%{matched_vessel_type}%'
            ))
        
        # Status filters
        for status in self.keyword_patterns['status_values']:
            if status in query:
                filters.append(FilterCondition(
                    column='current_status',
                    operator=FilterOperator.ILIKE,
                    value=f'%{status}%'
                ))
        
        # Position filters
        for position in self.keyword_patterns['positions']:
            if position in query:
                filters.append(FilterCondition(
                    column='position',
                    operator=FilterOperator.ILIKE,
                    value=f'%{position}%'
                ))
        
        # Port filters
        port_pattern = r'(?:from|to|at|in)\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)'
        port_matches = re.findall(port_pattern, query)
        for port in port_matches:
            if any(word in query for word in ['from', 'departure', 'left']):
                filters.append(FilterCondition(
                    column='departure_port',
                    operator=FilterOperator.ILIKE,
                    value=f'%{port}%'
                ))
            elif any(word in query for word in ['to', 'arrival', 'arrived']):
                filters.append(FilterCondition(
                    column='arrival_port',
                    operator=FilterOperator.ILIKE,
                    value=f'%{port}%'
                ))
        
        return filters
    
    def _find_best_vessel_type_match(self, query: str) -> Optional[str]:
        """FIXED: Find the best vessel type match without creating duplicates"""
        query_words = set(query.lower().split())
        
        best_match = None
        longest_match_length = 0
        
        # Check each canonical vessel type and its variations
        for canonical_type, variations in self.keyword_patterns['vessel_types'].items():
            for variation in variations:
                variation_words = set(variation.lower().split())
                
                # Check if all words in the variation are present in query
                if variation_words.issubset(query_words):
                    # Prefer longer, more specific matches
                    if len(variation) > longest_match_length:
                        best_match = canonical_type
                        longest_match_length = len(variation)
        
        return best_match
    
    def _extract_ordering(self, query: str, tables: List[str]) -> List[OrderClause]:
        """Extract ordering criteria"""
        order_clauses = []
        
        for keyword, (column, direction) in self.keyword_patterns['order_keywords'].items():
            if keyword in query:
                order_clauses.append(OrderClause(
                    column=column,
                    direction=direction
                ))
                break  # Only use the first ordering found
        
        return order_clauses
    
    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract limit from query"""
        # Look for explicit numbers
        number_matches = re.findall(r'\b(\d+)\b', query)
        for num_str in number_matches:
            num = int(num_str)
            if 1 <= num <= 1000:  # Reasonable limit range
                return num
        
        # Look for implicit limits
        if any(word in query for word in ['top', 'first']):
            return 10  # Default limit
        
        return None
    
    def _extract_offset(self, query: str) -> Optional[int]:
        """Extract offset from query"""
        # Look for skip/offset patterns
        offset_pattern = r'(?:skip|offset)\s+(\d+)'
        match = re.search(offset_pattern, query)
        if match:
            return int(match.group(1))
        
        return None
    
    def _determine_joins(self, tables: List[str]) -> List[JoinClause]:
        """Determine necessary joins between tables"""
        joins = []
        
        if len(tables) <= 1:
            return joins
        
        # Get relationships from schema
        for i, table1 in enumerate(tables):
            for table2 in tables[i+1:]:
                join_path = self.schema.find_join_path(table1, table2)
                if join_path:
                    for relationship in join_path:
                        join_condition = f"{relationship.from_table}.{relationship.from_column} = {relationship.to_table}.{relationship.to_column}"
                        joins.append(JoinClause(
                            table=relationship.to_table,
                            on_condition=join_condition,
                            join_type="INNER"
                        ))
        
        return joins
    
    def _calculate_confidence(self, intent: QueryIntent, query: str) -> float:
        """Calculate confidence score for the parsed intent"""
        confidence = 0.0
        
        # Base confidence for having tables
        if intent.target_tables:
            confidence += 0.3
        
        # Confidence for having appropriate columns/aggregates
        if intent.select_columns or intent.aggregates:
            confidence += 0.2
        
        # Confidence for recognized keywords
        recognized_keywords = 0
        total_keywords = 0
        
        for keyword_list in self.keyword_patterns.values():
            if isinstance(keyword_list, list):
                for keyword in keyword_list:
                    total_keywords += 1
                    if keyword in query:
                        recognized_keywords += 1
            elif isinstance(keyword_list, dict):
                for sublist in keyword_list.values():
                    if isinstance(sublist, list):
                        for keyword in sublist:
                            total_keywords += 1
                            if keyword in query:
                                recognized_keywords += 1
        
        if total_keywords > 0:
            confidence += 0.3 * (recognized_keywords / total_keywords)
        
        # Confidence for having filters
        if intent.filters:
            confidence += 0.2
        
        return min(confidence, 1.0)

#end-of-file