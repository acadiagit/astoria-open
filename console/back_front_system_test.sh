# Path: /Users/hugodiaz/Astoria/hf_spaces/astoria_open/console
# File: test-system.sh
# Execute from: /Users/hugodiaz/Astoria/hf_spaces/astoria_open/console

#!/bin/bash

echo "🔍 Testing Astoria System - Backend + Frontend"
echo "=============================================="
echo ""

# Step 1: Verify backend is working
echo "1️⃣ Testing Backend API (the important part)..."
echo ""
echo "Testing health endpoint:"
curl -s http://127.0.0.1:5001/api/v1/health && echo "✅ Health endpoint working" || echo "❌ Health endpoint failed"
echo ""

echo "Testing query endpoint:"
response=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"query": "how many ships are there"}' \
  http://127.0.0.1:5001/api/v1/query)

if [[ $? -eq 0 ]]; then
    echo "✅ Query endpoint working"
    echo "Response preview:"
    echo "$response" | jq '.status, .nl_response, .generated_sql' 2>/dev/null || echo "$response" | head -3
else
    echo "❌ Query endpoint failed"
fi
echo ""

# Step 2: Check if frontend is running
echo "2️⃣ Checking Frontend Status..."
if pgrep -f "vite" > /dev/null; then
    echo "✅ Frontend (Vite) is running"
    echo "   URL: http://localhost:5173"
else
    echo "❌ Frontend not running"
    echo "   Starting frontend..."
    npm run dev &
    sleep 3
    echo "   Frontend should now be starting..."
fi
echo ""

# Step 3: Explain the 404 error
echo "3️⃣ About the 404 Error You Saw:"
echo "================================"
echo "❗ The 404 error on http://127.0.0.1:5001 is NORMAL and EXPECTED"
echo ""
echo "Why? Because:"
echo "  🔸 Port 5001 = Backend API server (Flask)"
echo "  🔸 Port 5173 = Frontend UI server (Vite)"
echo ""
echo "The backend (5001) serves API endpoints like:"
echo "  ✅ http://127.0.0.1:5001/api/v1/health"
echo "  ✅ http://127.0.0.1:5001/api/v1/query"
echo ""
echo "The frontend UI is served on:"
echo "  ✅ http://localhost:5173"
echo ""

# Step 4: Test instructions
echo "4️⃣ How to Test the UI Fix:"
echo "=========================="
echo "1. Open your browser to: http://localhost:5173"
echo "2. Click 'Test Hub Health' - should work now"
echo "3. Submit query: 'how many ships are there'"
echo "4. Open browser console (F12) to see debug logs"
echo "5. Check if the SQL results now display properly (not empty)"
echo ""

# Step 5: What to look for
echo "5️⃣ What You Should See After the Fix:"
echo "====================================="
echo "Before fix: 'SQL Result' section was empty"
echo "After fix:  'SQL Result' should show:"
echo "  📊 For counts: Large number (e.g., '731')"
echo "  📋 For lists: Table with columns and data"
echo "  🐛 Console logs showing: 'Raw data received:', 'Available fields:'"
echo ""

echo "🎯 The key test: Submit 'how many ships are there' and see if you get a visible number result!"

#end-of-script