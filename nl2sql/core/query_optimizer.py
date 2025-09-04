# Path: nl2sql/core/query_optimizer.py
# Filename: query_optimizer.py
# Purpose: SQL query optimization and validation for performance and correctness

"""
Query Optimizer

Optimizes generated SQL queries for performance and validates them
for correctness before execution.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OptimizationLevel(Enum):
    BASIC = "basic"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"

@dataclass
class OptimizationRule:
    name: str
    description: str
    pattern: str
    replacement: str
    conditions: List[str] = None

@dataclass
class QueryAnalysis:
    original_sql: str
    optimized_sql: str
    applied_optimizations: List[str]
    performance_score: float
    warnings: List[str]
    errors: List[str]
    estimated_execution_time: Optional[float] = None

class QueryOptimizer:
    """Optimizes and validates SQL queries"""
    
    def __init__(self, schema_analyzer, optimization_level: OptimizationLevel = OptimizationLevel.BASIC):
        self.schema = schema_analyzer
        self.optimization_level = optimization_level
        self.optimization_rules = self._build_optimization_rules()
        self.validation_rules = self._build_validation_rules()
    
    def _build_optimization_rules(self) -> List[OptimizationRule]:
        """Build optimization rules based on common patterns"""
        return [
            OptimizationRule(
                name="add_exists_optimization",
                description="Convert COUNT(*) > 0 to EXISTS for better performance",
                pattern=r"SELECT COUNT\(\*\) FROM (.+)",
                replacement=r"SELECT EXISTS (SELECT 1 FROM \1)",
                conditions=["used_in_boolean_context"]
            ),
            OptimizationRule(
                name="limit_with_order",
                description="Add LIMIT when ORDER BY is present without explicit limit",
                pattern=r"(.*ORDER BY.*)(?!.*LIMIT)",
                replacement=r"\1 LIMIT 1000",
                conditions=["no_explicit_limit", "has_order_by"]
            ),
            OptimizationRule(
                name="index_hint_year_built",
                description="Ensure year_built filters use available indexes",
                pattern=r"WHERE (.*)year_built\s*([<>=]+)\s*(\d+)",
                replacement=r"WHERE \1year_built \2 \3",
                conditions=["year_built_indexed"]
            ),
            OptimizationRule(
                name="join_order_optimization",
                description="Optimize join order based on table sizes",
                pattern=r"FROM (\w+)\s+JOIN (\w+)",
                replacement=r"FROM \1 JOIN \2",
                conditions=["multiple_joins"]
            ),
            OptimizationRule(
                name="unnecessary_distinct",
                description="Remove DISTINCT when not needed",
                pattern=r"SELECT DISTINCT (.+) FROM (\w+) WHERE (.+)\.id\s*=",
                replacement=r"SELECT \1 FROM \2 WHERE \3.id =",
                conditions=["primary_key_in_where"]
            )
        ]
    
    def _build_validation_rules(self) -> Dict[str, Any]:
        """Build validation rules for query correctness"""
        return {
            'syntax_patterns': [
                (r"SELECT\s+", "Query must start with SELECT"),
                (r"FROM\s+\w+", "Query must have a valid FROM clause"),
                (r";\s*$", "Query should end with semicolon")
            ],
            'performance_patterns': [
                (r"SELECT \* FROM \w+ WHERE", "Avoid SELECT * in production queries"),
                (r"WHERE.*LIKE\s*'%.*%'", "Leading wildcard searches are slow"),
                (r"ORDER BY.*LIMIT\s+(\d+)", "Large LIMIT values may be inefficient")
            ],
            'security_patterns': [
                (r"'.*'", "Use parameterized queries instead of string literals"),
                (r"--", "Potential SQL injection risk with comments"),
                (r";.*DROP|DELETE|UPDATE", "Dangerous operations detected")
            ]
        }
    
    def optimize(self, sql: str, context: Dict[str, Any] = None) -> QueryAnalysis:
        """Main optimization method"""
        logger.debug(f"Optimizing SQL query with {self.optimization_level.value} level")
        
        original_sql = sql.strip()
        optimized_sql = original_sql
        applied_optimizations = []
        warnings = []
        errors = []
        
        # Step 1: Validate syntax and security
        syntax_errors = self._validate_syntax(optimized_sql)
        if syntax_errors:
            errors.extend(syntax_errors)
            return QueryAnalysis(
                original_sql=original_sql,
                optimized_sql=optimized_sql,
                applied_optimizations=applied_optimizations,
                performance_score=0.0,
                warnings=warnings,
                errors=errors
            )
        
        # Step 2: Apply optimization rules
        for rule in self.optimization_rules:
            if self._should_apply_rule(rule, optimized_sql, context):
                new_sql = self._apply_optimization_rule(rule, optimized_sql)
                if new_sql != optimized_sql:
                    optimized_sql = new_sql
                    applied_optimizations.append(rule.name)
                    logger.debug(f"Applied optimization: {rule.name}")
        
        # Step 3: Analyze performance
        performance_warnings = self._analyze_performance(optimized_sql)
        warnings.extend(performance_warnings)
        
        # Step 4: Calculate performance score
        performance_score = self._calculate_performance_score(optimized_sql, warnings)
        
        # Step 5: Add final optimizations based on schema
        optimized_sql = self._apply_schema_based_optimizations(optimized_sql)
        
        return QueryAnalysis(
            original_sql=original_sql,
            optimized_sql=optimized_sql,
            applied_optimizations=applied_optimizations,
            performance_score=performance_score,
            warnings=warnings,
            errors=errors
        )
    
    def _validate_syntax(self, sql: str) -> List[str]:
        """Validate SQL syntax"""
        errors = []
        
        # Basic syntax checks
        sql_upper = sql.upper()
        
        if not sql_upper.strip().startswith('SELECT'):
            errors.append("Query must start with SELECT")
        
        if 'FROM' not in sql_upper:
            errors.append("Query must contain FROM clause")
        
        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            errors.append("Unbalanced parentheses in query")
        
        # Check for SQL injection patterns
        dangerous_patterns = [
            r';\s*(DROP|DELETE|UPDATE|INSERT)\s+',
            r'UNION\s+SELECT',
            r'--\s*\w+',
            r'/\*.*\*/'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                errors.append(f"Potentially dangerous SQL pattern detected: {pattern}")
        
        return errors
    
    def _should_apply_rule(self, rule: OptimizationRule, sql: str, context: Dict[str, Any]) -> bool:
        """Determine if an optimization rule should be applied"""
        if not rule.conditions:
            return True
        
        context = context or {}
        
        for condition in rule.conditions:
            if condition == "used_in_boolean_context":
                # Check if COUNT is used in a boolean context
                if not re.search(r'COUNT\([^)]+\)\s*[><=]', sql):
                    return False
            elif condition == "no_explicit_limit":
                if 'LIMIT' in sql.upper():
                    return False
            elif condition == "has_order_by":
                if 'ORDER BY' not in sql.upper():
                    return False
            elif condition == "year_built_indexed":
                # Check if year_built column has an index
                for table_name in self.schema.tables:
                    table_info = self.schema.get_table_info(table_name)
                    if table_info and 'year_built' in table_info.columns:
                        # Assume indexed based on common patterns
                        return True
            elif condition == "multiple_joins":
                join_count = len(re.findall(r'\bJOIN\b', sql, re.IGNORECASE))
                if join_count < 2:
                    return False
            elif condition == "primary_key_in_where":
                # Check if WHERE clause contains primary key
                if not re.search(r'WHERE.*\.id\s*=', sql):
                    return False
        
        return True
    
    def _apply_optimization_rule(self, rule: OptimizationRule, sql: str) -> str:
        """Apply a specific optimization rule"""
        try:
            optimized = re.sub(rule.pattern, rule.replacement, sql, flags=re.IGNORECASE)
            return optimized
        except Exception as e:
            logger.warning(f"Failed to apply optimization rule {rule.name}: {e}")
            return sql
    
    def _analyze_performance(self, sql: str) -> List[str]:
        """Analyze query for performance issues"""
        warnings = []
        
        # Check for SELECT *
        if re.search(r'SELECT\s+\*', sql, re.IGNORECASE):
            warnings.append("Using SELECT * may impact performance - specify only needed columns")
        
        # Check for missing WHERE clause
        if 'WHERE' not in sql.upper() and 'LIMIT' not in sql.upper():
            warnings.append("Query without WHERE clause may return large result set")
        
        # Check for leading wildcard in LIKE
        if re.search(r"LIKE\s*'%", sql, re.IGNORECASE):
            warnings.append("Leading wildcard in LIKE clause prevents index usage")
        
        # Check for functions in WHERE clause
        function_patterns = [
            r'WHERE\s+\w+\([^)]+\)\s*[=<>]',
            r'WHERE\s+UPPER\(',
            r'WHERE\s+LOWER\(',
            r'WHERE\s+SUBSTR\('
        ]
        
        for pattern in function_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                warnings.append("Functions in WHERE clause may prevent index usage")
        
        # Check for large LIMIT values
        limit_match = re.search(r'LIMIT\s+(\d+)', sql, re.IGNORECASE)
        if limit_match:
            limit_value = int(limit_match.group(1))
            if limit_value > 1000:
                warnings.append(f"Large LIMIT value ({limit_value}) may impact performance")
        
        # Check for missing ORDER BY with LIMIT
        if 'LIMIT' in sql.upper() and 'ORDER BY' not in sql.upper():
            warnings.append("LIMIT without ORDER BY may return inconsistent results")
        
        return warnings
    
    def _calculate_performance_score(self, sql: str, warnings: List[str]) -> float:
        """Calculate a performance score from 0.0 to 1.0"""
        base_score = 1.0
        
        # Deduct points for each warning
        warning_penalty = len(warnings) * 0.1
        base_score -= warning_penalty
        
        # Bonus points for good practices
        if 'WHERE' in sql.upper():
            base_score += 0.1
        
        if 'LIMIT' in sql.upper():
            base_score += 0.1
        
        if not re.search(r'SELECT\s+\*', sql, re.IGNORECASE):
            base_score += 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))
    
    def _apply_schema_based_optimizations(self, sql: str) -> str:
        """Apply optimizations based on schema knowledge"""
        optimized_sql = sql
        
        # Add table aliases for better readability in complex queries
        if optimized_sql.count('JOIN') > 1:
            optimized_sql = self._add_table_aliases(optimized_sql)
        
        # Optimize date comparisons
        optimized_sql = self._optimize_date_comparisons(optimized_sql)
        
        # Add hints for common query patterns
        optimized_sql = self._add_query_hints(optimized_sql)
        
        return optimized_sql
    
    def _add_table_aliases(self, sql: str) -> str:
        """Add table aliases to complex queries"""
        # This is a simplified implementation
        # In practice, this would be more sophisticated
        
        table_aliases = {
            'vessels': 'v',
            'voyages': 'vo',
            'crew': 'c',
            'maintenance': 'm'
        }
        
        for table, alias in table_aliases.items():
            if table in sql and f'{table} {alias}' not in sql:
                sql = sql.replace(f'FROM {table}', f'FROM {table} {alias}')
                sql = sql.replace(f'JOIN {table}', f'JOIN {table} {alias}')
        
        return sql
    
    def _optimize_date_comparisons(self, sql: str) -> str:
        """Optimize date comparison operations"""
        # Convert string dates to proper date format
        date_pattern = r"(\w+)\s*([<>=]+)\s*'(\d{4}-\d{2}-\d{2})'"
        
        def replace_date(match):
            column, operator, date_str = match.groups()
            return f"{column} {operator} DATE '{date_str}'"
        
        return re.sub(date_pattern, replace_date, sql)
    
    def _add_query_hints(self, sql: str) -> str:
        """Add PostgreSQL-specific query hints where appropriate"""
        # Add index hints for common patterns
        if 'year_built' in sql:
            # Suggest using index on year_built
            sql = sql.replace(
                'WHERE year_built',
                '/* Use index on year_built */ WHERE year_built'
            )
        
        return sql
    
    def validate_against_schema(self, sql: str) -> List[str]:
        """Validate SQL against actual database schema"""
        errors = []
        
        # Extract table names from query
        table_pattern = r'FROM\s+(\w+)|JOIN\s+(\w+)'
        table_matches = re.findall(table_pattern, sql, re.IGNORECASE)
        
        for match in table_matches:
            table_name = match[0] or match[1]
            if table_name and not self.schema.get_table_info(table_name):
                errors.append(f"Table '{table_name}' does not exist in schema")
        
        # Extract column names and validate
        column_pattern = r'(\w+)\.(\w+)|SELECT\s+(\w+)|WHERE\s+(\w+)'
        column_matches = re.findall(column_pattern, sql, re.IGNORECASE)
        
        for match in column_matches:
            if match[0] and match[1]:  # qualified column
                table_name, column_name = match[0], match[1]
                if not self.schema.validate_column_exists(table_name, column_name):
                    errors.append(f"Column '{column_name}' does not exist in table '{table_name}'")
        
        return errors
    
    def get_execution_plan_estimate(self, sql: str) -> Dict[str, Any]:
        """Estimate query execution plan without running EXPLAIN"""
        plan = {
            'estimated_cost': 'medium',
            'scan_type': 'sequential',
            'join_strategy': 'nested_loop',
            'recommendations': []
        }
        
        # Analyze query structure
        if 'WHERE' not in sql.upper():
            plan['estimated_cost'] = 'high'
            plan['scan_type'] = 'sequential'
            plan['recommendations'].append("Add WHERE clause to reduce scan cost")
        
        if 'JOIN' in sql.upper():
            join_count = len(re.findall(r'\bJOIN\b', sql, re.IGNORECASE))
            if join_count > 2:
                plan['estimated_cost'] = 'high'
                plan['join_strategy'] = 'hash_join'
                plan['recommendations'].append("Consider breaking complex joins into smaller queries")
        
        if 'ORDER BY' in sql.upper() and 'LIMIT' not in sql.upper():
            plan['recommendations'].append("Add LIMIT to avoid sorting large result sets")
        
        return plan

#end-of-script