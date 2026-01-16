# Path: utils/debug_data_reality.py
# Filename: debug_data_reality.py
# Execute from: astoria_open (project root)

"""
Data Reality Check

Connects to PostgreSQL database to understand actual data structure
vs. expected patterns in the maritime NL2SQL system.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
from collections import Counter

def connect_to_database():
    """Establish PostgreSQL connection"""
    load_dotenv()
    
    try:
        connection = psycopg2.connect(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            database=os.getenv('POSTGRES_DB')
        )
        print("✅ Database connection successful")
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def analyze_vessel_types(connection):
    """Analyze actual vessel types in the database"""
    print("\n" + "="*60)
    print("VESSEL TYPE ANALYSIS")
    print("="*60)
    
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        # Get all distinct vessel types
        cursor.execute("""
            SELECT 
                vessel_type,
                COUNT(*) as count,
                MIN(name) as example_vessel
            FROM vessels 
            WHERE vessel_type IS NOT NULL
            GROUP BY vessel_type 
            ORDER BY count DESC
        """)
        
        vessel_types = cursor.fetchall()
        
        print(f"Found {len(vessel_types)} distinct vessel types:")
        for vt in vessel_types:
            print(f"  - '{vt['vessel_type']}': {vt['count']} vessels (e.g., {vt['example_vessel']})")
        
        # Check for specific types mentioned in patterns
        expected_types = ['brig', 'Brig', 'BRIG', 'schooner', 'Schooner', 'SCHOONER']
        print(f"\nChecking for expected pattern types:")
        
        for expected in expected_types:
            cursor.execute("SELECT COUNT(*) as count FROM vessels WHERE vessel_type = %s", (expected,))
            count = cursor.fetchone()['count']
            print(f"  - '{expected}': {count} vessels")
        
        # Check case-insensitive matches
        print(f"\nCase-insensitive pattern matches:")
        pattern_searches = ['brig', 'schooner', 'cargo', 'passenger', 'tanker', 'fishing']
        
        for pattern in pattern_searches:
            cursor.execute("SELECT COUNT(*) as count FROM vessels WHERE vessel_type ILIKE %s", (f'%{pattern}%',))
            count = cursor.fetchone()['count']
            if count > 0:
                cursor.execute("SELECT DISTINCT vessel_type FROM vessels WHERE vessel_type ILIKE %s", (f'%{pattern}%',))
                matches = [row['vessel_type'] for row in cursor.fetchall()]
                print(f"  - '{pattern}': {count} vessels - Types: {matches}")
            else:
                print(f"  - '{pattern}': {count} vessels")
        
        return vessel_types

def analyze_table_structure(connection):
    """Analyze table structure and comments"""
    print("\n" + "="*60)
    print("TABLE STRUCTURE ANALYSIS")
    print("="*60)
    
    tables = ['vessels', 'voyages', 'crew', 'maintenance']
    
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        for table in tables:
            print(f"\n--- {table.upper()} TABLE ---")
            
            # Get table comment
            cursor.execute("""
                SELECT obj_description(c.oid) as comment
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = %s AND n.nspname = 'public'
            """, (table,))
            
            comment_result = cursor.fetchone()
            if comment_result and comment_result['comment']:
                print(f"Comment: {comment_result['comment']}")
            else:
                print("Comment: No comment found")
            
            # Get column information
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table,))
            
            columns = cursor.fetchall()
            print(f"Columns ({len(columns)}):")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  - {col['column_name']}: {col['data_type']} {nullable}{default}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"Total rows: {count}")

def analyze_sample_data(connection):
    """Analyze sample data from each table"""
    print("\n" + "="*60)
    print("SAMPLE DATA ANALYSIS")
    print("="*60)
    
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        # Vessels sample
        print(f"\n--- VESSELS SAMPLE (first 5) ---")
        cursor.execute("SELECT name, vessel_type, year_built, gross_tonnage FROM vessels ORDER BY name LIMIT 5")
        vessels = cursor.fetchall()
        for vessel in vessels:
            print(f"  {vessel['name']} | {vessel['vessel_type']} | {vessel['year_built']} | {vessel['gross_tonnage']}")
        
        # Voyages sample
        print(f"\n--- VOYAGES SAMPLE (first 3) ---")
        cursor.execute("""
            SELECT v.name as vessel_name, vo.departure_port, vo.arrival_port, vo.cargo
            FROM voyages vo 
            JOIN vessels v ON vo.vessel_id = v.id 
            ORDER BY vo.departure_date 
            LIMIT 3
        """)
        voyages = cursor.fetchall()
        for voyage in voyages:
            print(f"  {voyage['vessel_name']}: {voyage['departure_port']} → {voyage['arrival_port']} | {voyage['cargo']}")
        
        # Crew sample
        print(f"\n--- CREW SAMPLE (first 3) ---")
        cursor.execute("""
            SELECT c.name, c.position, v.name as vessel_name
            FROM crew c 
            JOIN vessels v ON c.vessel_id = v.id 
            ORDER BY c.name 
            LIMIT 3
        """)
        crew = cursor.fetchall()
        for member in crew:
            print(f"  {member['name']} | {member['position']} | {member['vessel_name']}")

def test_problematic_queries(connection):
    """Test the specific queries that are failing"""
    print("\n" + "="*60)
    print("PROBLEMATIC QUERY TESTING")
    print("="*60)
    
    test_queries = [
        ("Direct 'brig' search", "SELECT COUNT(*) FROM vessels WHERE vessel_type = 'brig'"),
        ("Case-insensitive 'brig'", "SELECT COUNT(*) FROM vessels WHERE vessel_type ILIKE '%brig%'"),
        ("Direct 'Brig' search", "SELECT COUNT(*) FROM vessels WHERE vessel_type = 'Brig'"),
        ("List all containing 'brig'", "SELECT name, vessel_type FROM vessels WHERE vessel_type ILIKE '%brig%'"),
        ("Schooner test", "SELECT name, vessel_type FROM vessels WHERE vessel_type ILIKE '%schooner%' LIMIT 3"),
        ("Duplicate condition test", "SELECT name, vessel_type FROM vessels WHERE vessel_type ILIKE '%schooner%' AND vessel_type ILIKE '%schooner%'"),
    ]
    
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        for desc, query in test_queries:
            print(f"\n--- {desc} ---")
            print(f"Query: {query}")
            try:
                cursor.execute(query)
                results = cursor.fetchall()
                
                if query.startswith("SELECT COUNT"):
                    print(f"Result: {results[0]['count']} rows")
                else:
                    print(f"Results ({len(results)} rows):")
                    for row in results[:5]:  # Show first 5 results
                        if 'name' in row and 'vessel_type' in row:
                            print(f"  - {row['name']}: {row['vessel_type']}")
                        else:
                            print(f"  - {dict(row)}")
                    if len(results) > 5:
                        print(f"  ... and {len(results) - 5} more")
                        
            except Exception as e:
                print(f"❌ Query failed: {e}")

def analyze_pattern_expectations():
    """Analyze what the maritime patterns expect vs reality"""
    print("\n" + "="*60)
    print("PATTERN EXPECTATION ANALYSIS")
    print("="*60)
    
    # These are from your maritime_patterns.py
    expected_vessel_types = [
        'schooner', 'schooners', 'brig', 'brigs', 'cargo', 'passenger',
        'tanker', 'tankers', 'fishing', 'trawler', 'yacht', 'steamship'
    ]
    
    expected_patterns = [
        "list all vessels",
        "show schooners", 
        "find tankers",
        "list 4 brigs",
        "show largest vessels",
        "oldest vessels"
    ]
    
    print("Expected vessel types from patterns:")
    for vt in expected_vessel_types:
        print(f"  - {vt}")
    
    print(f"\nExpected query patterns:")
    for pattern in expected_patterns:
        print(f"  - \"{pattern}\"")
    
    print(f"\nPattern regex examples:")
    regex_examples = [
        (r'^(?:list|show|find|get)\s+(?:all\s+)?(?:vessels?|ships?|boats?)$', "list all vessels"),
        (r'^(?:list|show|find|get)\s+(?:all\s+)?(?P<vessel_type>schooners?|brigs?|cargo\s+ships?)$', "list brigs"),
        (r'^(?:show|list|find|get)\s+(?:the\s+)?(?P<limit>\d+)?\s*(?:largest|biggest)\s+(?:vessels?|ships?)$', "show 5 largest ships")
    ]
    
    for regex, example in regex_examples:
        print(f"  - Pattern: {regex}")
        print(f"    Example: \"{example}\"")

def generate_recommendations(vessel_types):
    """Generate recommendations based on findings"""
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    print("Based on the data analysis, here are the key issues and recommendations:")
    
    print(f"\n1. VESSEL TYPE MISMATCH:")
    actual_types = [vt['vessel_type'] for vt in vessel_types]
    expected_patterns = ['brig', 'brigs', 'schooner', 'schooners']
    
    print(f"   - Your patterns expect: {expected_patterns}")
    print(f"   - Your database contains: {actual_types}")
    print(f"   - Recommendation: Update maritime_patterns.py to match actual data")
    
    print(f"\n2. CASE SENSITIVITY:")
    print(f"   - Your patterns use lowercase matching")
    print(f"   - Your database may have different casing")
    print(f"   - Recommendation: Ensure consistent ILIKE usage")
    
    print(f"\n3. SYNONYM MAPPING:")
    print(f"   - Your table comments mention many synonyms")
    print(f"   - Your patterns don't leverage all synonyms")
    print(f"   - Recommendation: Expand entity mappings in query_parser.py")
    
    print(f"\n4. DUPLICATE PARAMETER BUG:")
    print(f"   - The 'ILIKE %s AND ILIKE %s' suggests parameter processing error")
    print(f"   - Check _process_parameter_value() in maritime_patterns.py")
    print(f"   - Recommendation: Debug parameter binding logic")
    
    print(f"\n5. FALLBACK STRATEGY:")
    print(f"   - When rule-based fails, fallback to LLM isn't seamless")
    print(f"   - Recommendation: Improve error handling and fallback logic")

def main():
    """Main debugging function"""
    print("🚢 DATA REALITY CHECK - MARITIME NL2SQL DEBUGGING")
    print("="*60)
    print("This script analyzes the actual PostgreSQL database content")
    print("vs. expected patterns in your maritime NL2SQL system.")
    print("="*60)
    
    # Connect to database
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        # Run all analysis functions
        vessel_types = analyze_vessel_types(connection)
        analyze_table_structure(connection)
        analyze_sample_data(connection)
        test_problematic_queries(connection)
        analyze_pattern_expectations()
        generate_recommendations(vessel_types)
        
        print(f"\n🎯 NEXT STEPS:")
        print("1. Run utils/debug_pattern_matching.py to isolate the duplicate parameter bug")
        print("2. Run utils/debug_pipeline_flow.py to test the full processing pipeline")
        print("3. Update maritime patterns based on actual database content")
        print("4. Test case-insensitive matching improvements")
        
    finally:
        connection.close()
        print(f"\n✅ Database connection closed")

if __name__ == "__main__":
    main()

#end-of-file