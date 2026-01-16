import re

pattern = r'^(?:list|show|find|get)\s+(?:(?P<limit>\d+)\s+)?(?:all\s+)?(?P<vessel_type>schooners?|brigs?|cargo\s+ships?|passenger\s+ships?|tankers?|fishing\s+boats?|steamships?)$'

test_cases = [
    "list brigs",           # Should match: vessel_type='brigs', limit=None
    "list 4 brigs",         # Should match: vessel_type='brigs', limit='4'  
    "show 10 schooners",    # Should match: vessel_type='schooners', limit='10'
    "find all tankers",     # Should match: vessel_type='tankers', limit=None
]

for query in test_cases:
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        print(f"'{query}' -> {match.groupdict()}")
    else:
        print(f"'{query}' -> NO MATCH")
