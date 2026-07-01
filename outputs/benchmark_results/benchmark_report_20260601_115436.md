# APL-to-Python Migration Platform - Benchmark Report

Generated: 2026-06-01T11:54:36.432550

## Executive Summary

| Metric | Result | Rate |
|--------|--------|------|
| **Total Tests** | 10 | - |
| **Understanding** | 10 | 100.0% |
| **Conversion** | 0 | 0.0% |
| **APL Execution** | 10 | 100.0% |
| **Python Execution** | 0 | 0.0% |
| **Parity** | 0 | 0.0% |
| **Fallback Used** | 0 | 0.0% |

## Performance

| Metric | Value |
|--------|-------|
| **Average Latency** | 90247.39ms |
| **Max Latency** | 130057.91ms |
| **Min Latency** | 68078.86ms |

## Failures

| Component | Failures |
|-----------|----------|
| Understanding | 0 |
| Conversion | 10 |
| APL Execution | 0 |
| Python Execution | 10 |
| Parity | 10 |

## Test Results

| Test | U | C | APL | Py | Par | FB | Latency |
|------|---|---|-----|----|----|----|----|
| 01_sum          | P | F | P | F | F | N | 69881.0ms |
| 02_average      | P | F | P | F | F | N | 68078.9ms |
| 03_salary_analysis | P | F | P | F | F | N | 95980.3ms |
| 04_inventory    | P | F | P | F | F | N | 116948.5ms |
| 05_matrix_multiply | P | F | P | F | F | N | 68492.2ms |
| 06_banking      | P | F | P | F | F | N | 101126.6ms |
| 07_student_marks | P | F | P | F | F | N | 104814.0ms |
| 08_reshape      | P | F | P | F | F | N | 71768.7ms |
| 09_reverse      | P | F | P | F | F | N | 75325.7ms |
| 10_edge_case    | P | F | P | F | F | N | 130057.9ms |
