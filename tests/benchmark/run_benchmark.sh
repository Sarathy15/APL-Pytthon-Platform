#!/bin/bash
# Benchmark Test Runner for APL-to-Python Migration Platform (Unix/Linux/Mac)
# This shell script runs the comprehensive benchmark suite

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../../.."

echo ""
echo "============================================================================"
echo "APL-to-Python Migration Platform - Benchmark Suite"
echo "============================================================================"
echo ""

echo "Project Root: $PROJECT_ROOT"
echo "Benchmark Directory: $SCRIPT_DIR"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "Python command: $PYTHON_CMD"
echo ""

# Verify benchmark directory exists
if [ ! -f "$SCRIPT_DIR/01_sum.apl" ]; then
    echo "ERROR: Benchmark APL files not found"
    echo "Expected: $SCRIPT_DIR/01_sum.apl"
    exit 1
fi

# Run the benchmark runner
echo "Running benchmark suite..."
echo ""

$PYTHON_CMD "$SCRIPT_DIR/benchmark_runner.py"

RESULT=$?

echo ""
echo "============================================================================"
if [ $RESULT -eq 0 ]; then
    echo "Benchmark completed successfully!"
else
    echo "ERROR: Benchmark runner failed with exit code $RESULT"
fi
echo "Results saved to: outputs/benchmark_results/"
echo "============================================================================"
echo ""

exit $RESULT
