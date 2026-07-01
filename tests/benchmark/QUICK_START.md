# Benchmark Suite - Quick Start Guide

## What You Have

You now have a comprehensive benchmark suite in `tests/benchmark/` with:

### 10 APL Test Programs
- **01-02**: Simple operations (sum, average)
- **03-07**: Medium complexity (analysis, filtering, calculations)
- **08-10**: Advanced operations (reshape, reverse, edge cases)

### Test Infrastructure
- **benchmark_runner.py** - Main test orchestrator
- **run_benchmark.bat** - Windows launcher
- **run_benchmark.sh** - Unix/Linux/Mac launcher
- **track_results.py** - Results analysis and comparison

## How to Run

### Windows
```cmd
cd tests\benchmark
run_benchmark.bat
```

### Linux/Mac
```bash
cd tests/benchmark
bash run_benchmark.sh
```

### Direct Python
```bash
python tests/benchmark/benchmark_runner.py
```

## What Gets Tested

Each APL program goes through **5 pipeline stages**:

```
┌─────────────┐
│   APL Code  │
└──────┬──────┘
       ↓
┌──────────────────────┐
│ 1. UNDERSTAND        │ ← Parse & Semantic Analysis
│    PASS/FAIL         │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ 2. CONVERT           │ ← Use LLM provider to generate Python
│    PASS/FAIL         │
└──────┬───────────────┘
       ↓
┌─────────────────┬────────────────┐
│                 │                │
↓                 ↓                ↓
3. APL EXEC    3. PYTHON EXEC  Records:
   PASS/FAIL      PASS/FAIL     - Fallback? YES/NO
                                - Latency (ms)
│                 │                │
└─────────────────┼────────────────┘
                  ↓
         ┌──────────────────┐
         │ 5. PARITY CHECK  │
         │    PASS/FAIL     │
         └──────────────────┘
```

## Output Files

Results are saved to `outputs/benchmark_results/`:

```
benchmark_report_20260601_143022.json       ← Raw data (all metrics)
benchmark_report_20260601_143022.md         ← Human-readable report
benchmark_report_20260601_143022.csv        ← Spreadsheet format
```

## Understanding the Report

### Summary Section
Shows pass rates for each stage:
```
Total Tests:      10
Understand:       10/10 (100.0%)
Convert:          10/10 (100.0%)
APL Execute:      10/10 (100.0%)
Python Execute:    8/10 (80.0%)
Parity:            7/10 (70.0%)
```

### Green Flags ✓
- Understand rate > 95%
- Convert rate > 90%
- Parity rate > 85%
- Minimal fallbacks

### Red Flags ✗
- Convert failures → Check LLM prompt engineering
- Python execute failures → Check generated code quality
- Parity mismatches → Check conversion logic
- High latency → Profile provider calls

## Tracking Progress

To compare runs over time:

```bash
python track_results.py compare
```

This shows:
- Before/after for each metric
- Regressions (↓ means worse)
- Improvements (↑ means better)

## Expanding the Suite

Add more tests by creating new `NN_name.apl` files:

```apl
⍝ Description of what this test does
⍝ Expected output: [example]
code ← goes here
+/code
```

Then re-run the benchmark suite.

## Integration Points

The benchmark automatically tests these components:
- `backend/parser/apl_parser.py` - Parsing
- `backend/parser/semantic_analyzer.py` - Analysis
- `backend/execution/apl_runner.py` - APL execution
- `backend/execution/python_runner.py` - Python execution
- `backend/providers/provider_factory.py` - LLM conversion
- `backend/comparator/engine.py` - Result comparison

## Next Steps

1. **Run the benchmark**: `run_benchmark.bat` (Windows) or `bash run_benchmark.sh` (Linux/Mac)
2. **Review the report**: Check `outputs/benchmark_results/`
3. **Identify failures**: Look for FAIL entries and error messages
4. **Fix issues**: Address conversion or execution problems
5. **Re-run**: Track improvements with `track_results.py compare`

## Tips for Debugging Failures

### Conversion Failures
- Check the LLM prompt in benchmark_runner.py
- Adjust provider configuration
- Test with a different provider

### Python Execution Failures
- Look at the generated Python code in the JSON report
- Test the code snippet locally
- Check for missing numpy functions

### Parity Mismatches
- Compare expected vs actual outputs
- Check for floating-point precision issues
- Review the conversion logic for subtle bugs

---

**You now have a quantifiable way to measure platform quality!** 📊
