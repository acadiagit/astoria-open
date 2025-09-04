# Path: nl2sql/core/schema_analyzer.py
# Filename: schema_analyzer.py
# Purpose: Dynamic database schema analysis and relationship mapping

"""
Dynamic Database Schema Analysis

Automatically discovers and analyzes database schema structure,
relationships, and metadata for intelligent query generation.
"""

import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class ColumnType(Enum):
    TEXT = "text"
    INTEGER = "integer" 
    NUMERIC = "numeric"
    TIMESTAMP = "timestamp"
    BOOLEAN = "boolean"
    FOREIGN_KEY = "foreign_key"

@dataclass
class ColumnInfo:
    name: str
    data_type: ColumnType
    is_nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    foreign_table: Optional[str] = None
    foreign_column: Optional[str] = None
    max_length: Optional[int] = None
    description: Optional[str] = None

@dataclass 
class TableInfo:
    name: str
    columns: Dict[str, ColumnInfo]
    primary_keys: List[str]
    foreign_keys: Dict[str, Tuple[str, str]]  # column -> (table, column)
    indexes: List[str]
    description: Optional[str] = None

@dataclass
class RelationshipInfo:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: str  # "one_to_many", "many_to_one", "many_to_many"

class SchemaAnalyzer:
    """Analyzes PostgreSQL database schema for intelligent query generation"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.tables: Dict[str, TableInfo] = {}
        self.relationships: List[RelationshipInfo] = []
        self.table_aliases: Dict[str, str] = {}
        self._load_schema()
        
    def _load_schema(self):
        """Load complete schema information from database"""
        logger.info("Loading database schema...")
        
        # Load table information
        self._load_tables()
        
        # Load column information  
        self._load_columns()
        
        # Load relationships
        self._load_relationships()
        
        # Load indexes
        self._load_indexes()
        
        # Load comments (PostgreSQL specific)
        self._load_comments()
        
        # Build table aliases
        self._build_table_aliases()
        
        logger.info(f"Schema loaded: {len(self.tables)} tables, {len(self.relationships)} relationships")
    
    def _load_tables(self):
        """Load all tables in the public schema"""
        with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            for row in cursor.fetchall():
                table_name = row['table_name']
                self.tables[table_name] = TableInfo(
                    name=table_name,
                    columns={},
                    primary_keys=[],
                    foreign_keys={},
                    indexes=[],
                    description=None
                )
    
    def _load_columns(self):
        """Load column information for all tables"""
        with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.character_maximum_length,
                    c.column_default,
                    CASE WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY'
                         WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY'
                         ELSE NULL END as constraint_type
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT kcu.table_name, kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = 'public'
                ) pk ON c.table_name = pk.table_name AND c.column_name = pk.column_name
                LEFT JOIN (
                    SELECT kcu.table_name, kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                ) fk ON c.table_name = fk.table_name AND c.column_name = fk.column_name
                WHERE c.table_schema = 'public'
                ORDER BY c.table_name, c.ordinal_position
            """)
            
            for row in cursor.fetchall():
                table_name = row['table_name']
                column_name = row['column_name']
                
                if table_name not in self.tables:
                    continue
                
                # Map PostgreSQL types to our enum
                pg_type = row['data_type'].lower()
                if pg_type in ['character varying', 'varchar', 'text', 'char']:
                    column_type = ColumnType.TEXT
                elif pg_type in ['integer', 'bigint', 'smallint', 'serial', 'bigserial']:
                    column_type = ColumnType.INTEGER
                elif pg_type in ['numeric', 'decimal', 'real', 'double precision']:
                    column_type = ColumnType.NUMERIC
                elif pg_type in ['timestamp', 'timestamptz', 'date', 'time']:
                    column_type = ColumnType.TIMESTAMP
                elif pg_type == 'boolean':
                    column_type = ColumnType.BOOLEAN
                else:
                    column_type = ColumnType.TEXT  # Default fallback
                
                is_primary_key = row['constraint_type'] == 'PRIMARY KEY'
                is_foreign_key = row['constraint_type'] == 'FOREIGN KEY'
                
                column_info = ColumnInfo(
                    name=column_name,
                    data_type=column_type,
                    is_nullable=row['is_nullable'] == 'YES',
                    is_primary_key=is_primary_key,
                    is_foreign_key=is_foreign_key,
                    max_length=row['character_maximum_length'],
                    description=None  # Will be populated in _load_comments
                )
                
                self.tables[table_name].columns[column_name] = column_info
                
                if is_primary_key:
                    self.tables[table_name].primary_keys.append(column_name)
    
    def _load_relationships(self):
        """Load foreign key relationships between tables"""
        with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    tc.table_name as from_table,
                    kcu.column_name as from_column,
                    ccu.table_name as to_table,
                    ccu.column_name as to_column,
                    tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            """)
            
            for row in cursor.fetchall():
                from_table = row['from_table']
                from_column = row['from_column']
                to_table = row['to_table']
                to_column = row['to_column']
                
                # Add to relationships list
                relationship = RelationshipInfo(
                    from_table=from_table,
                    from_column=from_column,
                    to_table=to_table,
                    to_column=to_column,
                    relationship_type="many_to_one"  # FK relationships are typically many-to-one
                )
                self.relationships.append(relationship)
                
                # Update foreign key info in tables
                if from_table in self.tables and from_column in self.tables[from_table].columns:
                    self.tables[from_table].columns[from_column].foreign_table = to_table
                    self.tables[from_table].columns[from_column].foreign_column = to_column
                    self.tables[from_table].foreign_keys[from_column] = (to_table, to_column)
    
    def _load_indexes(self):
        """Load index information for tables"""
        with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    t.relname as table_name,
                    i.relname as index_name
                FROM pg_class t
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                WHERE n.nspname = 'public'
                AND t.relkind = 'r'
                ORDER BY t.relname, i.relname
            """)
            
            for row in cursor.fetchall():
                table_name = row['table_name']
                index_name = row['index_name']
                
                if table_name in self.tables:
                    if index_name not in self.tables[table_name].indexes:
                        self.tables[table_name].indexes.append(index_name)
    
    def _load_comments(self):
        """Load PostgreSQL comments for tables and columns (if available)"""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                # Load table comments
                cursor.execute("""
                    SELECT 
                        c.relname as table_name,
                        obj_description(c.oid) as table_comment
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public'
                    AND c.relkind = 'r'
                    AND obj_description(c.oid) IS NOT NULL
                """)
                
                for row in cursor.fetchall():
                    table_name = row['table_name']
                    comment = row['table_comment']
                    if table_name in self.tables and comment:
                        self.tables[table_name].description = comment.strip()
                
                # Load column comments
                cursor.execute("""
                    SELECT 
                        c.relname as table_name,
                        a.attname as column_name,
                        col_description(c.oid, a.attnum) as column_comment
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    JOIN pg_attribute a ON a.attrelid = c.oid
                    WHERE n.nspname = 'public'
                    AND c.relkind = 'r'
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                    AND col_description(c.oid, a.attnum) IS NOT NULL
                """)
                
                for row in cursor.fetchall():
                    table_name = row['table_name']
                    column_name = row['column_name']
                    comment = row['column_comment']
                    
                    if (table_name in self.tables and 
                        column_name in self.tables[table_name].columns and 
                        comment):
                        self.tables[table_name].columns[column_name].description = comment.strip()
                
                logger.debug("PostgreSQL comments loaded successfully")
                
        except Exception as e:
            logger.warning(f"Could not load PostgreSQL comments: {e}")
            # This is not critical - the system works without comments
    
    def _build_table_aliases(self):
        """Build common aliases for table names"""
        for table_name in self.tables.keys():
            # Create short aliases
            if table_name == 'vessels':
                self.table_aliases.update({
                    'ship': 'vessels',
                    'ships': 'vessels', 
                    'boat': 'vessels',
                    'boats': 'vessels',
                    'vessel': 'vessels'
                })
            elif table_name == 'voyages':
                self.table_aliases.update({
                    'voyage': 'voyages',
                    'trip': 'voyages',
                    'trips': 'voyages',
                    'journey': 'voyages',
                    'journeys': 'voyages'
                })
            elif table_name == 'crew':
                self.table_aliases.update({
                    'sailor': 'crew',
                    'sailors': 'crew',
                    'seamen': 'crew',
                    'people': 'crew'
                })
            elif table_name == 'maintenance':
                self.table_aliases.update({
                    'repair': 'maintenance',
                    'repairs': 'maintenance',
                    'service': 'maintenance'
                })
    
    def get_table_info(self, table_name: str) -> Optional[TableInfo]:
        """Get information for a specific table"""
        # Try direct lookup first
        if table_name in self.tables:
            return self.tables[table_name]
        
        # Try alias lookup
        if table_name in self.table_aliases:
            return self.tables[self.table_aliases[table_name]]
        
        return None
    
    def find_tables_by_alias(self, alias: str) -> List[str]:
        """Find table names that match an alias"""
        matches = []
        
        # Direct match
        if alias in self.tables:
            matches.append(alias)
        
        # Alias match
        if alias in self.table_aliases:
            matches.append(self.table_aliases[alias])
        
        # Partial match
        for table_name in self.tables.keys():
            if alias.lower() in table_name.lower():
                matches.append(table_name)
        
        return list(set(matches))  # Remove duplicates
    
    def get_column_info(self, table_name: str, column_name: str) -> Optional[ColumnInfo]:
        """Get information for a specific column"""
        table_info = self.get_table_info(table_name)
        if table_info and column_name in table_info.columns:
            return table_info.columns[column_name]
        return None
    
    def find_columns_by_name(self, column_name: str) -> List[Tuple[str, ColumnInfo]]:
        """Find all columns with a given name across all tables"""
        matches = []
        for table_name, table_info in self.tables.items():
            if column_name in table_info.columns:
                matches.append((table_name, table_info.columns[column_name]))
        return matches
    
    def get_related_tables(self, table_name: str) -> List[Tuple[str, str]]:
        """Get all tables related to the given table via foreign keys"""
        related = []
        
        for relationship in self.relationships:
            if relationship.from_table == table_name:
                related.append((relationship.to_table, 'references'))
            elif relationship.to_table == table_name:
                related.append((relationship.from_table, 'referenced_by'))
        
        return related
    
    def find_join_path(self, table1: str, table2: str) -> Optional[List[RelationshipInfo]]:
        """Find the shortest join path between two tables"""
        if table1 == table2:
            return []
        
        # Simple direct relationship check
        for relationship in self.relationships:
            if ((relationship.from_table == table1 and relationship.to_table == table2) or
                (relationship.from_table == table2 and relationship.to_table == table1)):
                return [relationship]
        
        # For now, only handle direct relationships
        # TODO: Implement multi-hop path finding using graph algorithms
        return None
    
    def get_searchable_columns(self, table_name: str) -> List[str]:
        """Get columns that are good for text searching"""
        table_info = self.get_table_info(table_name)
        if not table_info:
            return []
        
        searchable = []
        for column_name, column_info in table_info.columns.items():
            if column_info.data_type == ColumnType.TEXT:
                searchable.append(column_name)
        
        return searchable
    
    def get_filterable_columns(self, table_name: str) -> Dict[str, ColumnType]:
        """Get columns that are good for filtering with their types"""
        table_info = self.get_table_info(table_name)
        if not table_info:
            return {}
        
        filterable = {}
        for column_name, column_info in table_info.columns.items():
            if column_info.data_type in [ColumnType.INTEGER, ColumnType.NUMERIC, 
                                       ColumnType.TIMESTAMP, ColumnType.TEXT]:
                filterable[column_name] = column_info.data_type
        
        return filterable
    
    def get_aggregatable_columns(self, table_name: str) -> List[str]:
        """Get columns suitable for aggregation (COUNT, SUM, AVG, etc.)"""
        table_info = self.get_table_info(table_name)
        if not table_info:
            return []
        
        aggregatable = []
        for column_name, column_info in table_info.columns.items():
            if column_info.data_type in [ColumnType.INTEGER, ColumnType.NUMERIC]:
                aggregatable.append(column_name)
        
        return aggregatable
    
    def validate_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        return self.get_column_info(table_name, column_name) is not None
    
    def suggest_columns(self, table_name: str, partial_name: str) -> List[str]:
        """Suggest column names based on partial input"""
        table_info = self.get_table_info(table_name)
        if not table_info:
            return []
        
        suggestions = []
        partial_lower = partial_name.lower()
        
        for column_name in table_info.columns.keys():
            if partial_lower in column_name.lower():
                suggestions.append(column_name)
        
        return suggestions
    
    def get_schema_summary(self) -> Dict:
        """Get a summary of the entire schema"""
        summary = {
            'tables': {},
            'total_tables': len(self.tables),
            'total_relationships': len(self.relationships),
            'has_comments': False
        }
        
        comments_found = 0
        for table_name, table_info in self.tables.items():
            table_summary = {
                'columns': len(table_info.columns),
                'primary_keys': table_info.primary_keys,
                'foreign_keys': list(table_info.foreign_keys.keys()),
                'indexes': len(table_info.indexes),
                'description': table_info.description
            }
            
            if table_info.description:
                comments_found += 1
            
            # Count column comments
            column_comments = sum(1 for col in table_info.columns.values() if col.description)
            table_summary['column_comments'] = column_comments
            comments_found += column_comments
            
            summary['tables'][table_name] = table_summary
        
        summary['has_comments'] = comments_found > 0
        summary['total_comments'] = comments_found
        
        return summary

#end-of-file