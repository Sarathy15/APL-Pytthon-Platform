import asyncio
import json
from pathlib import Path
from typing import Any

from backend.agents.conversion_agent import ConversionAgent
from backend.agents.understanding_agent import UnderstandingAgent
from backend.comparator.engine import ComparatorEngine
from backend.execution.python_runner import PythonRunner
from backend.execution.apl_runner import APLRunner
from backend.traces.trace_capture import TraceCapture
from backend.traces.trace_replay import TraceReplay

OUTPUT_DIR = Path('outputs') / 'traces' / 'e2e_ai_migration'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TESTS = [
    {
        'name': 'sum_reduction',
        'apl_code': '+/A',
        'inputs': {'A': [1, 2, 3]},
        'expected_output': 6,
    },
    {
        'name': 'product_reduction',
        'apl_code': '×/A',
        'inputs': {'A': [2, 3, 4]},
        'expected_output': 24,
    },
    {
        'name': 'max_reduction',
        'apl_code': '⌈/A',
        'inputs': {'A': [1, 8, 3]},
        'expected_output': 8,
    },
]


async def run_test(case: dict[str, Any]) -> dict[str, Any]:
    understanding = await UnderstandingAgent.analyze(case['apl_code'])
    conversion = await ConversionAgent.convert(case['apl_code'], understanding)

    trace_capture = TraceCapture(output_dir=OUTPUT_DIR)
    trace = trace_capture.capture(
        function_name=case['name'],
        apl_code=case['apl_code'],
        inputs=case['inputs'],
        metadata={'test': case['name']},
    )

    trace_replay = TraceReplay(trace_dir=OUTPUT_DIR)
    replay_report = trace_replay.replay_trace(trace, python_code=conversion['python_code'])

    python_source = conversion['python_code']
    python_exec = PythonRunner.execute(python_source)
    apl_exec = APLRunner.execute(case['apl_code'], inputs=case['inputs'])
    comparator = ComparatorEngine.compare(
        replay_report['apl_output'],
        replay_report['python_output'],
        rtol=1e-7,
        atol=1e-9,
    )

    passed = (
        replay_report['match']
        and replay_report['apl_success']
        and replay_report['python_success']
        and replay_report['apl_output'] == case['expected_output']
        and replay_report['python_output'] == case['expected_output']
    )

    return {
        'name': case['name'],
        'apl_code': case['apl_code'],
        'inputs': case['inputs'],
        'understanding': understanding,
        'generated_python': python_source,
        'trace_saved': True,
        'apl_output': replay_report['apl_output'],
        'python_output': replay_report['python_output'],
        'replay_result': replay_report,
        'comparator_result': comparator,
        'pass': passed,
    }


async def main() -> None:
    results = []
    for case in TESTS:
        results.append(await run_test(case))

    successful = sum(1 for item in results if item['pass'])
    failed = len(results) - successful
    summary = {
        'pipeline_working': failed == 0,
        'successful_conversions': successful,
        'failed_conversions': failed,
        'ready_for_phase5': failed == 0,
        'results': results,
    }

    print(json.dumps(summary, indent=2, default=str))


if __name__ == '__main__':
    asyncio.run(main())
