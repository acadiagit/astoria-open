# Path: utils/debug_pattern_matching.py
# Filename: debug_pattern_matching.py
# Execute from: astoria_open (project root)

"""
Pattern Matching Isolation

Tests the maritime patterns system in isolation to identify
the source of duplicate parameter generation and matching issues.
"""

import sys
import os
import re
from typing import Dict, List, Any, Tuple

# Add the project root to path so we can import nl2sql modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from nl2sql.patterns.maritime_patterns import MaritimePatterns, PatternMatch
    from nl2sql.patterns.pattern_cache import PatternCache
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root: astoria_open")
    sys.exit(1)

def test_direct_pattern_matching():
    """Test maritime patterns directly without database"""
    print("\n" + "="*60)
    print("DIRECT PATTERN MATCHING TEST")
    print("="*60)
    
    maritime_patterns = MaritimePatterns()
    
    # Test queries that are known to be problematic
    test_queries = [
        "list 4 brigs",
        "show me schooners", 
        "list all vessels",
        "find tankers",
        "how many ships",
        "oldest vessels",
        "largest boats"
    ]
    
    print(f"Testing {len(test_queries)} queries against maritime patterns...")
    
    for query in test_queries:
        print(f"\n--- Testing: '{query}' ---")
        
        # Try to match pattern
        pattern_match = maritime_patterns.match_pattern(query)
        
        if pattern_match:
            print(f"✅ Pattern matched: {pattern_match.pattern.name}")
            print(f"   Confidence: {pattern_match.confidence:.2f}")
            print(f"   Pattern type: {pattern_match.pattern.pattern_type.value}")
            print(f"   Matched groups: {pattern_match.matched_groups}")
            print(f"   Generated SQL: {pattern_match.sql_query}")
            print(f"   Parameters: {pattern_match.parameters}")
            
            # Check for duplicate parameters in SQL
            if "ILIKE %s AND" in pattern_match.sql_query:
                param_count = pattern_match.sql_query.count('%s')
                actual_params = len(pattern_match.parameters)
                if param_count != actual_params:
                    print(f"🚨 PARAMETER MISMATCH: SQL has {param_count} placeholders but {actual_params} parameters")
                    print(f"🚨 This is likely the source of the duplicate parameter bug!")
        else:
            print(f"❌ No pattern matched")
            
            # Try to understand why by testing individual patterns
            print("   Checking individual patterns...")
            for pattern in maritime_patterns.patterns[:5]:  # Check first 5 patterns
                match = re.search(pattern.regex_pattern, query.lower(), re.IGNORECASE)
                if match:
                    print(f"   - Manual regex match found: {pattern.name}")
                    print(f"     Groups: {match.groupdict()}")

def test_parameter_processing():
    """Test parameter processing logic in detail"""
    print("\n" + "="*60)
    print("PARAMETER PROCESSING TEST")
    print("="*60)
    
    maritime_patterns = MaritimePatterns()
    
    # Find the specific pattern that should match "list 4 brigs"
    brig_pattern = None
    for pattern in maritime_patterns.patterns:
        if 'brigs?' in pattern.regex_pattern:
            brig_pattern = pattern
            break
    
    if not brig_pattern:
        print("❌ Could not find brig pattern in maritime_patterns")
        return
    
    print(f"Found brig pattern: {brig_pattern.name}")
    print(f"Regex: {brig_pattern.regex_pattern}")
    print(f"SQL Template: {brig_pattern.sql_template}")
    print(f"Parameter mapping: {brig_pattern.parameter_mapping}")
    
    # Test the regex matching
    test_query = "list 4 brigs"
    match = re.search(brig_pattern.regex_pattern, test_query.lower(), re.IGNORECASE)
    
    if match:
        print(f"\n✅ Regex matches '{test_query}'")
        print(f"Groups: {match.groupdict()}")
        
        # Test parameter processing manually
        matched_groups = match.groupdict()
        print(f"\nTesting parameter processing:")
        
        for param_name, group_name in brig_pattern.parameter_mapping.items():
            if group_name in matched_groups:
                value = matched_groups[group_name]
                print(f"  {param_name} <- {group_name}: '{value}'")
                
                # Test the _process_parameter_value logic
                processed = maritime_patterns._process_parameter_value(param_name, value, brig_pattern)
                print(f"  Processed value: '{processed}'")
            else:
                print(f"  {param_name} <- {group_name}: NOT FOUND in groups")
        
        # Generate SQL manually to trace the issue
        try:
            sql_query, parameters = maritime_patterns._generate_sql_from_pattern(brig_pattern, matched_groups)
            print(f"\nGenerated SQL: {sql_query}")
            print(f"Parameters: {parameters}")
            
            # Count placeholders vs parameters
            placeholder_count = sql_query.count('%s')
            parameter_count = len(parameters)
            print(f"Placeholders in SQL: {placeholder_count}")
            print(f"Actual parameters: {parameter_count}")
            
            if placeholder_count != parameter_count:
                print(f"🚨 MISMATCH DETECTED!")
                print(f"This explains the duplicate parameter error")
                
        except Exception as e:
            print(f"❌ Error generating SQL: {e}")
    else:
        print(f"❌ Regex does not match '{test_query}'")

def test_pattern_coverage():
    """Test pattern coverage against expected vessel types"""
    print("\n" + "="*60)
    print("PATTERN COVERAGE TEST")
    print("="*60)
    
    maritime_patterns = MaritimePatterns()
    
    # Expected vessel types from database analysis (you'll update this after running debug_data_reality.py)
    expected_vessel_types = [
        'Cargo', 'Schooner', 'Passenger', 'Tanker', 'Fishing'  # Based on your sample data
    ]
    
    # Test queries for each expected type
    test_templates = [
        "list {type}",
        "show {type}s", 
        "find all {type}s",
        "how many {type}s"
    ]
    
    print("Testing pattern coverage for expected vessel types...")
    
    coverage_results = {}
    
    for vessel_type in expected_vessel_types:
        print(f"\n--- Testing coverage for '{vessel_type}' ---")
        coverage_results[vessel_type] = {'matched': 0, 'total': 0}
        
        for template in test_templates:
            query = template.format(type=vessel_type.lower())
            coverage_results[vessel_type]['total'] += 1
            
            pattern_match = maritime_patterns.match_pattern(query)
            if pattern_match and pattern_match.confidence > 0.5:
                print(f"  ✅ '{query}' -> {pattern_match.pattern.name}")
                coverage_results[vessel_type]['matched'] += 1
            else:
                print(f"  ❌ '{query}' -> No match")
    
    # Summary
    print(f"\nCOVERAGE SUMMARY:")
    for vessel_type, results in coverage_results.items():
        percentage = (results['matched'] / results['total']) * 100
        print(f"  {vessel_type}: {results['matched']}/{results['total']} ({percentage:.1f}%)")

def test_individual_regex_patterns():
    """Test individual regex patterns to find issues"""
    print("\n" + "="*60)
    print("INDIVIDUAL REGEX PATTERN TEST")
    print("="*60)
    
    maritime_patterns = MaritimePatterns()
    
    # Test specific problematic cases
    test_cases = [
        ("list 4 brigs", "Should match vessel filtering pattern"),
        ("list brigs", "Should match vessel by type pattern"),
        ("show schooners", "Should match vessel by type pattern"),
        ("how many vessels", "Should match count pattern"),
    ]
    
    print("Testing individual regex patterns...")
    
    for query, expected in test_cases:
        print(f"\n--- Testing: '{query}' ({expected}) ---")
        
        matches_found = []
        
        for i, pattern in enumerate(maritime_patterns.patterns):
            match = re.search(pattern.regex_pattern, query.lower(), re.IGNORECASE)
            if match:
                matches_found.append((i, pattern, match))
                print(f"  Match {len(matches_found)}: {pattern.name}")
                print(f"    Regex: {pattern.regex_pattern}")
                print(f"    Groups: {match.groupdict()}")
                print(f"    Confidence: {pattern.confidence_score}")
        
        if not matches_found:
            print(f"  ❌ No regex matches found")
        elif len(matches_found) > 1:
            print(f"  ⚠️ Multiple matches found - may cause conflicts")

def test_sql_generation_edge_cases():
    """Test SQL generation for edge cases"""
    print("\n" + "="*60)
    print("SQL GENERATION EDGE CASES")
    print("="*60)
    
    maritime_patterns = MaritimePatterns()
    
    edge_cases = [
        "list brigs",  # No number specified
        "show 10 largest vessels",  # With number
        "find schooners built before 1900",  # Complex pattern
        "how many active ships",  # Count with modifier
    ]
    
    for query in edge_cases:
        print(f"\n--- Edge case: '{query}' ---")
        
        pattern_match = maritime_patterns.match_pattern(query)
        if pattern_match:
            print(f"Matched: {pattern_match.pattern.name}")
            
            # Analyze the SQL generation
            sql = pattern_match.sql_query
            params = pattern_match.parameters
            
            print(f"SQL: {sql}")
            print(f"Parameters: {params}")
            
            # Check for common issues
            issues = []
            if sql.count('%s') != len(params):
                issues.append(f"Parameter count mismatch: {sql.count('%s')} placeholders vs {len(params)} parameters")
            
            if 'ILIKE %s AND' in sql and len(params) == 1:
                issues.append("Duplicate ILIKE condition with single parameter")
            
            if issues:
                print(f"🚨 Issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print(f"✅ No obvious issues")
        else:
            print(f"❌ No pattern matched")

def analyze_pattern_conflicts():
    """Analyze potential conflicts between patterns"""
    print("\n" + "="*60)
    print("PATTERN CONFLICT ANALYSIS")
    print("="*60)
    
    maritime_patterns = MaritimePatterns()
    
    # Test a query against all patterns to see if multiple match
    test_query = "list vessels"
    
    print(f"Testing '{test_query}' against all patterns to find conflicts...")
    
    all_matches = []
    for i, pattern in enumerate(maritime_patterns.patterns):
        match = re.search(pattern.regex_pattern, test_query.lower(), re.IGNORECASE)
        if match:
            all_matches.append((i, pattern, match))
    
    print(f"Found {len(all_matches)} matching patterns:")
    
    for i, (idx, pattern, match) in enumerate(all_matches):
        print(f"  {i+1}. {pattern.name} (confidence: {pattern.confidence_score})")
        print(f"     Pattern: {pattern.regex_pattern}")
        print(f"     Groups: {match.groupdict()}")
    
    if len(all_matches) > 1:
        print(f"\n⚠️ Multiple patterns match - the system should use the highest confidence")
        
        # Test the actual pattern matching logic
        best_match = maritime_patterns.match_pattern(test_query)
        if best_match:
            print(f"✅ System selected: {best_match.pattern.name} (confidence: {best_match.confidence:.2f})")
        else:
            print(f"❌ System failed to select any pattern despite manual matches")

def main():
    """Main debugging function"""
    print("🔍 PATTERN MATCHING ISOLATION - MARITIME NL2SQL DEBUGGING")
    print("="*60)
    print("This script tests the maritime patterns system in isolation")
    print("to identify the source of duplicate parameters and matching issues.")
    print("="*60)
    
    try:
        # Run all test functions
        test_direct_pattern_matching()
        test_parameter_processing()
        test_pattern_coverage()
        test_individual_regex_patterns()
        test_sql_generation_edge_cases()
        analyze_pattern_conflicts()
        
        print(f"\n🎯 KEY FINDINGS:")
        print("1. Check the output above for 'PARAMETER MISMATCH' warnings")
        print("2. Look for patterns that don't match expected vessel types")
        print("3. Note any SQL generation issues or duplicate conditions")
        print("4. Identify regex patterns that need updating")
        
        print(f"\n📋 NEXT STEPS:")
        print("1. Fix any parameter mismatches in maritime_patterns.py")
        print("2. Update regex patterns to match actual database content")
        print("3. Run utils/debug_pipeline_flow.py to test the full system")
        
    except Exception as e:
        print(f"❌ Error during pattern testing: {e}")
        print(f"Make sure you're running from the project root directory")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

#end-of-file