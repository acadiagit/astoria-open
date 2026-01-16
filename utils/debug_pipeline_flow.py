# Path: utils/debug_pipeline_flow.py
# Filename: debug_pipeline_flow.py
# Execute from: astoria_open (project root)

"""
Pipeline Flow Analysis

Traces the complete query processing pipeline from nl_query_service.py
through NL2SQLService to identify where the system breaks down.
"""

import sys
import os
import json
import time
import traceback
from typing import Dict, Any

# Add the project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import psycopg2
    from dotenv import load_dotenv
    from app.services.nl_query_service import process_nl_query, _initialize_services
    from nl2sql import NL2SQLService
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root and all dependencies are installed")
    sys.exit(1)

def test_direct_nl2sql_service():
    """Test the NL2SQL service directly"""
    print("\n" + "="*60)
    print("DIRECT NL2SQL SERVICE TEST")
    print("="*60)
    
    load_dotenv()
    
    try:
        # Initialize database connection
        db_connection = psycopg2.connect(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        
        print("Database connection established")
        
        # Initialize NL2SQL service with rule-based only configuration
        config = {
            'routing_strategy': 'RULE_BASED_ONLY',
            'caching_enabled': True,
            'routing_config': {
                'thresholds': {
                    'simple_threshold': 0.2,
                    'moderate_threshold': 0.5,
                    'ambiguity_threshold': 0.3,
                    'confidence_threshold': 0.6
                },
                'fallback_enabled': False,
                'performance_tracking': True,
                'adaptive_learning': True
            }
        }
        
        nl2sql_service = NL2SQLService(
            db_connection=db_connection,
            config=config,
            langchain_agent_factory=None
        )
        
        print("NL2SQL service initialized")
        
        # Test the problematic query
        test_query = "list 4 brigs"
        print(f"\nTesting query: '{test_query}'")
        
        result = nl2sql_service.process_query(test_query)
        
        print(f"\nDirect NL2SQL Service Results:")
        print(f"  Success: {result.success}")
        print(f"  Processing method: {result.processing_method}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Generated SQL: {result.sql_query}")
        print(f"  Parameters: {result.parameters}")
        print(f"  Results: {result.results}")
        print(f"  Errors: {result.errors}")
        print(f"  Warnings: {result.warnings}")
        
        return result
        
    except Exception as e:
        print(f"Error in direct NL2SQL service test: {e}")
        traceback.print_exc()
        return None
    finally:
        if 'db_connection' in locals():
            db_connection.close()

def test_nl_query_service():
    """Test the full nl_query_service pipeline"""
    print("\n" + "="*60)
    print("FULL NL_QUERY_SERVICE PIPELINE TEST")
    print("="*60)
    
    test_queries = [
        "list 4 brigs",
        "show schooners", 
        "how many vessels",
        "list all ships",
        "oldest vessels"
    ]
    
    print("Testing queries through the full nl_query_service pipeline...")
    
    for query in test_queries:
        print(f"\n--- Testing: '{query}' ---")
        
        try:
            start_time = time.time()
            result = process_nl_query(query, include_narrative=True)
            end_time = time.time()
            
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Processing method: {result.get('processing_method', 'unknown')}")
            print(f"Generated SQL: {result.get('generated_sql', 'none')}")
            print(f"Confidence: {result.get('confidence', 0)}")
            print(f"Execution time: {end_time - start_time:.2f}s")
            print(f"Results count: {len(result.get('results', []))}")
            print(f"Errors: {result.get('errors', [])}")
            print(f"Warnings: {result.get('warnings', [])}")
            
            if result.get('results'):
                print(f"Sample results: {result['results'][:2]}")
                
        except Exception as e:
            print(f"Error processing query: {e}")
            traceback.print_exc()

def test_api_endpoint():
    """Test the API endpoint directly"""
    print("\n" + "="*60)
    print("API ENDPOINT TEST")
    print("="*60)
    
    import requests
    
    api_url = "http://127.0.0.1:5001/api/v1/query"
    test_queries = [
        "list 4 brigs",
        "show schooners",
        "how many vessels"
    ]
    
    print(f"Testing API endpoint: {api_url}")
    
    for query in test_queries:
        print(f"\n--- API Test: '{query}' ---")
        
        try:
            response = requests.post(
                api_url,
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"API Response:")
                print(f"  Status: {result.get('status')}")
                print(f"  Generated SQL: {result.get('generated_sql')}")
                print(f"  Processing method: {result.get('processing_method')}")
                print(f"  Results count: {len(result.get('results', []))}")
                print(f"  Errors: {result.get('errors', [])}")
                print(f"  Warnings: {result.get('warnings', [])}")
            else:
                print(f"API Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except Exception as e:
            print(f"Error: {e}")

def compare_with_langchain_agent():
    """Compare results with the working LangChain agent"""
    print("\n" + "="*60)
    print("LANGCHAIN AGENT COMPARISON")
    print("="*60)
    
    try:
        from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
        from langchain_community.utilities.sql_database import SQLDatabase
        from langchain_groq import ChatGroq
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        
        load_dotenv()
        
        # Initialize LangChain agent (similar to agent_sql_tester.py)
        llm = ChatGroq(
            model_name="llama3-8b-8192",
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            max_retries=2,
            request_timeout=30
        )
        
        db_uri = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}".format(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        
        db = SQLDatabase.from_uri(
            db_uri, 
            include_tables=['vessels', 'voyages', 'crew', 'maintenance']
        )
        
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        
        system_prompt = """
        You are a powerful SQL agent. Your job is to interact with a PostgreSQL database to answer user questions.
        Always inspect the schema of a table before querying it.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent_executor = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            prompt=prompt,
            verbose=False,
            agent_type="openai-tools",
            handle_parsing_errors=True
        )
        
        # Test the same problematic queries
        test_queries = ["list 4 brigs", "show schooners"]
        
        for query in test_queries:
            print(f"\n--- LangChain Agent Test: '{query}' ---")
            
            try:
                result = agent_executor.invoke({"input": query})
                print(f"LangChain Result: {result.get('output', 'No output')}")
                
                # Extract SQL if available
                if 'intermediate_steps' in result:
                    for action, observation in result['intermediate_steps']:
                        if hasattr(action, 'tool') and action.tool == "sql_db_query":
                            print(f"LangChain SQL: {action.tool_input}")
                            break
                            
            except Exception as e:
                print(f"LangChain agent error: {e}")
                
    except ImportError:
        print("LangChain components not available for comparison")
    except Exception as e:
        print(f"Error in LangChain comparison: {e}")

def trace_routing_decisions():
    """Trace routing decisions through the system"""
    print("\n" + "="*60)
    print("ROUTING DECISION ANALYSIS")
    print("="*60)
    
    try:
        from nl2sql.routing.complexity_analyzer import ComplexityAnalyzer
        from nl2sql.routing.query_router import QueryRouter, RoutingStrategy
        from nl2sql.core.schema_analyzer import SchemaAnalyzer
        
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
        complexity_analyzer = ComplexityAnalyzer(schema_analyzer)
        query_router = QueryRouter(complexity_analyzer, RoutingStrategy.RULE_BASED_ONLY)
        
        test_queries = ["list 4 brigs", "show schooners", "how many vessels"]
        
        for query in test_queries:
            print(f"\n--- Routing Analysis: '{query}' ---")
            
            # Analyze complexity
            metrics = complexity_analyzer.analyze(query)
            print(f"Complexity Metrics:")
            print(f"  Overall score: {metrics.overall_score:.2f}")
            print(f"  Lexical: {metrics.lexical_complexity:.2f}")
            print(f"  Syntactic: {metrics.syntactic_complexity:.2f}")
            print(f"  Semantic: {metrics.semantic_complexity:.2f}")
            print(f"  Ambiguity: {metrics.ambiguity_score:.2f}")
            
            # Get routing decision
            decision = query_router.route_query(query)
            print(f"Routing Decision:")
            print(f"  Method: {decision.processing_method}")
            print(f"  Confidence: {decision.confidence:.2f}")
            print(f"  Reasoning: {decision.reasoning}")
            print(f"  Fallback: {decision.fallback_method}")
        
        db_connection.close()
        
    except Exception as e:
        print(f"Error in routing analysis: {e}")
        traceback.print_exc()

def analyze_execution_differences():
    """Analyze differences between working and failing executions"""
    print("\n" + "="*60)
    print("EXECUTION DIFFERENCE ANALYSIS")
    print("="*60)
    
    # Compare the working query from logs vs failing one
    working_example = {
        'query': 'Which 3 vessels are schooners?',
        'sql': "SELECT name, vessel_type FROM vessels WHERE vessel_type = 'Schooner' LIMIT 3",
        'method': 'langchain_agent'
    }
    
    failing_example = {
        'query': 'list 4 brigs',
        'sql': "SELECT name, vessel_type, year_built\nFROM vessels\nWHERE vessel_type ILIKE %s AND vessel_type ILIKE %s\nLIMIT 4",
        'method': 'rule_based_general'
    }
    
    print("Working Example:")
    print(f"  Query: {working_example['query']}")
    print(f"  SQL: {working_example['sql']}")
    print(f"  Method: {working_example['method']}")
    print(f"  Issues: None - uses exact match and finds 'Schooner'")
    
    print(f"\nFailing Example:")
    print(f"  Query: {failing_example['query']}")
    print(f"  SQL: {failing_example['sql']}")
    print(f"  Method: {failing_example['method']}")
    print(f"  Issues:")
    print(f"    1. Duplicate ILIKE conditions")
    print(f"    2. Looking for 'brig' but database has different vessel types")
    print(f"    3. Parameter count mismatch")
    
    print(f"\nKey Differences:")
    print(f"  1. LangChain agent inspects schema first and uses exact matches")
    print(f"  2. Rule-based system uses patterns that don't match actual data")
    print(f"  3. Parameter processing in maritime patterns has bugs")
    print(f"  4. No fallback when rule-based fails")

def generate_pipeline_recommendations():
    """Generate recommendations for pipeline improvements"""
    print("\n" + "="*60)
    print("PIPELINE IMPROVEMENT RECOMMENDATIONS")
    print("="*60)
    
    recommendations = [
        {
            'area': 'Pattern Matching',
            'issues': ['Regex patterns don\'t match actual database content', 'Parameter processing creates duplicates'],
            'solutions': ['Update maritime_patterns.py with actual vessel types', 'Fix _process_parameter_value() logic', 'Add validation tests']
        },
        {
            'area': 'Database Alignment',
            'issues': ['Expected vessel types differ from database content', 'Case sensitivity mismatches'],
            'solutions': ['Sync patterns with actual data', 'Implement better case-insensitive handling', 'Use table comments for synonyms']
        },
        {
            'area': 'Error Handling',
            'issues': ['No graceful fallback when rule-based fails', 'Limited error reporting'],
            'solutions': ['Implement proper fallback to LLM', 'Add detailed error logging', 'Return meaningful error messages']
        },
        {
            'area': 'Testing',
            'issues': ['No systematic validation of patterns', 'No integration tests'],
            'solutions': ['Add pattern validation tests', 'Create integration test suite', 'Monitor pattern success rates']
        }
    ]
    
    for rec in recommendations:
        print(f"\n{rec['area']}:")
        print("  Issues:")
        for issue in rec['issues']:
            print(f"    - {issue}")
        print("  Solutions:")
        for solution in rec['solutions']:
            print(f"    - {solution}")

def main():
    """Main pipeline debugging function"""
    print("PIPELINE FLOW ANALYSIS - MARITIME NL2SQL DEBUGGING")
    print("="*60)
    print("This script traces the complete query processing pipeline")
    print("from nl_query_service.py through NL2SQLService to identify issues.")
    print("="*60)
    
    # Run all analysis functions
    test_direct_nl2sql_service()
    test_nl_query_service()
    test_api_endpoint()
    compare_with_langchain_agent()
    trace_routing_decisions()
    analyze_execution_differences()
    generate_pipeline_recommendations()
    
    print(f"\nSUMMARY:")
    print("1. Check above for parameter mismatches and duplicate SQL conditions")
    print("2. Note differences between rule-based and LangChain agent results")
    print("3. Review routing decisions and complexity analysis")
    print("4. Implement recommended fixes for robust operation")
    
    print(f"\nNEXT STEPS:")
    print("1. Fix duplicate parameter bug in maritime_patterns.py")
    print("2. Update vessel type patterns to match database content")
    print("3. Implement better error handling and fallback logic")
    print("4. Add comprehensive testing framework")

if __name__ == "__main__":
    main()

#end-of-file
        