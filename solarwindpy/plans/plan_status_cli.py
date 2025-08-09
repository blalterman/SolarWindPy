#!/usr/bin/env python3
"""
Command line interface for the planning agents status tracking system.

Usage:
    python -m solarwindpy.plans.plan_status_cli [command] [options]
    
Commands:
    list        - List all discovered plans
    status      - Show detailed status for a specific plan
    report      - Generate comprehensive status report
    summary     - Show brief summary of all plans
"""

import sys
import argparse
import json
from pathlib import Path
from .status_tracker import StatusTracker


def format_time(minutes: int) -> str:
    """Format time in minutes to human-readable string."""
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f}h"
    days = hours / 24
    return f"{days:.1f}d"


def format_percentage(percentage: float) -> str:
    """Format percentage with appropriate color coding."""
    if percentage >= 100:
        return f"✅ {percentage:.1f}%"
    elif percentage >= 80:
        return f"🟡 {percentage:.1f}%"
    elif percentage >= 50:
        return f"🟠 {percentage:.1f}%"
    elif percentage > 0:
        return f"🔴 {percentage:.1f}%"
    else:
        return f"⚪ {percentage:.1f}%"


def format_status(status: str) -> str:
    """Format status with appropriate emoji."""
    status_map = {
        'completed': '✅ Completed',
        'in_progress': '🔄 In Progress',
        'paused': '⏸️ Paused',
        'planning': '📋 Planning',
        'pending': '⏳ Pending'
    }
    return status_map.get(status.lower(), f"❓ {status}")


def list_plans(tracker: StatusTracker) -> None:
    """List all discovered plans."""
    plans = tracker.discover_plans()
    
    if not plans:
        print("No plans found.")
        return
    
    print(f"Found {len(plans)} plan(s):")
    for i, plan_name in enumerate(plans, 1):
        print(f"  {i}. {plan_name}")


def show_plan_status(tracker: StatusTracker, plan_name: str) -> None:
    """Show detailed status for a specific plan."""
    status = tracker.get_plan_status(plan_name)
    
    if not status:
        print(f"Plan '{plan_name}' not found.")
        return
    
    print(f"\n📋 Plan: {status.plan_name}")
    print(f"   Status: {format_status(status.status)}")
    print(f"   Progress: {format_percentage(status.overall_completion_percentage)}")
    
    if status.estimated_duration:
        print(f"   Estimated Duration: {format_time(status.estimated_duration)}")
    if status.time_invested:
        print(f"   Time Invested: {format_time(status.time_invested)}")
    
    estimated_completion = status.estimated_completion_time
    if estimated_completion:
        print(f"   Estimated Completion: {format_time(estimated_completion)}")
    
    if status.created_date:
        print(f"   Created: {status.created_date}")
    if status.last_updated:
        print(f"   Last Updated: {status.last_updated}")
    
    # Show phases
    if status.phases:
        print(f"\n   Phases ({len(status.phases)}):")
        for i, phase in enumerate(status.phases, 1):
            completion = format_percentage(phase.completion_percentage)
            print(f"   {i}. {phase.name}: {completion}")
            
            if phase.tasks:
                for j, task in enumerate(phase.tasks, 1):
                    task_status = format_status(task.status)
                    task_name = task.name[:50] + "..." if len(task.name) > 50 else task.name
                    print(f"      {i}.{j} {task_name}: {task_status}")
    
    # Show acceptance criteria
    if status.acceptance_criteria:
        completed_criteria = sum(1 for c in status.acceptance_criteria if c['completed'])
        total_criteria = len(status.acceptance_criteria)
        print(f"\n   Acceptance Criteria: {completed_criteria}/{total_criteria} completed")
        
        for i, criteria in enumerate(status.acceptance_criteria, 1):
            status_icon = "✅" if criteria['completed'] else "⬜"
            print(f"   {status_icon} {criteria['description']}")
    
    # Show blockers
    if status.blockers:
        print(f"\n   ⚠️ Blockers ({len(status.blockers)}):")
        for blocker in status.blockers:
            print(f"   - {blocker}")
    
    # Show notes
    if status.notes:
        print(f"\n   📝 Notes:")
        # Show first few lines of notes
        notes_lines = status.notes.split('\n')[:3]
        for line in notes_lines:
            if line.strip():
                print(f"   {line.strip()}")
        if len(status.notes.split('\n')) > 3:
            print("   ...")


def show_summary(tracker: StatusTracker) -> None:
    """Show brief summary of all plans."""
    plans = tracker.get_all_plans_status()
    
    if not plans:
        print("No plans found.")
        return
    
    print(f"\n📊 Plans Summary ({len(plans)} total):")
    print("=" * 50)
    
    for plan in sorted(plans, key=lambda p: p.overall_completion_percentage, reverse=True):
        progress = format_percentage(plan.overall_completion_percentage)
        status_str = format_status(plan.status)
        
        # Truncate plan name if too long
        name = plan.plan_name[:25] + "..." if len(plan.plan_name) > 25 else plan.plan_name
        print(f"{name:30} {progress:15} {status_str}")


def generate_report(tracker: StatusTracker, output_file: str = None) -> None:
    """Generate comprehensive status report."""
    report = tracker.generate_status_report()
    
    if output_file:
        # Remove non-serializable plan_objects for JSON export
        json_report = {k: v for k, v in report.items() if k != 'plan_objects'}
        with open(output_file, 'w') as f:
            json.dump(json_report, f, indent=2)
        print(f"Report saved to {output_file}")
        return
    
    # Print human-readable report
    print(f"\n📈 Comprehensive Status Report")
    print(f"Generated: {report['timestamp']}")
    print("=" * 50)
    
    print(f"Total Plans: {report['total_plans']}")
    print(f"Completed: {report['completed_plans']}")
    print(f"In Progress: {report['in_progress_plans']}")
    print(f"Overall Progress: {format_percentage(report['overall_completion_percentage'])}")
    
    if report['total_estimated_time_hours'] > 0:
        print(f"Total Estimated Time: {report['total_estimated_time_hours']:.1f}h")
    if report['total_invested_time_hours'] > 0:
        print(f"Total Invested Time: {report['total_invested_time_hours']:.1f}h")
    
    if report['active_blockers'] > 0:
        print(f"⚠️ Active Blockers: {report['active_blockers']}")
    
    # Show recommendations
    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"  {i}. {recommendation}")
    
    # Show top plans by progress
    plan_objects = report.get('plan_objects', [])
    if plan_objects:
        plans_by_progress = sorted(
            plan_objects, 
            key=lambda p: p.overall_completion_percentage, 
            reverse=True
        )
        
        print(f"\n🎯 Top Plans by Progress:")
        for i, plan in enumerate(plans_by_progress[:5], 1):
            progress = format_percentage(plan.overall_completion_percentage)
            print(f"  {i}. {plan.plan_name}: {progress}")
    else:
        # Fallback to dictionary access if plan_objects not available
        plans_by_progress = sorted(
            report['plans'], 
            key=lambda p: p.get('overall_completion_percentage', 0), 
            reverse=True
        )
        
        print(f"\n🎯 Top Plans by Progress:")
        for i, plan in enumerate(plans_by_progress[:5], 1):
            progress = format_percentage(plan.get('overall_completion_percentage', 0))
            print(f"  {i}. {plan.get('plan_name', 'Unknown')}: {progress}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Planning Agents Status Tracking System",
        epilog="Use 'python -m solarwindpy.plans.plan_status_cli <command> -h' for command-specific help."
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all discovered plans')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show detailed status for a plan')
    status_parser.add_argument('plan_name', help='Name of the plan to show status for')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show brief summary of all plans')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate comprehensive status report')
    report_parser.add_argument('-o', '--output', help='Output file for JSON report')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize status tracker
    tracker = StatusTracker()
    
    # Execute command
    try:
        if args.command == 'list':
            list_plans(tracker)
        elif args.command == 'status':
            show_plan_status(tracker, args.plan_name)
        elif args.command == 'summary':
            show_summary(tracker)
        elif args.command == 'report':
            generate_report(tracker, args.output)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()