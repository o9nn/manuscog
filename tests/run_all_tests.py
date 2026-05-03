#!/usr/bin/env python3
"""
Comprehensive Test Runner
=========================

Runs all test suites and generates a validation report.
"""

import sys
import os
import unittest
import time
import io
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def run_test_suite(test_module: str) -> Tuple[int, int, int, float, str]:
    """
    Run a test suite and return results.
    
    Returns: (tests_run, failures, errors, duration, output)
    """
    # Capture output
    output = io.StringIO()
    
    # Create test suite
    loader = unittest.TestLoader()
    
    try:
        suite = loader.loadTestsFromName(test_module)
    except Exception as e:
        return (0, 0, 1, 0, f"Failed to load {test_module}: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(stream=output, verbosity=2)
    
    start_time = time.time()
    result = runner.run(suite)
    duration = time.time() - start_time
    
    return (
        result.testsRun,
        len(result.failures),
        len(result.errors),
        duration,
        output.getvalue()
    )


def run_all_tests() -> Dict[str, Tuple[int, int, int, float, str]]:
    """Run all test suites."""
    test_suites = [
        'test_cognitive_kernel',
        'test_pln_advanced',
        'test_ecan_advanced',
        'test_pattern_moses_advanced',
        'test_integration',
        'test_distributed',
    ]
    
    results = {}
    
    for suite in test_suites:
        print(f"\n{'='*60}")
        print(f" Running: {suite}")
        print('='*60)
        
        tests_run, failures, errors, duration, output = run_test_suite(suite)
        results[suite] = (tests_run, failures, errors, duration, output)
        
        status = "PASSED" if failures == 0 and errors == 0 else "FAILED"
        print(f"\n{suite}: {status}")
        print(f"  Tests: {tests_run}, Failures: {failures}, Errors: {errors}")
        print(f"  Duration: {duration:.2f}s")
    
    return results


def generate_validation_report(results: Dict[str, Tuple[int, int, int, float, str]]) -> str:
    """Generate a comprehensive validation report."""
    report = []
    
    # Header
    report.append("# OpenCog Inferno AGI - Validation Report")
    report.append("")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Summary
    total_tests = sum(r[0] for r in results.values())
    total_failures = sum(r[1] for r in results.values())
    total_errors = sum(r[2] for r in results.values())
    total_duration = sum(r[3] for r in results.values())
    
    overall_status = "PASSED" if total_failures == 0 and total_errors == 0 else "FAILED"
    
    report.append("## Executive Summary")
    report.append("")
    report.append(f"| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| Overall Status | **{overall_status}** |")
    report.append(f"| Total Tests | {total_tests} |")
    report.append(f"| Passed | {total_tests - total_failures - total_errors} |")
    report.append(f"| Failures | {total_failures} |")
    report.append(f"| Errors | {total_errors} |")
    report.append(f"| Total Duration | {total_duration:.2f}s |")
    report.append("")
    
    # Test Suite Results
    report.append("## Test Suite Results")
    report.append("")
    report.append("| Suite | Tests | Passed | Failed | Errors | Duration |")
    report.append("|-------|-------|--------|--------|--------|----------|")
    
    for suite, (tests, failures, errors, duration, _) in results.items():
        passed = tests - failures - errors
        status_icon = "✓" if failures == 0 and errors == 0 else "✗"
        report.append(
            f"| {status_icon} {suite} | {tests} | {passed} | {failures} | {errors} | {duration:.2f}s |"
        )
    
    report.append("")
    
    # Detailed Results
    report.append("## Detailed Results")
    report.append("")
    
    for suite, (tests, failures, errors, duration, output) in results.items():
        status = "PASSED" if failures == 0 and errors == 0 else "FAILED"
        report.append(f"### {suite}")
        report.append("")
        report.append(f"**Status:** {status}")
        report.append(f"**Tests Run:** {tests}")
        report.append(f"**Duration:** {duration:.2f}s")
        report.append("")
        
        if failures > 0 or errors > 0:
            report.append("**Issues:**")
            report.append("```")
            # Extract failure/error messages from output
            lines = output.split('\n')
            in_failure = False
            for line in lines:
                if 'FAIL:' in line or 'ERROR:' in line:
                    in_failure = True
                if in_failure:
                    report.append(line)
                    if line.strip() == '' and in_failure:
                        in_failure = False
            report.append("```")
        report.append("")
    
    # Component Validation
    report.append("## Component Validation")
    report.append("")
    
    components = [
        ("AtomSpace Hypergraph", "test_cognitive_kernel", "Core knowledge representation"),
        ("PLN Reasoning Engine", "test_pln_advanced", "Probabilistic logic inference"),
        ("ECAN Attention System", "test_ecan_advanced", "Economic attention allocation"),
        ("Pattern Recognition", "test_pattern_moses_advanced", "Pattern mining and recognition"),
        ("MOSES Learning", "test_pattern_moses_advanced", "Program synthesis and learning"),
        ("Integration Layer", "test_integration", "Cross-subsystem coordination"),
        ("Distributed System", "test_distributed", "Multi-node operations"),
    ]
    
    report.append("| Component | Status | Description |")
    report.append("|-----------|--------|-------------|")
    
    for component, suite, description in components:
        if suite in results:
            tests, failures, errors, _, _ = results[suite]
            status = "✓ Validated" if failures == 0 and errors == 0 else "✗ Issues Found"
        else:
            status = "⚠ Not Tested"
        report.append(f"| {component} | {status} | {description} |")
    
    report.append("")
    
    # Recommendations
    report.append("## Recommendations")
    report.append("")
    
    if total_failures > 0 or total_errors > 0:
        report.append("### Issues to Address")
        report.append("")
        for suite, (tests, failures, errors, _, _) in results.items():
            if failures > 0 or errors > 0:
                report.append(f"- **{suite}**: {failures} failures, {errors} errors")
        report.append("")
    
    report.append("### Next Steps")
    report.append("")
    report.append("1. Review and fix any failing tests")
    report.append("2. Run performance benchmarks for optimization opportunities")
    report.append("3. Conduct integration testing in multi-node environment")
    report.append("4. Perform stress testing under sustained load")
    report.append("")
    
    # Footer
    report.append("---")
    report.append("")
    report.append("*This report was automatically generated by the OpenCog Inferno AGI validation suite.*")
    
    return "\n".join(report)


def main():
    """Main entry point."""
    print("=" * 60)
    print(" OpenCog Inferno AGI - Comprehensive Test Suite")
    print("=" * 60)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to tests directory
    os.chdir(os.path.dirname(__file__))
    
    # Run all tests
    results = run_all_tests()
    
    # Generate report
    report = generate_validation_report(results)
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), 'VALIDATION_REPORT.md')
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Print summary
    print("\n" + "=" * 60)
    print(" Test Summary")
    print("=" * 60)
    
    total_tests = sum(r[0] for r in results.values())
    total_failures = sum(r[1] for r in results.values())
    total_errors = sum(r[2] for r in results.values())
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {total_tests - total_failures - total_errors}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")
    
    overall_status = "PASSED" if total_failures == 0 and total_errors == 0 else "FAILED"
    print(f"\nOverall Status: {overall_status}")
    print(f"\nValidation report saved to: {report_path}")
    
    # Return exit code
    return 0 if total_failures == 0 and total_errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
