#!/usr/bin/env python3
"""
Plan Completion Manager for SolarWindPy
Automatically handles plan lifecycle completion workflow
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import subprocess


def is_plan_completed(plan_dir: Path) -> bool:
    """
    Check if a plan is completed by examining the 0-Overview.md file.
    
    Args:
        plan_dir: Path to the plan directory
        
    Returns:
        True if plan shows completion status
    """
    overview_file = plan_dir / "0-Overview.md"
    
    if not overview_file.exists():
        return False
    
    try:
        with open(overview_file, 'r') as f:
            content = f.read()
        
        # Check for completion indicators
        completion_markers = [
            "Status**: Completed",
            "Status: Completed", 
            "**Status**: Completed",
            "- **Status**: Completed"
        ]
        
        # Check for phase completion (all phases marked with [x])
        lines = content.split('\n')
        phase_lines = [line for line in lines if '**Phase' in line and ('Est:' in line or 'hours' in line)]
        
        if phase_lines:
            # All phase lines should start with [x] for completion
            completed_phases = [line for line in phase_lines if line.strip().startswith('- [x]')]
            if len(completed_phases) == len(phase_lines):
                return True
        
        # Check for explicit completion status
        for marker in completion_markers:
            if marker in content:
                return True
                
        return False
        
    except Exception as e:
        print(f"⚠️  Error reading {overview_file}: {e}")
        return False


def move_plan_to_completed(plan_name: str, source_dir: Path, completed_dir: Path) -> bool:
    """
    Move a completed plan to the completed directory.
    
    Args:
        plan_name: Name of the plan
        source_dir: Source plan directory
        completed_dir: Destination completed directory
        
    Returns:
        True if move was successful
    """
    try:
        # Ensure completed directory exists
        completed_dir.mkdir(exist_ok=True)
        
        # Target location
        target_dir = completed_dir / plan_name
        
        # Check if target already exists
        if target_dir.exists():
            print(f"⚠️  Plan already exists in completed: {target_dir}")
            return False
        
        # Move the plan
        shutil.move(str(source_dir), str(target_dir))
        print(f"✅ Moved completed plan: {plan_name} → plans/completed/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error moving plan {plan_name}: {e}")
        return False


def preserve_plan_branches(plan_name: str) -> dict:
    """
    Ensure plan branches are preserved and not deleted.
    
    Args:
        plan_name: Name of the plan
        
    Returns:
        Dictionary with branch preservation status
    """
    try:
        # Check which branches exist for this plan
        result = subprocess.run(
            ['git', 'branch', '--all'], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            return {"error": "Failed to list git branches"}
        
        branches = result.stdout.split('\n')
        plan_branches = []
        
        for branch in branches:
            branch = branch.strip().replace('*', '').strip()
            if f"plan/{plan_name}" in branch or f"feature/{plan_name}" in branch:
                plan_branches.append(branch)
        
        # Log branch preservation
        preservation_log = {
            "plan_name": plan_name,
            "timestamp": datetime.now().isoformat(),
            "preserved_branches": plan_branches,
            "note": "Branches preserved for auditing purposes - DO NOT DELETE"
        }
        
        # Write preservation record
        log_file = Path('.claude/branch-preservation.log')
        
        # Append to log file
        with open(log_file, 'a') as f:
            f.write(f"{json.dumps(preservation_log)}\n")
        
        print(f"🔒 Branch preservation logged: {len(plan_branches)} branches for {plan_name}")
        
        return preservation_log
        
    except Exception as e:
        return {"error": f"Failed to preserve branches: {e}"}


def scan_and_archive_completed_plans():
    """
    Scan all plans and automatically move completed ones to plans/completed/
    """
    print("🔍 Scanning for completed plans...")
    
    plans_dir = Path('plans')
    completed_dir = plans_dir / 'completed'
    
    if not plans_dir.exists():
        print("❌ Plans directory not found")
        return
    
    moved_plans = []
    preserved_branches = []
    
    # Scan all plan directories (excluding completed, abandoned, and special files)
    for item in plans_dir.iterdir():
        if item.is_dir() and item.name not in ['completed', 'abandoned']:
            
            print(f"📋 Checking plan: {item.name}")
            
            if is_plan_completed(item):
                print(f"✅ Plan completed: {item.name}")
                
                # Preserve branches before moving
                branch_status = preserve_plan_branches(item.name)
                preserved_branches.append(branch_status)
                
                # Move to completed
                if move_plan_to_completed(item.name, item, completed_dir):
                    moved_plans.append(item.name)
                    
            else:
                print(f"⏳ Plan still active: {item.name}")
    
    # Summary
    if moved_plans:
        print(f"\n📊 Summary:")
        print(f"   Moved {len(moved_plans)} completed plans to plans/completed/")
        for plan in moved_plans:
            print(f"   - {plan}")
        
        print(f"\n🔒 Branch Preservation:")
        for branch_info in preserved_branches:
            if 'error' not in branch_info:
                plan_name = branch_info['plan_name']
                branch_count = len(branch_info['preserved_branches'])
                print(f"   - {plan_name}: {branch_count} branches preserved")
    else:
        print("\n📊 No completed plans found to archive")


def main():
    """Main entry point for plan completion manager."""
    
    # Change to repository root
    if Path('.git').exists():
        print("🏠 Running from repository root")
    else:
        print("❌ Not in git repository root")
        return
    
    scan_and_archive_completed_plans()


if __name__ == "__main__":
    main()