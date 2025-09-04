# Path: nl2sql/core/sql_generator.py
# Filename: sql_generator.py
# Purpose: Rule-based SQL generation from structured query intent

"""
SQL Generator

Converts structured query intent into optimized PostgreSQL queries
with proper syntax validation and performance considerations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .query_parser import QueryIntent, QueryType, FilterOperator, AggregateFunction

logger = logging.getLogger(__name__)

@dataclass
class GeneratedSQL:
    """Container for generated SQL with metadata"""
    sql: str
    parameters: List[Any]
    estimated_rows: Optional[int] = None
    execution_plan: Optional[str] = None
    warnings: List[str] = None

class SQLGenerator:
    """Generates SQL queries from structured intent"""
    
    def __init__(self, schema_analyzer):
        self.schema = schema_analyzer
        self.sql_templates = self._build_sql_templates()
        
    def _build_sql_templates(self) -> Dict[str, str]:
        """Build reusable SQL templates"""
        return {
            'basic_select': """
                SELECT {select_clause}
                FROM {from_clause}
                {join_clause}
                {where_clause}
                {group_by_clause}
                {order_by_clause}
                {limit_clause}
            """,
            'count_query': """
                SELECT COUNT(*) as count
                FROM {from_clause}
                {join_clause}
                {where_clause}
            """,
            'aggregate_query': """
                SELECT {aggregate_clause}
                FROM {from_clause}
                {join_clause}
                {where_clause}
                {group_by_clause}
                {order_by_clause}
                {limit_clause}
            """
        }
    
    def generate(self, intent: QueryIntent) -> GeneratedSQL:
        """Main method to generate SQL from intent"""
        logger.debug(f"Generating SQL for intent: {intent.query_type}")
        
        try:
            if intent.query_type == QueryType.COUNT:
                return self._generate_count_query(intent)
            elif intent.query_type == QueryType.AGGREGATE:
                return self._generate_aggregate_query(intent)
            elif intent.query_type == QueryType.EXISTS:
                return self._generate_exists_query(intent)
            else:
                return self._generate_select_query(intent)
                
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise SQLGenerationError(f"Failed to generate SQL: {e}")
    
    def _generate_select_query(self, intent: QueryIntent) -> GeneratedSQL:
        """Generate a standard SELECT query"""
        select_clause = self._build_select_clause(intent)
        from_clause = self._build_from_clause(intent)
        join_clause = self._build_join_clause(intent)
        where_clause, parameters = self._build_where_clause(intent)
        group_by_clause = self._build_group_by_clause(intent)
        order_by_clause = self._build_order_by_clause(intent)
        limit_clause = self._build_limit_clause(intent)
        
        sql = self.sql_templates['basic_select'].format(
            select_clause=select_clause,
            from_clause=from_clause,
            join_clause=join_clause,
            where_clause=where_clause,
            group_by_clause=group_by_clause,
            order_by_clause=order_by_clause,
            limit_clause=limit_clause
        )
        
        # Clean up the SQL
        sql = self._clean_sql(sql)
        
        return GeneratedSQL(
            sql=sql,
            parameters=parameters,
            warnings=self._validate_query(intent)
        )
    
    def _generate_count_query(self, intent: QueryIntent) -> GeneratedSQL:
        """Generate a COUNT query"""
        from_clause = self._build_from_clause(intent)
        join_clause = self._build_join_clause(intent)
        where_clause, parameters = self._build_where_clause(intent)
        
        sql = self.sql_templates['count_query'].format(
            from_clause=from_clause,
            join_clause=join_clause,
            where_clause=where_clause
        )
        
        sql = self._clean_sql(sql)
        
        return GeneratedSQL(
            sql=sql,
            parameters=parameters,
            warnings=self._validate_query(intent)
        )
    
    def _generate_aggregate_query(self, intent: QueryIntent) -> GeneratedSQL:
        """Generate an aggregate query (SUM, AVG, etc.)"""
        aggregate_clause = self._build_aggregate_clause(intent)
        from_clause = self._build_from_clause(intent)
        join_clause = self._build_join_clause(intent)
        where_clause, parameters = self._build_where_clause(intent)
        group_by_clause = self._build_group_by_clause(intent)
        order_by_clause = self._build_order_by_clause(intent)
        limit_clause = self._build_limit_clause(intent)
        
        sql = self.sql_templates['aggregate_query'].format(
            aggregate_clause=aggregate_clause,
            from_clause=from_clause,
            join_clause=join_clause,
            where_clause=where_clause,
            group_by_clause=group_by_clause,
            order_by_clause=order_by_clause,
            limit_clause=limit_clause
        )
        
        sql = self._clean_sql(sql)
        
        return GeneratedSQL(
            sql=sql,
            parameters=parameters,
            warnings=self._validate_query(intent)
        )
    
    def _generate_exists_query(self, intent: QueryIntent) -> GeneratedSQL:
        """Generate an EXISTS query"""
        from_clause = self._build_from_clause(intent)
        join_clause = self._build_join_clause(intent)
        where_clause, parameters = self._build_where_clause(intent)
        
        sql = f"""
            SELECT EXISTS (
                SELECT 1
                FROM {from_clause}
                {join_clause}
                {where_clause}
            ) as exists_result
        """
        
        sql = self._clean_sql(sql)
        
        return GeneratedSQL(
            sql=sql,
            parameters=parameters,
            warnings=self._validate_query(intent)
        )
    
    def _build_select_clause(self, intent: QueryIntent) -> str:
        """Build the SELECT clause"""
        if not intent.select_columns:
            return "*"
        
        columns = []
        for column in intent.select_columns:
            if "." in column:
                # Already qualified
                columns.append(column)
            else:
                # Add table qualification if multiple tables
                if len(intent.target_tables) > 1:
                    # Find which table contains this column
                    table = self._find_column_table(column, intent.target_tables)
                    if table:
                        columns.append(f"{table}.{column}")
                    else:
                        columns.append(column)
                else:
                    columns.append(column)
        
        return ", ".join(columns)
    
    def _build_aggregate_clause(self, intent: QueryIntent) -> str:
        """Build the aggregate SELECT clause"""
        if not intent.aggregates:
            return "COUNT(*) as count"
        
        aggregates = []
        for agg in intent.aggregates:
            agg_str = f"{agg.function.value}({agg.column})"
            if agg.alias:
                agg_str += f" as {agg.alias}"
            aggregates.append(agg_str)
        
        return ", ".join(aggregates)
    
    def _build_from_clause(self, intent: QueryIntent) -> str:
        """Build the FROM clause"""
        if not intent.target_tables:
            raise SQLGenerationError("No target tables specified")
        
        # Use the first table as the main table
        return intent.target_tables[0]
    
    def _build_join_clause(self, intent: QueryIntent) -> str:
        """Build JOIN clauses"""
        if not intent.joins:
            return ""
        
        joins = []
        for join in intent.joins:
            join_str = f"{join.join_type} JOIN {join.table} ON {join.on_condition}"
            joins.append(join_str)
        
        return "\n".join(joins)
    
    def _build_where_clause(self, intent: QueryIntent) -> Tuple[str, List[Any]]:
        """Build WHERE clause with parameters"""
        if not intent.filters:
            return "", []
        
        conditions = []
        parameters = []
        
        for filter_cond in intent.filters:
            condition, param = self._build_filter_condition(filter_cond)
            conditions.append(condition)
            if param is not None:
                if isinstance(param, list):
                    parameters.extend(param)
                else:
                    parameters.append(param)
        
        if conditions:
            return f"WHERE {' AND '.join(conditions)}", parameters
        else:
            return "", parameters
    
    def _build_filter_condition(self, filter_cond) -> Tuple[str, Any]:
        """Build individual filter condition"""
        column = filter_cond.column
        operator = filter_cond.operator
        value = filter_cond.value
        
        # Add table qualification if needed
        if filter_cond.table:
            column = f"{filter_cond.table}.{column}"
        
        if operator == FilterOperator.EQUALS:
            return f"{column} = %s", value
        elif operator == FilterOperator.NOT_EQUALS:
            return f"{column} != %s", value
        elif operator == FilterOperator.GREATER_THAN:
            return f"{column} > %s", value
        elif operator == FilterOperator.LESS_THAN:
            return f"{column} < %s", value
        elif operator == FilterOperator.GREATER_EQUAL:
            return f"{column} >= %s", value
        elif operator == FilterOperator.LESS_EQUAL:
            return f"{column} <= %s", value
        elif operator == FilterOperator.LIKE:
            return f"{column} LIKE %s", value
        elif operator == FilterOperator.ILIKE:
            return f"{column} ILIKE %s", value
        elif operator == FilterOperator.IN:
            placeholders = ",".join(["%s"] * len(value))
            return f"{column} IN ({placeholders})", value
        elif operator == FilterOperator.BETWEEN:
            return f"{column} BETWEEN %s AND %s", [value[0], value[1]]
        elif operator == FilterOperator.IS_NULL:
            return f"{column} IS NULL", None
        elif operator == FilterOperator.IS_NOT_NULL:
            return f"{column} IS NOT NULL", None
        else:
            raise SQLGenerationError(f"Unsupported operator: {operator}")
    
    def _build_group_by_clause(self, intent: QueryIntent) -> str:
        """Build GROUP BY clause"""
        if not intent.group_by:
            return ""
        
        return f"GROUP BY {', '.join(intent.group_by)}"
    
    def _build_order_by_clause(self, intent: QueryIntent) -> str:
        """Build ORDER BY clause"""
        if not intent.order_by:
            return ""
        
        orders = []
        for order in intent.order_by:
            column = order.column
            if order.table:
                column = f"{order.table}.{column}"
            orders.append(f"{column} {order.direction}")
        
        return f"ORDER BY {', '.join(orders)}"
    
    def _build_limit_clause(self, intent: QueryIntent) -> str:
        """Build LIMIT clause"""
        clauses = []
        
        if intent.limit:
            clauses.append(f"LIMIT {intent.limit}")
        
        if intent.offset:
            clauses.append(f"OFFSET {intent.offset}")
        
        return " ".join(clauses)
    
    def _find_column_table(self, column: str, tables: List[str]) -> Optional[str]:
        """Find which table contains a given column"""
        for table in tables:
            table_info = self.schema.get_table_info(table)
            if table_info and column in table_info.columns:
                return table
        return None
    
    def _clean_sql(self, sql: str) -> str:
        """Clean up generated SQL"""
        # Remove extra whitespace and empty lines
        lines = [line.strip() for line in sql.split('\n') if line.strip()]
        
        # Join with single spaces, but preserve structure
        cleaned_lines = []
        for line in lines:
            if line.upper().startswith(('SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY', 'LIMIT')):
                cleaned_lines.append(line)
            else:
                cleaned_lines.append(f"  {line}")
        
        return '\n'.join(cleaned_lines)
    
    def _validate_query(self, intent: QueryIntent) -> List[str]:
        """Validate the generated query and return warnings"""
        warnings = []
        
        # Check for missing tables
        if not intent.target_tables:
            warnings.append("No target tables specified")
        
        # Check for invalid columns
        for column in intent.select_columns:
            if "." not in column:  # Not qualified
                found = False
                for table in intent.target_tables:
                    if self.schema.validate_column_exists(table, column):
                        found = True
                        break
                if not found:
                    warnings.append(f"Column '{column}' may not exist in specified tables")
        
        # Check for missing joins
        if len(intent.target_tables) > 1 and not intent.joins:
            warnings.append("Multiple tables specified but no joins defined")
        
        # Check for potentially expensive queries
        if not intent.filters and not intent.limit:
            warnings.append("Query may return large result set - consider adding filters or limit")
        
        return warnings
    
    def get_estimated_cost(self, intent: QueryIntent) -> Dict[str, Any]:
        """Estimate query execution cost"""
        cost = {
            'complexity': 'low',
            'estimated_rows': None,
            'recommendations': []
        }
        
        # Complexity estimation
        complexity_score = 0
        
        if len(intent.target_tables) > 1:
            complexity_score += 2
        
        if len(intent.joins) > 0:
            complexity_score += len(intent.joins)
        
        if len(intent.filters) == 0:
            complexity_score += 3
        
        if intent.aggregates:
            complexity_score += 1
        
        if complexity_score <= 2:
            cost['complexity'] = 'low'
        elif complexity_score <= 5:
            cost['complexity'] = 'medium'
        else:
            cost['complexity'] = 'high'
        
        # Recommendations
        if not intent.filters:
            cost['recommendations'].append("Add filters to improve performance")
        
        if len(intent.target_tables) > 1 and not intent.joins:
            cost['recommendations'].append("Define explicit joins for better performance")
        
        if not intent.limit and cost['complexity'] != 'low':
            cost['recommendations'].append("Consider adding LIMIT clause")
        
        return cost

class SQLGenerationError(Exception):
    """Exception raised when SQL generation fails"""
    pass

#end-of-script