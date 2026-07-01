# APL-to-Python Benchmark Suite

This directory contains a comprehensive benchmark suite for testing the APL-to-Python migration platform.

## Test Programs (10 Comprehensive Benchmarks)

| # | Name | Description | Complexity |
|---|------|-------------|-----------|
| 01 | sum.apl | Basic vector summation | Simple |
| 02 | average.apl | Calculate mean of vector | Simple |
| 03 | salary_analysis.apl | Multi-stat analysis (avg/max/min) | Medium |
| 04 | inventory.apl | Element-wise multiplication and sum | Medium |
| 05 | matrix_multiply.apl | Matrix-vector dot product | Medium |
| 06 | banking.apl | Scalar multiplication (interest calculation) | Simple |
| 07 | student_marks.apl | Complex analysis with filtering | Medium |
| 08 | reshape.apl | Array shape transformation | Medium |
| 09 | reverse.apl | Vector reversal | Simple |
| 10 | edge_case.apl | Single element and empty array handling | Complex |

## Running Benchmarks

### Quick Start

```bash
# Run the benchmark suite
python benchmark_runner.py
```

### Output

Results are saved to `../../outputs/benchmark_results/` with:
- **JSON Report**: Full structured data for programmatic analysis
- **Markdown Report**: Human-readable summary with tables

## Metrics Tracked

For each test, the benchmark runner records:

| Metric | Description |
|--------|-------------|
| **Understand PASS/FAIL** | Can the platform parse and semantically analyze the APL code? |
| **Convert PASS/FAIL** | Can the APL be successfully converted to Python? |
| **APL Execute PASS/FAIL** | Does the original APL code execute successfully? |
| **Python Execute PASS/FAIL** | Does the converted Python code execute successfully? |
| **Parity PASS/FAIL** | Do both versions produce identical or near-identical results? |
| **Fallback Used?** | Did the converter fall back to simpler/generic approaches? |
| **Latency** | Total time to process the entire pipeline (ms) |

## Performance Analysis

The benchmark reveals:

1. **Conversion Quality**: Percentage of tests that reach full parity
2. **Reliability**: Which APL features fail most often
3. **Performance**: Average processing time per test
4. **Fallback Patterns**: Which operators trigger fallbacks
5. **Edge Cases**: Handling of boundary conditions

## Understanding Results

### Success Indicators
- ✓ All metrics showing PASS
- Parity rate > 90%
- No fallbacks needed

### Warning Signs
- ✗ Convert failures (semantic issues)
- ✗ Python execute failures (generated code problems)
- ✗ Parity mismatches (logic errors)
- Fallback frequently used

## Extending Benchmarks

To add more tests:

1. Create a new `NN_name.apl` file
2. Include a comment explaining expected output
3. Re-run `benchmark_runner.py`

## Architecture Integration

The benchmark runner integrates with:
- **Parser**: `backend/parser/apl_parser.py`
- **Semantic Analyzer**: `backend/parser/semantic_analyzer.py`
- **Providers**: `backend/providers/provider_factory.py`
- **Execution**: `backend/execution/apl_runner.py` + `python_runner.py`
- **Comparator**: `backend/comparator/engine.py`
