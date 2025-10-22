#!/usr/bin/env python3

"""
Post-Experiment Analysis Tool
Analizza i risultati del First Task Experiment e genera report dettagliati
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def load_metrics(filename: str) -> Dict[str, Any]:
    """Load metrics from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: Metrics file '{filename}' not found{Colors.END}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"{Colors.RED}Error: Invalid JSON in '{filename}'{Colors.END}")
        sys.exit(1)


def print_header(text: str):
    """Print a colored header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_section(text: str):
    """Print a section title"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*len(text)}{Colors.END}")


def analyze_timing(metrics: Dict[str, Any]):
    """Analyze timing metrics"""
    print_section("⏱️  TIMING ANALYSIS")
    
    timing = metrics['timing']
    
    print(f"\n{Colors.BOLD}Operation Times:{Colors.END}")
    print(f"  Task Creation:        {timing['task_creation_ms']:>6} ms")
    print(f"  Claim Operation:      {timing['claim_operation_ms']:>6} ms")
    print(f"  Complete Operation:   {timing['complete_operation_ms']:>6} ms")
    
    print(f"\n{Colors.BOLD}Propagation Times:{Colors.END}")
    print(f"  Task Propagation:     {timing['task_propagation_ms']:>6} ms")
    print(f"  Claim Propagation:    {timing['claim_propagation_ms']:>6} ms")
    print(f"  Complete Propagation: {timing['complete_propagation_ms']:>6} ms")
    
    print(f"\n{Colors.BOLD}Total Duration:{Colors.END}")
    total_seconds = timing['total_duration_ms'] / 1000
    print(f"  {timing['total_duration_ms']:>6} ms ({total_seconds:.2f} seconds)")
    
    # Performance evaluation
    print(f"\n{Colors.BOLD}Performance Evaluation:{Colors.END}")
    
    avg_propagation = (timing['task_propagation_ms'] + 
                       timing['claim_propagation_ms'] + 
                       timing['complete_propagation_ms']) / 3
    
    if avg_propagation < 5000:
        perf_rating = f"{Colors.GREEN}Excellent{Colors.END}"
    elif avg_propagation < 10000:
        perf_rating = f"{Colors.YELLOW}Good{Colors.END}"
    else:
        perf_rating = f"{Colors.RED}Needs Improvement{Colors.END}"
    
    print(f"  Average Propagation Time: {avg_propagation:.0f} ms")
    print(f"  Rating: {perf_rating}")


def analyze_economics(metrics: Dict[str, Any]):
    """Analyze economic metrics"""
    print_section("💰 ECONOMIC ANALYSIS")
    
    econ = metrics['economic']
    
    print(f"\n{Colors.BOLD}Creator (Node 1):{Colors.END}")
    print(f"  Initial Balance:  {econ['creator_initial_sp']:>6} SP")
    print(f"  Final Balance:    {econ['creator_final_sp']:>6} SP")
    
    if econ['creator_delta_sp'] == -10:
        delta_color = Colors.GREEN
    else:
        delta_color = Colors.RED
    print(f"  Delta:            {delta_color}{econ['creator_delta_sp']:>6} SP{Colors.END}")
    
    print(f"\n{Colors.BOLD}Contributor (Node 2):{Colors.END}")
    print(f"  Initial Balance:  {econ['contributor_initial_sp']:>6} SP")
    print(f"  Final Balance:    {econ['contributor_final_sp']:>6} SP")
    
    if econ['contributor_delta_sp'] >= 9 and econ['contributor_delta_sp'] <= 10:
        delta_color = Colors.GREEN
    else:
        delta_color = Colors.RED
    print(f"  Delta:            {delta_color}{econ['contributor_delta_sp']:>+6} SP{Colors.END}")
    print(f"  Reputation Gain:  {Colors.GREEN}{econ['contributor_reputation_gain']:>6}{Colors.END}")
    
    print(f"\n{Colors.BOLD}Treasury:{Colors.END}")
    print(f"  Tax Collected:    {Colors.CYAN}{econ['tax_collected_sp']:>6} SP{Colors.END}")
    
    # Calculate ROI for creator
    print(f"\n{Colors.BOLD}Economic Efficiency:{Colors.END}")
    cost_per_sp = abs(econ['creator_delta_sp'])
    received_sp = econ['contributor_delta_sp']
    efficiency = (received_sp / cost_per_sp * 100) if cost_per_sp > 0 else 0
    
    print(f"  SP Transfer Efficiency: {efficiency:.1f}%")
    print(f"  Tax Rate: {econ['tax_collected_sp'] / 10 * 100:.1f}%")
    
    # Qualitative assessment
    print(f"\n{Colors.BOLD}Value Assessment:{Colors.END}")
    print(f"  Creator paid:     10 SP")
    print(f"  Received value:   1 Bug Report (qualitative)")
    print(f"  Contributor ROI:  Gained {econ['contributor_delta_sp']} SP + {econ['contributor_reputation_gain']} reputation")


def analyze_consensus(metrics: Dict[str, Any]):
    """Analyze consensus metrics"""
    print_section("🔗 CONSENSUS ANALYSIS")
    
    consensus = metrics['consensus']
    
    print(f"\n{Colors.BOLD}Consensus Checks:{Colors.END}")
    
    balance_status = f"{Colors.GREEN}✓ YES{Colors.END}" if consensus['balance_consensus'] else f"{Colors.RED}✗ NO{Colors.END}"
    status_status = f"{Colors.GREEN}✓ YES{Colors.END}" if consensus['status_consensus'] else f"{Colors.RED}✗ NO{Colors.END}"
    
    print(f"  Balance Consensus:  {balance_status}")
    print(f"  Status Consensus:   {status_status}")
    
    print(f"\n{Colors.BOLD}Checkpoints:{Colors.END}")
    for i in range(1, 4):
        checkpoint = consensus[f'checkpoint{i}']
        if checkpoint == "PASS":
            status = f"{Colors.GREEN}✓ PASS{Colors.END}"
        else:
            status = f"{Colors.RED}✗ FAIL{Colors.END}"
        
        checkpoint_names = {
            1: "Balance Frozen",
            2: "Task Claimed",
            3: "Reward Transfer"
        }
        print(f"  Checkpoint {i} ({checkpoint_names[i]}): {status}")
    
    # Overall consensus health
    print(f"\n{Colors.BOLD}Consensus Health:{Colors.END}")
    all_pass = all(consensus[f'checkpoint{i}'] == "PASS" for i in range(1, 4))
    if all_pass and consensus['balance_consensus'] and consensus['status_consensus']:
        health = f"{Colors.GREEN}Excellent - All nodes in perfect sync{Colors.END}"
    elif all_pass:
        health = f"{Colors.YELLOW}Good - Minor sync issues detected{Colors.END}"
    else:
        health = f"{Colors.RED}Poor - Consensus failures detected{Colors.END}"
    
    print(f"  {health}")


def generate_summary(metrics: Dict[str, Any]):
    """Generate executive summary"""
    print_section("📊 EXECUTIVE SUMMARY")
    
    result = metrics['result']
    
    if result == "SUCCESS":
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ EXPERIMENT SUCCESSFUL{Colors.END}\n")
        print("The system has successfully demonstrated:")
        print("  1. ✓ Task with reward was created")
        print("  2. ✓ Contributor completed it")
        print("  3. ✓ Automatic SP + reputation transfer")
        print("  4. ✓ All nodes reached consensus")
        print("  5. ✓ No human approval required")
        
        print(f"\n{Colors.BOLD}Core Principle Proven:{Colors.END}")
        print("  Contribution → Value (without gatekeepers)")
        
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ EXPERIMENT FAILED{Colors.END}\n")
        print("One or more checkpoints failed.")
        print("Review the detailed logs for debugging.")
    
    # Key metrics at a glance
    print(f"\n{Colors.BOLD}Key Metrics:{Colors.END}")
    print(f"  Total Duration:        {metrics['timing']['total_duration_ms']/1000:.2f}s")
    print(f"  SP Transferred:        {metrics['economic']['contributor_delta_sp']} SP")
    print(f"  Reputation Gained:     {metrics['economic']['contributor_reputation_gain']}")
    print(f"  Consensus Achieved:    {'Yes' if metrics['consensus']['balance_consensus'] else 'No'}")


def generate_recommendations(metrics: Dict[str, Any]):
    """Generate recommendations based on results"""
    print_section("💡 RECOMMENDATIONS")
    
    timing = metrics['timing']
    consensus = metrics['consensus']
    
    recommendations = []
    
    # Timing recommendations
    avg_prop = (timing['task_propagation_ms'] + 
                timing['claim_propagation_ms'] + 
                timing['complete_propagation_ms']) / 3
    
    if avg_prop > 10000:
        recommendations.append(
            "⚠️  High propagation times detected (>10s average).\n"
            "   Consider:\n"
            "   - Reducing gossip interval\n"
            "   - Optimizing network topology\n"
            "   - Checking for network congestion"
        )
    
    # Consensus recommendations
    if not consensus['balance_consensus']:
        recommendations.append(
            "❌ Balance consensus failure detected.\n"
            "   This is critical! Investigate:\n"
            "   - CRDT merge logic\n"
            "   - Clock synchronization\n"
            "   - Race conditions in balance calculation"
        )
    
    if not consensus['status_consensus']:
        recommendations.append(
            "❌ Status consensus failure detected.\n"
            "   Investigate:\n"
            "   - Task state machine transitions\n"
            "   - Gossip message ordering\n"
            "   - Concurrent claim handling"
        )
    
    # Economic recommendations
    econ = metrics['economic']
    if econ['tax_collected_sp'] > 1:
        recommendations.append(
            f"ℹ️  Tax rate is {econ['tax_collected_sp']/10*100:.1f}%.\n"
            f"   Consider making this governance-adjustable."
        )
    
    # Next steps
    if metrics['result'] == "SUCCESS":
        recommendations.append(
            "✅ Experiment successful! Next steps:\n"
            "   1. Run with more nodes (5-10)\n"
            "   2. Test concurrent tasks\n"
            "   3. Try auction-based allocation\n"
            "   4. Invite real contributors\n"
            "   5. Document the results publicly"
        )
    else:
        recommendations.append(
            "❌ Experiment failed. Next steps:\n"
            "   1. Review detailed logs\n"
            "   2. Create GitHub issue for bug\n"
            "   3. Fix the identified issue\n"
            "   4. Re-run the experiment\n"
            "   5. Document lessons learned"
        )
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")
    else:
        print("\nNo specific recommendations. System operating nominally.")


def save_report(metrics: Dict[str, Any], output_file: str):
    """Save analysis report to markdown file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(output_file, 'w') as f:
        f.write(f"# First Task Experiment - Analysis Report\n\n")
        f.write(f"**Generated**: {timestamp}\n")
        f.write(f"**Result**: {metrics['result']}\n\n")
        
        f.write("## Executive Summary\n\n")
        if metrics['result'] == "SUCCESS":
            f.write("✅ **EXPERIMENT SUCCESSFUL**\n\n")
            f.write("The system has successfully demonstrated:\n")
            f.write("1. Task with reward was created\n")
            f.write("2. Contributor completed it\n")
            f.write("3. Automatic SP + reputation transfer\n")
            f.write("4. All nodes reached consensus\n")
            f.write("5. No human approval required\n\n")
            f.write("**Core Principle Proven**: Contribution → Value (without gatekeepers)\n\n")
        else:
            f.write("❌ **EXPERIMENT FAILED**\n\n")
        
        f.write("## Timing Metrics\n\n")
        f.write("| Metric | Time (ms) |\n")
        f.write("|--------|----------|\n")
        timing = metrics['timing']
        for key, value in timing.items():
            f.write(f"| {key.replace('_', ' ').title()} | {value} |\n")
        
        f.write("\n## Economic Metrics\n\n")
        econ = metrics['economic']
        f.write(f"- **Creator**: {econ['creator_initial_sp']} SP → {econ['creator_final_sp']} SP (Δ {econ['creator_delta_sp']} SP)\n")
        f.write(f"- **Contributor**: {econ['contributor_initial_sp']} SP → {econ['contributor_final_sp']} SP (Δ +{econ['contributor_delta_sp']} SP)\n")
        f.write(f"- **Reputation Gain**: +{econ['contributor_reputation_gain']}\n")
        f.write(f"- **Tax Collected**: {econ['tax_collected_sp']} SP\n\n")
        
        f.write("## Consensus Metrics\n\n")
        consensus = metrics['consensus']
        f.write(f"- **Balance Consensus**: {'✓ YES' if consensus['balance_consensus'] else '✗ NO'}\n")
        f.write(f"- **Status Consensus**: {'✓ YES' if consensus['status_consensus'] else '✗ NO'}\n")
        f.write(f"- **Checkpoint 1**: {consensus['checkpoint1']}\n")
        f.write(f"- **Checkpoint 2**: {consensus['checkpoint2']}\n")
        f.write(f"- **Checkpoint 3**: {consensus['checkpoint3']}\n\n")
        
        f.write("## Node Information\n\n")
        nodes = metrics['node_ids']
        f.write(f"- **Node 1** (Creator): `{nodes['node1'][:16]}...`\n")
        f.write(f"- **Node 2** (Contributor): `{nodes['node2'][:16]}...`\n")
        f.write(f"- **Node 3** (Observer): `{nodes['node3'][:16]}...`\n")
        f.write(f"- **Task ID**: `{metrics['task_id'][:16]}...`\n")
    
    print(f"\n{Colors.GREEN}✓ Report saved to: {output_file}{Colors.END}")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <metrics_file.json> [output_report.md]")
        sys.exit(1)
    
    metrics_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "analysis_report.md"
    
    print_header("FIRST TASK EXPERIMENT - POST-ANALYSIS")
    
    print(f"{Colors.BOLD}Loading metrics from:{Colors.END} {metrics_file}")
    metrics = load_metrics(metrics_file)
    
    print(f"{Colors.BOLD}Experiment Date:{Colors.END} {metrics['experiment_date']}")
    print(f"{Colors.BOLD}Result:{Colors.END} {metrics['result']}")
    
    # Run analyses
    generate_summary(metrics)
    analyze_timing(metrics)
    analyze_economics(metrics)
    analyze_consensus(metrics)
    generate_recommendations(metrics)
    
    # Save report
    print_section("📄 SAVING REPORT")
    save_report(metrics, output_file)
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}Analysis complete!{Colors.END}\n")


if __name__ == "__main__":
    main()
