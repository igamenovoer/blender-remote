#!/bin/bash

echo "🧪 Running BLD_Remote_MCP vs BlenderAutoMCP Tests with Pixi"
echo "="*60

# Step 1: Check if services are running
echo "📡 Step 1: Checking if both services are running..."
pixi run python simple_test.py

if [ $? -ne 0 ]; then
    echo "❌ Services not running. Please start them first with:"
    echo "   ./start_dual_services.sh"
    exit 1
fi

echo ""
echo "✅ Services detected. Proceeding with tests..."

# Step 2: Run basic comparison test
echo ""
echo "🔄 Step 2: Running basic comparison test..."
pixi run python run_comparison_test.py

if [ $? -eq 0 ]; then
    echo "✅ Basic comparison test PASSED"
else
    echo "❌ Basic comparison test FAILED"
fi

# Step 3: Run detailed protocol comparison 
echo ""
echo "🔬 Step 3: Running detailed protocol comparison..."
pixi run python detailed_comparison_test.py

# Step 4: Run protocol compatibility test
echo ""
echo "🔧 Step 4: Running protocol compatibility test..."
pixi run python protocol_comparison_test.py

# Step 5: Run comprehensive test suite (if available)
echo ""
echo "🎯 Step 5: Running smoke test with pixi..."
if [ -f "tests/smoke_test.py" ]; then
    pixi run python tests/smoke_test.py
else
    echo "⚠️ Smoke test not found, skipping"
fi

echo ""
echo "✅ All tests completed!"
echo "📊 Check the output above for detailed results"