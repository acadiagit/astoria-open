# Path: /Users/hugodiaz/Astoria/hf_spaces/astoria_open/console
# File: test-api-directly.sh
# Execute from: /Users/hugodiaz/Astoria/hf_spaces/astoria_open/console

#!/bin/bash

echo "🧪 Testing API Endpoints Directly"
echo "================================="
echo ""

# Test the actual query endpoint that matters
echo "1️⃣ Testing Query Endpoint (the important one):"
echo ""

curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "how many ships are there"}' \
  http://127.0.0.1:5001/api/v1/query | jq '.'

echo ""
echo ""

echo "2️⃣ What to look for in the response above:"
echo "  ✅ status: 'success'"
echo "  ✅ generated_sql: 'SELECT COUNT(*)...'"
echo "  ✅ nl_response: 'Found 1 results'"
echo "  ❓ Look for data fields like: results, data, database_results, etc."
echo ""

echo "3️⃣ Now test the UI:"
echo "==================="
echo "1. Open: http://localhost:5173"
echo "2. Submit query: 'how many ships are there'"
echo "3. Check browser console (F12) for debug logs"
echo "4. Look for these debug messages:"
echo "   - 'Full API response:'"
echo "   - 'Raw data received:'"
echo "   - 'Available fields:'"
echo ""

echo "🎯 The fix should now show actual data instead of empty SQL Result section!"

#end-of-script