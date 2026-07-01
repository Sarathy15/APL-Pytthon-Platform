"""
Quick benchmark results tracker and comparison tool

This script helps track benchmark results over time and identify regressions.
Usage: python track_results.py [compare_with_previous]
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import sys


def export_to_csv(json_report: Dict[str, Any], csv_file: Path):
    """Export benchmark results to CSV for easy analysis"""
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write summary section
        writer.writerow(['APL-to-Python Benchmark Results'])
        writer.writerow(['Generated', json_report['timestamp']])
        writer.writerow([])
        
        # Write summary stats
        summary = json_report['summary']
        writer.writerow(['Summary Statistics'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Tests', summary['total_tests']])
        writer.writerow(['Understand Pass', f"{summary['understand_pass']} ({summary['understand_rate']})"])
        writer.writerow(['Convert Pass', f"{summary['convert_pass']} ({summary['convert_rate']})"])
        writer.writerow(['APL Execute Pass', f"{summary['apl_execute_pass']} ({summary['apl_execute_rate']})"])
        writer.writerow(['Python Execute Pass', f"{summary['python_execute_pass']} ({summary['python_execute_rate']})"])
        writer.writerow(['Parity Pass', f"{summary['parity_pass']} ({summary['parity_rate']})"])
        writer.writerow(['Fallback Used', summary['fallback_used']])
        writer.writerow(['Average Latency (ms)', summary['average_latency_ms']])
        writer.writerow([])
        
        # Write detailed results
        writer.writerow(['Detailed Test Results'])
        writer.writerow([
            'Test Name', 'File', 'Understand', 'Convert', 'APL Execute', 
            'Python Execute', 'Parity', 'Fallback', 'Latency (ms)',
            'Understand Error', 'Convert Error', 'APL Error', 'Python Error', 'Parity Error'
        ])
        
        for result in json_report['detailed_results']:
            writer.writerow([
                result['test_name'],
                result['apl_file'],
                'PASS' if result['understand_pass'] else 'FAIL',
                'PASS' if result['convert_pass'] else 'FAIL',
                'PASS' if result['apl_execute_pass'] else 'FAIL',
                'PASS' if result['python_execute_pass'] else 'FAIL',
                'PASS' if result['parity_pass'] else 'FAIL',
                'YES' if result['fallback_used'] else 'NO',
                f"{result['latency_ms']:.2f}",
                result['understand_error'] or '',
                result['convert_error'] or '',
                result['apl_execute_error'] or '',
                result['python_execute_error'] or '',
                result['parity_error'] or ''
            ])


def find_latest_report() -> Path:
    """Find the latest benchmark report"""
    output_dir = Path(__file__).parent.parent.parent / "outputs" / "benchmark_results"
    
    json_files = list(output_dir.glob("benchmark_report_*.json"))
    if not json_files:
        print("No benchmark reports found")
        return None
    
    # Sort by modification time, get newest
    latest = sorted(json_files, key=lambda p: p.stat().st_mtime)[-1]
    return latest


def compare_reports(report1: Dict[str, Any], report2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two benchmark reports to identify changes"""
    
    comparison = {
        "timestamp1": report1['timestamp'],
        "timestamp2": report2['timestamp'],
        "changes": {}
    }
    
    summary1 = report1['summary']
    summary2 = report2['summary']
    
    # Compare metrics
    for key in ['understand_pass', 'convert_pass', 'apl_execute_pass', 'python_execute_pass', 'parity_pass']:
        val1 = summary1[key]
        val2 = summary2[key]
        diff = val2 - val1
        comparison['changes'][key] = {
            'before': val1,
            'after': val2,
            'change': diff,
            'direction': '↑' if diff > 0 else '↓' if diff < 0 else '→'
        }
    
    # Compare latency
    lat1 = float(summary1['average_latency_ms'].rstrip('ms'))
    lat2 = float(summary2['average_latency_ms'].rstrip('ms'))
    diff_lat = lat2 - lat1
    comparison['changes']['average_latency_ms'] = {
        'before': lat1,
        'after': lat2,
        'change': diff_lat,
        'direction': '↓' if diff_lat < 0 else '↑' if diff_lat > 0 else '→'  # Down is better for latency
    }
    
    return comparison


def main():
    """Main entry point"""
    output_dir = Path(__file__).parent.parent.parent / "outputs" / "benchmark_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find latest report
    latest_report_path = find_latest_report()
    
    if not latest_report_path:
        print("Error: No benchmark reports found in outputs/benchmark_results/")
        sys.exit(1)
    
    print(f"Found latest report: {latest_report_path.name}")
    
    # Load and parse the report
    with open(latest_report_path, 'r') as f:
        latest_report = json.load(f)
    
    # Export to CSV
    csv_file = output_dir / latest_report_path.stem.replace('.json', '.csv')
    export_to_csv(latest_report, csv_file)
    print(f"✓ Exported to CSV: {csv_file}")
    
    # If comparing, find previous report
    if len(sys.argv) > 1 and sys.argv[1] == 'compare':
        json_files = sorted(
            output_dir.glob("benchmark_report_*.json"),
            key=lambda p: p.stat().st_mtime
        )
        
        if len(json_files) < 2:
            print("Need at least 2 reports to compare")
            return
        
        previous_report_path = json_files[-2]
        
        with open(previous_report_path, 'r') as f:
            previous_report = json.load(f)
        
        comparison = compare_reports(previous_report, latest_report)
        
        print("\n" + "="*60)
        print("COMPARISON: Previous vs Latest")
        print("="*60)
        
        for metric, change_data in comparison['changes'].items():
            direction = change_data['direction']
            before = change_data['before']
            after = change_data['after']
            change = change_data['change']
            
            print(f"{metric:30} {direction} {before:3} → {after:3} (Δ{change:+.1f})")


if __name__ == "__main__":
    main()
