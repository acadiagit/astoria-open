# Path: nl2sql/core/__init__.py
# Filename: __init__.py
# Purpose: Core NL2SQL components package initialization

"""
Core NL2SQL Components

Contains the fundamental building blocks for natural language to SQL conversion:
- Schema analysis and introspection
- Query parsing and intent extraction  
- SQL generation from structured intent
- Query optimization and validation
"""

from .schema_analyzer import SchemaAnalyzer, TableInfo, ColumnInfo, RelationshipInfo
from .query_parser import QueryParser, QueryIntent, QueryType, FilterCondition
from .sql_generator import SQLGenerator
from .query_optimizer import QueryOptimizer

__all__ = [
    'SchemaAnalyzer',
    'TableInfo', 
    'ColumnInfo',
    'RelationshipInfo',
    'QueryParser',
    'QueryIntent',
    'QueryType',
    'FilterCondition',
    'SQLGenerator',
    'QueryOptimizer'
]

#end-of-script