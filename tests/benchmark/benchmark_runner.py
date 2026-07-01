"""
Benchmark Test Runner for APL-to-Python Migration Platform

This script runs all APL programs in tests/benchmark/ through the complete pipeline
and generates a detailed report with metrics for:
- Understand PASS/FAIL
- Convert PASS/FAIL
- APL Execute PASS/FAIL
- Python Execute PASS/FAIL
- Parity PASS/FAIL
- Fallback Used? YES/NO
- Latency (ms)
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Any, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

import numpy as np
from backend.parser.apl_parser import APLParser
from backend.parser.semantic_analyzer import SemanticAnalyzer
from backend.execution.apl_runner import APLRunner
from backend.execution.python_runner import PythonRunner
from backend.providers.provider_factory import ProviderFactory
from backend.comparator.engine import ComparatorEngine


@dataclass
class BenchmarkResult:
    """Store results for a single benchmark test"""
    test_name: str
    apl_file: str
    understand_pass: bool
    convert_pass: bool
    apl_execute_pass: bool
    python_execute_pass: bool
    parity_pass: bool
    fallback_used: bool
    latency_ms: float
    understand_error: Optional[str] = None
    convert_error: Optional[str] = None
    apl_execute_error: Optional[str] = None
    python_execute_error: Optional[str] = None
    parity_error: Optional[str] = None
    converted_python: Optional[str] = None
    apl_output: Optional[Any] = None
    python_output: Optional[Any] = None


class BenchmarkRunner:
    """Main benchmark test runner"""
    
    def __init__(self, benchmark_dir: Path, output_dir: Path):
        self.benchmark_dir = benchmark_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.parser = APLParser()
        self.semantic_analyzer = SemanticAnalyzer()
        self.apl_runner = APLRunner()
        self.python_runner = PythonRunner()
        self.comparator = ComparatorEngine()
        
        # Get default provider
        self.provider_factory = ProviderFactory()
        self.provider = self.provider_factory.get_provider()
        
        self.results: List[BenchmarkResult] = []
    
    def run_all_tests(self) -> List[BenchmarkResult]:
        """Run all APL benchmark tests"""
        apl_files = sorted(self.benchmark_dir.glob("*.apl"))
        
        print(f"Found {len(apl_files)} APL test files")
        print(f"Output directory: {self.output_dir}")
        print("-" * 80)
        
        for apl_file in apl_files:
            result = self.run_single_test(apl_file)
            self.results.append(result)
            self.print_result(result)
        
        return self.results
    
    def run_single_test(self, apl_file: Path) -> BenchmarkResult:
        """Run a single APL benchmark test through the entire pipeline"""
        test_name = apl_file.stem
        start_time = time.time()
        
        result = BenchmarkResult(
            test_name=test_name,
            apl_file=str(apl_file.name),
            understand_pass=False,
            convert_pass=False,
            apl_execute_pass=False,
            python_execute_pass=False,
            parity_pass=False,
            fallback_used=False,
            latency_ms=0.0
        )
        
        try:
            # Read APL program
            apl_code = apl_file.read_text()
            
            # Stage 1: Understand (Parse & Semantic Analysis)
            try:
                parsed = self.parser.parse(apl_code)
                self.semantic_analyzer.analyze(parsed)
                result.understand_pass = True
            except Exception as e:
                result.understand_error = str(e)
                result.latency_ms = (time.time() - start_time) * 1000
                return result
            
            # Stage 2: Convert APL to Python
            try:
                # Use the provider to convert
                conversion_prompt = f"""Convert this APL code to Python numpy:

{apl_code}

Provide only the Python code, no explanation."""
                
                conversion_response = self.provider.call(conversion_prompt)
                converted_python = conversion_response.content if hasattr(conversion_response, 'content') else str(conversion_response)
                
                # Try to extract code from markdown blocks if present
                if "```python" in converted_python:
                    converted_python = converted_python.split("```python")[1].split("```")[0].strip()
                elif "```" in converted_python:
                    converted_python = converted_python.split("```")[1].split("```")[0].strip()
                
                result.converted_python = converted_python
                result.convert_pass = True
                
                # Check if fallback was triggered (e.g., complex operators)
                if "⊂" in apl_code or "⊃" in apl_code or "⌺" in apl_code:
                    result.fallback_used = True
                    
            except Exception as e:
                result.convert_error = str(e)
                result.latency_ms = (time.time() - start_time) * 1000
                return result
            
            # Stage 3: Execute Original APL
            try:
                apl_output = self.apl_runner.execute(apl_code)
                result.apl_output = apl_output
                result.apl_execute_pass = True
            except Exception as e:
                result.apl_execute_error = str(e)
                # Continue anyway to test Python execution
            
            # Stage 4: Execute Converted Python
            try:
                python_output = self.python_runner.execute(result.converted_python)
                result.python_output = python_output
                result.python_execute_pass = True
            except Exception as e:
                result.python_execute_error = str(e)
                # Continue anyway
            
            # Stage 5: Check Parity (if both executed)
            if result.apl_execute_pass and result.python_execute_pass:
                try:
                    parity_check = self.comparator.compare(
                        result.apl_output,
                        result.python_output
                    )
                    result.parity_pass = parity_check.get("match", False)
                    if not result.parity_pass:
                        result.parity_error = parity_check.get("reason", "Unknown parity mismatch")
                except Exception as e:
                    result.parity_error = str(e)
        
        except Exception as e:
            result.understand_error = f"Unexpected error: {str(e)}"
        
        finally:
            result.latency_ms = (time.time() - start_time) * 1000
        
        return result
    
    def print_result(self, result: BenchmarkResult):
        """Print formatted result for a single test"""
        status_understand = "✓" if result.understand_pass else "✗"
        status_convert = "✓" if result.convert_pass else "✗"
        status_apl_exe = "✓" if result.apl_execute_pass else "✗"
        status_python_exe = "✓" if result.python_execute_pass else "✗"
        status_parity = "✓" if result.parity_pass else "✗"
        fallback = "YES" if result.fallback_used else "NO"
        
        print(f"{result.test_name:25} | U:{status_understand} C:{status_convert} A:{status_apl_exe} P:{status_python_exe} Par:{status_parity} | Fallback:{fallback} | {result.latency_ms:6.2f}ms")
        
        if result.understand_error:
            print(f"  └─ Understand Error: {result.understand_error[:60]}")
        if result.convert_error:
            print(f"  └─ Convert Error: {result.convert_error[:60]}")
        if result.apl_execute_error:
            print(f"  └─ APL Execute Error: {result.apl_execute_error[:60]}")
        if result.python_execute_error:
            print(f"  └─ Python Execute Error: {result.python_execute_error[:60]}")
        if result.parity_error:
            print(f"  └─ Parity Error: {result.parity_error[:60]}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        total = len(self.results)
        understand_pass = sum(1 for r in self.results if r.understand_pass)
        convert_pass = sum(1 for r in self.results if r.convert_pass)
        apl_execute_pass = sum(1 for r in self.results if r.apl_execute_pass)
        python_execute_pass = sum(1 for r in self.results if r.python_execute_pass)
        parity_pass = sum(1 for r in self.results if r.parity_pass)
        fallback_used = sum(1 for r in self.results if r.fallback_used)
        avg_latency = np.mean([r.latency_ms for r in self.results]) if self.results else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total,
                "understand_pass": understand_pass,
                "understand_rate": f"{(understand_pass/total*100):.1f}%" if total > 0 else "N/A",
                "convert_pass": convert_pass,
                "convert_rate": f"{(convert_pass/total*100):.1f}%" if total > 0 else "N/A",
                "apl_execute_pass": apl_execute_pass,
                "apl_execute_rate": f"{(apl_execute_pass/total*100):.1f}%" if total > 0 else "N/A",
                "python_execute_pass": python_execute_pass,
                "python_execute_rate": f"{(python_execute_pass/total*100):.1f}%" if total > 0 else "N/A",
                "parity_pass": parity_pass,
                "parity_rate": f"{(parity_pass/total*100):.1f}%" if total > 0 else "N/A",
                "fallback_used": fallback_used,
                "average_latency_ms": f"{avg_latency:.2f}"
            },
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any]):
        """Save report to JSON and markdown files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_file = self.output_dir / f"benchmark_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save markdown report
        md_file = self.output_dir / f"benchmark_report_{timestamp}.md"
        with open(md_file, 'w') as f:
            f.write(self._generate_markdown_report(report))
        
        print(f"\nReports saved:")
        print(f"  - JSON: {json_file}")
        print(f"  - Markdown: {md_file}")
        
        return json_file, md_file
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown formatted report"""
        summary = report["summary"]
        
        md = f"""# APL-to-Python Benchmark Report

Generated: {report['timestamp']}

## Summary

| Metric | Result | Rate |
|--------|--------|------|
| Total Tests | {summary['total_tests']} | - |
| Understand Pass | {summary['understand_pass']} | {summary['understand_rate']} |
| Convert Pass | {summary['convert_pass']} | {summary['convert_rate']} |
| APL Execute Pass | {summary['apl_execute_pass']} | {summary['apl_execute_rate']} |
| Python Execute Pass | {summary['python_execute_pass']} | {summary['python_execute_rate']} |
| Parity Pass | {summary['parity_pass']} | {summary['parity_rate']} |
| Fallback Used | {summary['fallback_used']} | - |
| Average Latency | - | {summary['average_latency_ms']}ms |

## Detailed Results

| Test | U | C | APL-E | Py-E | Parity | Fallback | Latency |
|------|---|---|-------|------|--------|----------|---------|
"""
        
        for result in report["detailed_results"]:
            u = "✓" if result["understand_pass"] else "✗"
            c = "✓" if result["convert_pass"] else "✗"
            a = "✓" if result["apl_execute_pass"] else "✗"
            p = "✓" if result["python_execute_pass"] else "✗"
            par = "✓" if result["parity_pass"] else "✗"
            fb = "YES" if result["fallback_used"] else "NO"
            
            md += f"| {result['test_name']} | {u} | {c} | {a} | {p} | {par} | {fb} | {result['latency_ms']:.2f}ms |\n"
        
        return md


def main():
    """Main entry point"""
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    benchmark_dir = project_root / "tests" / "benchmark"
    output_dir = project_root / "outputs" / "benchmark_results"
    
    if not benchmark_dir.exists():
        print(f"Error: Benchmark directory not found: {benchmark_dir}")
        sys.exit(1)
    
    # Run benchmarks
    runner = BenchmarkRunner(benchmark_dir, output_dir)
    results = runner.run_all_tests()
    
    # Generate and save report
    print("\n" + "=" * 80)
    print("BENCHMARK REPORT")
    print("=" * 80)
    
    report = runner.generate_report()
    
    # Print summary
    summary = report["summary"]
    print(f"\nTotal Tests: {summary['total_tests']}")
    print(f"Understand: {summary['understand_pass']}/{summary['total_tests']} ({summary['understand_rate']})")
    print(f"Convert: {summary['convert_pass']}/{summary['total_tests']} ({summary['convert_rate']})")
    print(f"APL Execute: {summary['apl_execute_pass']}/{summary['total_tests']} ({summary['apl_execute_rate']})")
    print(f"Python Execute: {summary['python_execute_pass']}/{summary['total_tests']} ({summary['python_execute_rate']})")
    print(f"Parity: {summary['parity_pass']}/{summary['total_tests']} ({summary['parity_rate']})")
    print(f"Fallback Used: {summary['fallback_used']}")
    print(f"Average Latency: {summary['average_latency_ms']}ms")
    
    # Save reports
    runner.save_report(report)
    
    print("\n✓ Benchmark suite completed")


if __name__ == "__main__":
    main()
