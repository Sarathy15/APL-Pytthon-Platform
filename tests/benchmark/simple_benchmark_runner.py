"""
Corrected Benchmark Runner - Direct Backend Integration

This script tests the APL-to-Python platform by directly integrating with the backend APIs.
It measures: Understand, Convert, Execute APL, Execute Python, and Parity.
"""

import sys
import json
import time
import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

# Setup path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
from backend.execution.apl_runner import APLRunner
from backend.execution.python_runner import PythonRunner
from backend.agents.understanding_agent import UnderstandingAgent
from backend.agents.conversion_agent import ConversionAgent
from backend.comparator.engine import ComparatorEngine
from backend.providers.provider_factory import ProviderFactory


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
    provider_used: Optional[str] = None


class SimpleBenchmarkRunner:
    """Simplified benchmark runner using actual backend APIs"""
    
    def __init__(self, benchmark_dir: Path, output_dir: Path):
        self.benchmark_dir = benchmark_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.apl_runner = APLRunner()
        self.python_runner = PythonRunner()
        self.comparator = ComparatorEngine()
        
        # Get provider
        self.provider_factory = ProviderFactory()
        self.provider = self.provider_factory.get_provider()
        
        self.results: List[BenchmarkResult] = []
    
    async def run_all_tests(self) -> List[BenchmarkResult]:
        """Run all APL benchmark tests"""
        apl_files = sorted(self.benchmark_dir.glob("*.apl"))
        
        print(f"\n{'='*80}")
        print(f"APL-to-Python Migration Platform - Benchmark Suite")
        print(f"{'='*80}")
        print(f"Found {len(apl_files)} APL test files")
        print(f"Output directory: {self.output_dir}")
        print(f"Provider: {self.provider.__class__.__name__}")
        print(f"{'='*80}\n")
        
        for i, apl_file in enumerate(apl_files, 1):
            print(f"[{i}/{len(apl_files)}] Testing {apl_file.name}...")
            result = await self.run_single_test(apl_file)
            self.results.append(result)
            self.print_result(result)
        
        return self.results
    
    async def run_single_test(self, apl_file: Path) -> BenchmarkResult:
        """Run a single APL benchmark test through the pipeline"""
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
            latency_ms=0.0,
            provider_used=self.provider.__class__.__name__
        )
        
        try:
            # Read APL program
            apl_code = apl_file.read_text(encoding='utf-8').strip()
            
            # Stage 1: Understand (APL semantic analysis)
            try:
                understanding = await UnderstandingAgent.analyze(apl_code)
                result.understand_pass = understanding.get("confidence", 0) > 0
                if not result.understand_pass:
                    result.understand_error = "Low confidence understanding"
            except Exception as e:
                result.understand_error = str(e)[:100]
            
            # Stage 2: Convert APL to Python
            try:
                # Use ConversionAgent for conversion
                conversion_result = await ConversionAgent.convert(apl_code, {})
                
                if conversion_result.get("success"):
                    result.converted_python = conversion_result.get("python_code")
                    result.convert_pass = True
                    result.fallback_used = conversion_result.get("fallback_used", False)
                else:
                    result.convert_error = conversion_result.get("error", "Unknown error")
                    
            except Exception as e:
                result.convert_error = str(e)[:100]
            
            # Stage 3: Execute Original APL
            try:
                apl_result = self.apl_runner.execute(apl_code)
                result.apl_output = apl_result.get("result")
                result.apl_execute_pass = apl_result.get("success", False)
                if not result.apl_execute_pass:
                    result.apl_execute_error = apl_result.get("error", "Unknown error")[:100]
            except Exception as e:
                result.apl_execute_error = str(e)[:100]
            
            # Stage 4: Execute Converted Python
            if result.converted_python:
                try:
                    python_result = self.python_runner.execute(result.converted_python)
                    result.python_output = python_result.get("result")
                    result.python_execute_pass = python_result.get("success", False)
                    if not result.python_execute_pass:
                        result.python_execute_error = python_result.get("error", "Unknown error")[:100]
                except Exception as e:
                    result.python_execute_error = str(e)[:100]
            
            # Stage 5: Check Parity
            if result.apl_execute_pass and result.python_execute_pass:
                try:
                    parity_check = self.comparator.compare(
                        result.apl_output,
                        result.python_output
                    )
                    result.parity_pass = parity_check.get("match", False)
                    if not result.parity_pass:
                        result.parity_error = parity_check.get("reason", "Mismatch")[:100]
                except Exception as e:
                    result.parity_error = str(e)[:100]
        
        except Exception as e:
            result.understand_error = f"Pipeline error: {str(e)}"[:100]
        
        finally:
            result.latency_ms = (time.time() - start_time) * 1000
        
        return result
    
    def print_result(self, result: BenchmarkResult):
        """Print formatted result for a single test"""
        u = "P" if result.understand_pass else "F"
        c = "P" if result.convert_pass else "F"
        a = "P" if result.apl_execute_pass else "F"
        p = "P" if result.python_execute_pass else "F"
        par = "P" if result.parity_pass else "F"
        fb = "Y" if result.fallback_used else "N"
        
        status_line = f"  U:{u} C:{c} A:{a} Py:{p} Par:{par} | FB:{fb} | {result.latency_ms:6.1f}ms"
        print(status_line)
        
        if result.understand_error:
            print(f"      ✗ Understand: {result.understand_error}")
        if result.convert_error:
            print(f"      ✗ Convert: {result.convert_error}")
        if result.apl_execute_error:
            print(f"      ✗ APL Exec: {result.apl_execute_error}")
        if result.python_execute_error:
            print(f"      ✗ Py Exec: {result.python_execute_error}")
        if result.parity_error:
            print(f"      ✗ Parity: {result.parity_error}")
    
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
        max_latency = np.max([r.latency_ms for r in self.results]) if self.results else 0
        min_latency = np.min([r.latency_ms for r in self.results]) if self.results else 0
        
        # Analyze failures
        failed_understand = [r for r in self.results if not r.understand_pass]
        failed_convert = [r for r in self.results if not r.convert_pass]
        failed_apl_exec = [r for r in self.results if not r.apl_execute_pass]
        failed_python_exec = [r for r in self.results if not r.python_execute_pass]
        failed_parity = [r for r in self.results if not r.parity_pass]
        
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
                "fallback_rate": f"{(fallback_used/total*100):.1f}%" if total > 0 else "N/A",
                "average_latency_ms": f"{avg_latency:.2f}",
                "max_latency_ms": f"{max_latency:.2f}",
                "min_latency_ms": f"{min_latency:.2f}",
            },
            "failures": {
                "understand_failures": len(failed_understand),
                "convert_failures": len(failed_convert),
                "apl_execute_failures": len(failed_apl_exec),
                "python_execute_failures": len(failed_python_exec),
                "parity_failures": len(failed_parity),
            },
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any]):
        """Save report to JSON and markdown files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_file = self.output_dir / f"benchmark_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save markdown report
        md_file = self.output_dir / f"benchmark_report_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown_report(report))
        
        print(f"\nReports saved:")
        print(f"  - JSON: {json_file}")
        print(f"  - Markdown: {md_file}")
        
        return json_file, md_file
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown formatted report"""
        summary = report["summary"]
        
        md = f"""# APL-to-Python Migration Platform - Benchmark Report

Generated: {report['timestamp']}

## Executive Summary

| Metric | Result | Rate |
|--------|--------|------|
| **Total Tests** | {summary['total_tests']} | - |
| **Understanding** | {summary['understand_pass']} | {summary['understand_rate']} |
| **Conversion** | {summary['convert_pass']} | {summary['convert_rate']} |
| **APL Execution** | {summary['apl_execute_pass']} | {summary['apl_execute_rate']} |
| **Python Execution** | {summary['python_execute_pass']} | {summary['python_execute_rate']} |
| **Parity** | {summary['parity_pass']} | {summary['parity_rate']} |
| **Fallback Used** | {summary['fallback_used']} | {summary['fallback_rate']} |

## Performance

| Metric | Value |
|--------|-------|
| **Average Latency** | {summary['average_latency_ms']}ms |
| **Max Latency** | {summary['max_latency_ms']}ms |
| **Min Latency** | {summary['min_latency_ms']}ms |

## Failures

| Component | Failures |
|-----------|----------|
| Understanding | {report['failures']['understand_failures']} |
| Conversion | {report['failures']['convert_failures']} |
| APL Execution | {report['failures']['apl_execute_failures']} |
| Python Execution | {report['failures']['python_execute_failures']} |
| Parity | {report['failures']['parity_failures']} |

## Test Results

| Test | U | C | APL | Py | Par | FB | Latency |
|------|---|---|-----|----|----|----|----|
"""
        
        for result in report["detailed_results"]:
            u = "P" if result["understand_pass"] else "F"
            c = "P" if result["convert_pass"] else "F"
            a = "P" if result["apl_execute_pass"] else "F"
            p = "P" if result["python_execute_pass"] else "F"
            par = "P" if result["parity_pass"] else "F"
            fb = "Y" if result["fallback_used"] else "N"
            
            md += f"| {result['test_name']:15} | {u} | {c} | {a} | {p} | {par} | {fb} | {result['latency_ms']:.1f}ms |\n"
        
        return md


async def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent.parent
    benchmark_dir = project_root / "tests" / "benchmark"
    output_dir = project_root / "outputs" / "benchmark_results"
    
    if not benchmark_dir.exists():
        print(f"Error: Benchmark directory not found: {benchmark_dir}")
        sys.exit(1)
    
    # Run benchmarks
    runner = SimpleBenchmarkRunner(benchmark_dir, output_dir)
    results = await runner.run_all_tests()
    
    # Generate and save report
    print("\n" + "=" * 80)
    print("BENCHMARK REPORT SUMMARY")
    print("=" * 80)
    
    report = runner.generate_report()
    summary = report["summary"]
    
    print(f"\nResults:")
    print(f"  Total Tests:       {summary['total_tests']}")
    print(f"  Understand:        {summary['understand_pass']}/{summary['total_tests']} ({summary['understand_rate']})")
    print(f"  Convert:           {summary['convert_pass']}/{summary['total_tests']} ({summary['convert_rate']})")
    print(f"  APL Execute:       {summary['apl_execute_pass']}/{summary['total_tests']} ({summary['apl_execute_rate']})")
    print(f"  Python Execute:    {summary['python_execute_pass']}/{summary['total_tests']} ({summary['python_execute_rate']})")
    print(f"  Parity:            {summary['parity_pass']}/{summary['total_tests']} ({summary['parity_rate']})")
    print(f"\nPerformance:")
    print(f"  Fallback Used:     {summary['fallback_used']} ({summary['fallback_rate']})")
    print(f"  Avg Latency:       {summary['average_latency_ms']}ms")
    print(f"  Max Latency:       {summary['max_latency_ms']}ms")
    
    # Save reports
    runner.save_report(report)
    
    print("\n✓ Benchmark suite completed")


if __name__ == "__main__":
    asyncio.run(main())
