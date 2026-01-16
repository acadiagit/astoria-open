# utils/debug_duplicate_params.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from nl2sql.core.query_parser import QueryParser
from nl2sql.core.schema_analyzer import SchemaAnalyzer
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Initialize components
db_connection = psycopg2.connect(
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    dbname=os.getenv('POSTGRES_DB')
)

schema_analyzer = SchemaAnalyzer(db_connection)
query_parser = QueryParser(schema_analyzer)

# Test the problematic query
test_query = "list 4 brigs"
print(f"Testing: '{test_query}'")

intent = query_parser.parse(test_query)

print(f"Parsed intent:")
print(f"  Target tables: {intent.target_tables}")
print(f"  Filters: {intent.filters}")
print(f"  Confidence: {intent.confidence}")

# Check each filter
for i, filter_cond in enumerate(intent.filters):
    print(f"  Filter {i+1}:")
    print(f"    Column: {filter_cond.column}")
    print(f"    Operator: {filter_cond.operator}")
    print(f"    Value: {filter_cond.value}")
