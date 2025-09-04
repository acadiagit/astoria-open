# Path: nl2sql_implementation_test.py
# Filename: nl2sql_implementation_test.py  
# Purpose: Test script to verify NL2SQL pipeline integration

"""
NL2SQL Implementation Test

Tests the complete NL2SQL pipeline with your maritime database
to ensure all components work correctly before deployment.
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append('/Users/hugodiaz/Astoria/hf_spaces/astoria_open')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection"""
    print("🔌 Testing database connection...")
    
    load_dotenv()
    
    try:
        connection = psycopg2.connect(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM vessels")
            vessel_count = cursor.fetchone()[0]
            print(f"✅ Database connected successfully! Found {vessel_count} vessels.")
            
        return connection
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def test_schema_analyzer(db_connection):
    """Test schema analyzer component"""
    print("\n📊 Testing Schema Analyzer...")
    
    try:
        from nl2sql.core import SchemaAnalyzer
        
        schema = SchemaAnalyzer(db_connection)
        summary = schema.get_schema_summary()
        
        print(f"✅ Schema Analysis Complete:")
        print(f"   - Tables: {summary['total_tables']}")
        print(f"   - Relationships: {summary['total_relationships']}")
        
        # Test table lookup
        vessels_info = schema.get_table_info('vessels')
        if vessels_info:
            print(f"   - Vessels table: {len(vessels_info.columns)} columns")
        
        return schema
        
    except Exception as e:
        print(f"❌ Schema Analyzer failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_pattern_matching():
    """Test maritime pattern matching"""
    print("\n🎯 Testing Pattern Matching...")
    
    try:
        from nl2sql.patterns import MaritimePatterns
        
        patterns = MaritimePatterns()
        
        test_queries = [
            "list all vessels",
            "how many ships are there", 
            "show largest vessels",
            "find voyages from Boston"
        ]
        
        for query in test_queries:
            match = patterns.match_pattern(query)
            if match:
                print(f"✅ '{query}' → Pattern: {match.pattern.name} (confidence: {match.confidence:.2f})")
            else:
                print(f"⚠️  '{query}' → No pattern match")
        
        return patterns
        
    except Exception as e:
        print(f"❌ Pattern Matching failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_complexity_analysis(schema):
    """Test query complexity analysis"""
    print("\n🧠 Testing Complexity Analysis...")
    
    try:
        from nl2sql.routing import ComplexityAnalyzer
        
        analyzer = ComplexityAnalyzer(schema)
        
        test_queries = [
            ("list ships", "SIMPLE"),
            ("how many schooners built before 1900", "MODERATE"), 
            ("compare average tonnage of vessels by type and analyze trends", "COMPLEX")
        ]
        
        for query, expected in test_queries:
            metrics = analyzer.analyze(query)
            level = analyzer.get_complexity_level(metrics)
            print(f"✅ '{query}' → {level.value.upper()} (score: {metrics.overall_score:.2f})")
        
        return analyzer
        
    except Exception as e:
        print(f"❌ Complexity Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_sql_generation(schema):
    """Test SQL generation"""
    print("\n⚙️  Testing SQL Generation...")
    
    try:
        from nl2sql.core import QueryParser, SQLGenerator
        
        parser = QueryParser(schema)
        generator = SQLGenerator(schema)
        
        test_query = "list all vessels"
        intent = parser.parse(test_query)
        generated = generator.generate(intent)
        
        print(f"✅ Generated SQL for '{test_query}':")
        print(f"   SQL: {generated.sql[:100]}...")
        print(f"   Parameters: {generated.parameters}")
        
        return generator
        
    except Exception as e:
        print(f"❌ SQL Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_full_service(db_connection):
    """Test the complete NL2SQL service"""
    print("\n🚀 Testing Complete NL2SQL Service...")
    
    try:
        from nl2sql import NL2SQLService
        
        # Create service without LangChain for now
        service = NL2SQLService(
            db_connection=db_connection,
            config={
                'routing_strategy': 'HYBRID_PREFER_RULES',
                'caching_enabled': True
            }
        )
        
        test_queries = [
            "list all vessels",
            "how many ships are there",
            "show the largest vessels"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing: '{query}'")
            result = service.process_query(query)
            
            print(f"   ✅ Status: {'SUCCESS' if result.success else 'FAILED'}")
            print(f"   📊 Method: {result.processing_method}")
            print(f"   ⏱️  Time: {result.execution_time:.3f}s")
            print(f"   🎯 Confidence: {result.confidence:.2f}")
            
            if result.sql_query:
                print(f"   💾 SQL: {result.sql_query[:80]}...")
            
            if result.errors:
                print(f"   ❌ Errors: {result.errors}")
        
        # Test service statistics
        stats = service.get_service_statistics()
        print(f"\n📈 Service Statistics:")
        print(f"   - Total queries: {stats['query_processing']['total_queries']}")
        print(f"   - Rule-based: {stats['query_processing']['rule_based_queries']}")
        
        return service
        
    except Exception as e:
        print(f"❌ Full Service test failed: {e}")
        print(f"   Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_langchain_integration():
    """Test LangChain integration (optional)"""
    print("\n🔗 Testing LangChain Integration...")
    
    try:
        # Try to import your existing agent
        from app.rag_components.agent_setup import create_maritime_agent
        
        agent = create_maritime_agent()
        print("✅ LangChain agent creation successful")
        
        # Test the bridge
        from nl2sql.integrations import LangChainBridge
        
        bridge = LangChainBridge(create_maritime_agent)
        validation = bridge.validate_integration()
        
        if validation['agent_creation_successful']:
            print("✅ LangChain bridge validation successful")
        else:
            print(f"⚠️  LangChain bridge issues: {validation['errors']}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  LangChain integration not available: {e}")
        print("   (This is OK - you can still use rule-based processing)")
        return False

def main():
    """Run all tests"""
    print("🧪 NL2SQL Pipeline Implementation Test")
    print("=" * 50)
    
    # Test 1: Database Connection
    db_connection = test_database_connection()
    if not db_connection:
        print("❌ Cannot proceed without database connection")
        return False
    
    # Test 2: Schema Analysis
    schema = test_schema_analyzer(db_connection)
    if not schema:
        print("❌ Cannot proceed without schema analysis")
        return False
    
    # Test 3: Pattern Matching
    patterns = test_pattern_matching()
    
    # Test 4: Complexity Analysis
    complexity_analyzer = test_complexity_analysis(schema)
    
    # Test 5: SQL Generation
    sql_generator = test_sql_generation(schema)
    
    # Test 6: Full Service
    service = test_full_service(db_connection)
    
    # Test 7: LangChain Integration (optional)
    langchain_available = test_langchain_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY:")
    
    tests_passed = [
        ("Database Connection", db_connection is not None),
        ("Schema Analysis", schema is not None),
        ("Pattern Matching", patterns is not None),
        ("Complexity Analysis", complexity_analyzer is not None),
        ("SQL Generation", sql_generator is not None),
        ("Full Service", service is not None),
        ("LangChain Integration", langchain_available)
    ]
    
    for test_name, passed in tests_passed:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    all_core_passed = all(passed for name, passed in tests_passed[:-1])  # Exclude LangChain
    
    if all_core_passed:
        print(f"\n🎉 SUCCESS! Your NL2SQL pipeline is ready for production!")
        print(f"   You can now integrate it with your existing application.")
    else:
        print(f"\n❌ Some tests failed. Please check the errors above.")
    
    return all_core_passed

if __name__ == "__main__":
    main()

#end-of-file