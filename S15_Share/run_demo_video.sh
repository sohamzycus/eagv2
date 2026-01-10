#!/bin/bash
# Demo script for video recording of 4 task flows

cd /Users/soham.niyogi/Soham/codebase/eagv2/S15_Share
source .venv/bin/activate

echo "=============================================="
echo "S15_Share Demo - 4 Task Flows with Ollama phi4"
echo "=============================================="
echo ""

# Task 1: Gmail Signup
echo ">>> TASK 1: Gmail Signup (Browser Automation)"
echo "Query: Sign me up on Gmail with name John Doe"
echo ""
python demo_4_tasks.py 1
echo ""
echo "Press Enter to continue to next task..."
read

# Task 2: Web Search
echo ">>> TASK 2: Web Search (Decision)"
echo "Query: Search for Tesla stock news"
echo ""
python demo_4_tasks.py 2
echo ""
echo "Press Enter to continue to next task..."
read

# Task 3: Document Processing
echo ">>> TASK 3: Document Processing (Decision)"
echo "Query: Search stored documents for DLF financials"
echo ""
python demo_4_tasks.py 3
echo ""
echo "Press Enter to continue to next task..."
read

# Task 4: Planning Request
echo ">>> TASK 4: Planning Request (Summarize)"
echo "Query: Create physics animation project plan"
echo ""
python demo_4_tasks.py 4
echo ""

echo "=============================================="
echo "Demo Complete!"
echo "=============================================="

