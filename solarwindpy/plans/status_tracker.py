"""
Status tracking system for planning agents with multi-source parsing.

This module provides comprehensive status tracking across plan files, git branches,
and JSON status files to enable intelligent progress reporting and coordination.
"""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict


@dataclass
class TaskStatus:
    """Individual task status information."""
    name: str
    estimated_time: Optional[int] = None  # in minutes
    actual_time: Optional[int] = None     # in minutes
    status: str = "pending"  # pending, in_progress, completed
    commit_hash: Optional[str] = None
    dependencies: List[str] = None
    validation_status: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class PhaseStatus:
    """Phase-level status information."""
    name: str
    estimated_time: Optional[int] = None
    actual_time: Optional[int] = None
    status: str = "pending"
    tasks: List[TaskStatus] = None
    
    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage based on completed tasks."""
        if not self.tasks:
            return 0.0
        completed = sum(1 for task in self.tasks if task.status == "completed")
        return (completed / len(self.tasks)) * 100.0


@dataclass
class PlanStatus:
    """Complete plan status with all metadata."""
    plan_name: str
    branch_name: str
    implementation_branch: Optional[str] = None
    status: str = "planning"  # planning, in_progress, paused, completed
    created_date: Optional[str] = None
    last_updated: Optional[str] = None
    estimated_duration: Optional[int] = None  # in minutes
    time_invested: int = 0  # in minutes
    phases: List[PhaseStatus] = None
    acceptance_criteria: List[Dict[str, Any]] = None
    blockers: List[str] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.phases is None:
            self.phases = []
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []
        if self.blockers is None:
            self.blockers = []
    
    @property
    def overall_completion_percentage(self) -> float:
        """Calculate overall completion percentage across all phases."""
        if not self.phases:
            return 0.0
        total_tasks = sum(len(phase.tasks) for phase in self.phases)
        if total_tasks == 0:
            return 0.0
        completed_tasks = sum(
            sum(1 for task in phase.tasks if task.status == "completed") 
            for phase in self.phases
        )
        return (completed_tasks / total_tasks) * 100.0
    
    @property
    def estimated_completion_time(self) -> Optional[int]:
        """Estimate remaining time based on current progress and velocity."""
        if self.time_invested == 0 or self.overall_completion_percentage == 0:
            return self.estimated_duration
        
        velocity = self.overall_completion_percentage / self.time_invested
        remaining_percentage = 100 - self.overall_completion_percentage
        
        if velocity > 0:
            return int(remaining_percentage / velocity)
        return None


class StatusTracker:
    """Multi-source status tracking system for planning agents."""
    
    def __init__(self, plans_directory: str = "solarwindpy/plans"):
        self.plans_directory = Path(plans_directory)
        self.status_cache = {}
        self._git_available = self._check_git_availability()
    
    def _check_git_availability(self) -> bool:
        """Check if git is available and we're in a git repository."""
        try:
            subprocess.run(['git', 'status'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def discover_plans(self) -> List[str]:
        """Discover all available plans from multiple sources."""
        plans = set()
        
        # Source 1: Plan files in plans directory
        if self.plans_directory.exists():
            for plan_file in self.plans_directory.glob("*.md"):
                if not plan_file.name.startswith("template"):
                    plans.add(plan_file.stem)
        
        # Source 2: Git plan branches (plan/*)
        if self._git_available:
            try:
                result = subprocess.run(
                    ['git', 'branch', '-r'], 
                    capture_output=True, text=True, check=True
                )
                for line in result.stdout.splitlines():
                    branch = line.strip().replace('origin/', '')
                    if branch.startswith('plan/'):
                        plan_name = branch.replace('plan/', '')
                        plans.add(plan_name)
            except subprocess.CalledProcessError:
                pass
        
        return sorted(list(plans))
    
    def parse_plan_file(self, plan_name: str) -> Optional[PlanStatus]:
        """Parse a plan markdown file to extract status information."""
        plan_file = self.plans_directory / f"{plan_name}.md"
        
        # Try to find plan file in current directory or on plan branch
        if not plan_file.exists() and self._git_available:
            # Check if file exists on plan branch
            try:
                result = subprocess.run([
                    'git', 'show', f'plan/{plan_name}:{plan_file}'
                ], capture_output=True, text=True, check=True)
                content = result.stdout
            except subprocess.CalledProcessError:
                return None
        else:
            if not plan_file.exists():
                return None
            with open(plan_file, 'r', encoding='utf-8') as f:
                content = f.read()
        
        return self._parse_plan_content(content, plan_name)
    
    def _parse_plan_content(self, content: str, plan_name: str) -> PlanStatus:
        """Parse plan file content to extract structured status information."""
        # Extract metadata
        metadata = self._extract_metadata(content)
        
        # Parse phases and tasks
        phases = self._parse_phases_and_tasks(content)
        
        # Parse acceptance criteria
        acceptance_criteria = self._parse_acceptance_criteria(content)
        
        # Extract progress tracking information
        progress_info = self._extract_progress_info(content)
        
        # Create PlanStatus object
        plan_status = PlanStatus(
            plan_name=plan_name,
            branch_name=f"plan/{plan_name}",
            implementation_branch=metadata.get('implementation_branch'),
            status=metadata.get('status', 'planning').lower(),
            created_date=metadata.get('created'),
            last_updated=metadata.get('last_updated'),
            estimated_duration=metadata.get('estimated_duration'),
            time_invested=progress_info.get('time_invested', 0),
            phases=phases,
            acceptance_criteria=acceptance_criteria,
            blockers=self._extract_blockers(content),
            notes=self._extract_notes(content)
        )
        
        return plan_status
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from plan file."""
        metadata = {}
        
        # Extract from Plan Metadata section
        metadata_match = re.search(
            r'## Plan Metadata\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL
        )
        if metadata_match:
            metadata_text = metadata_match.group(1)
            
            # Extract various metadata fields
            patterns = {
                'implementation_branch': r'Implementation Branch:\*\*\s*(.*?)(?:\n|$)',
                'status': r'Status:\*\*\s*(.*?)(?:\n|$)',
                'created': r'Created:\*\*\s*(.*?)(?:\n|$)',
                'estimated_duration': r'Estimated Duration:\*\*\s*(\d+)\s*min',
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, metadata_text)
                if match:
                    value = match.group(1).strip()
                    if key == 'estimated_duration':
                        metadata[key] = int(value)
                    else:
                        metadata[key] = value
        
        # Extract last updated from Progress Tracking section
        progress_match = re.search(
            r'Last Updated:\*\*\s*(.*?)(?:\n|$)', content
        )
        if progress_match:
            metadata['last_updated'] = progress_match.group(1).strip()
        
        return metadata
    
    def _parse_phases_and_tasks(self, content: str) -> List[PhaseStatus]:
        """Parse phases and tasks from implementation plan."""
        phases = []
        
        # Find Implementation Plan section
        plan_match = re.search(
            r'## 📋 Implementation Plan\s*\n(.*?)(?=\n## |\Z)', 
            content, re.DOTALL
        )
        if not plan_match:
            return phases
        
        plan_content = plan_match.group(1)
        
        # Parse phases
        phase_pattern = r'### (Phase \d+:.*?)\(Estimated: ([^)]+)\)\s*\n(.*?)(?=### |$)'
        phase_matches = re.finditer(phase_pattern, plan_content, re.DOTALL)
        
        for phase_match in phase_matches:
            phase_name = phase_match.group(1).strip()
            estimated_time_str = phase_match.group(2).strip()
            phase_tasks_content = phase_match.group(3)
            
            # Parse estimated time
            estimated_time = self._parse_time_string(estimated_time_str)
            
            # Parse tasks within this phase
            tasks = self._parse_tasks(phase_tasks_content)
            
            phase = PhaseStatus(
                name=phase_name,
                estimated_time=estimated_time,
                tasks=tasks
            )
            
            # Calculate phase status based on task completion
            if all(task.status == "completed" for task in tasks):
                phase.status = "completed"
            elif any(task.status in ["in_progress", "completed"] for task in tasks):
                phase.status = "in_progress"
            else:
                phase.status = "pending"
            
            phases.append(phase)
        
        return phases
    
    def _parse_tasks(self, tasks_content: str) -> List[TaskStatus]:
        """Parse individual tasks from phase content."""
        tasks = []
        
        # Task pattern: - [x] **Task Name** (Est: time) - Description
        task_pattern = r'- \[([ x])\] \*\*(.*?)\*\* \(Est: ([^)]+)\) - (.*?)\n(?:\s*- Commit: `([^`]+)`\n)?(?:\s*- Status: ([^\n]+)\n)?'
        
        task_matches = re.finditer(task_pattern, tasks_content, re.DOTALL)
        
        for task_match in task_matches:
            completed = task_match.group(1) == 'x'
            task_name = task_match.group(2).strip()
            estimated_time_str = task_match.group(3).strip()
            description = task_match.group(4).strip()
            commit_hash = task_match.group(5) if task_match.group(5) else None
            status_text = task_match.group(6) if task_match.group(6) else None
            
            # Parse estimated time
            estimated_time = self._parse_time_string(estimated_time_str)
            
            # Determine status
            if completed:
                status = "completed"
            elif status_text and "in progress" in status_text.lower():
                status = "in_progress"
            else:
                status = "pending"
            
            # Clean up commit hash
            if commit_hash and commit_hash.startswith('<checksum>'):
                commit_hash = None
            
            task = TaskStatus(
                name=f"{task_name} - {description}",
                estimated_time=estimated_time,
                status=status,
                commit_hash=commit_hash
            )
            
            tasks.append(task)
        
        return tasks
    
    def _parse_time_string(self, time_str: str) -> Optional[int]:
        """Parse time string like '30 min', '2 hours', '1.5h' to minutes."""
        if not time_str:
            return None
        
        # Handle various time formats
        time_str = time_str.lower().strip()
        
        # Minutes
        min_match = re.search(r'(\d+(?:\.\d+)?)\s*min', time_str)
        if min_match:
            return int(float(min_match.group(1)))
        
        # Hours
        hour_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:h|hour)', time_str)
        if hour_match:
            return int(float(hour_match.group(1)) * 60)
        
        # Just a number (assume minutes)
        num_match = re.search(r'^(\d+(?:\.\d+)?)$', time_str)
        if num_match:
            return int(float(num_match.group(1)))
        
        return None
    
    def _parse_acceptance_criteria(self, content: str) -> List[Dict[str, Any]]:
        """Parse acceptance criteria section."""
        criteria = []
        
        criteria_match = re.search(
            r'## ✅ Acceptance Criteria\s*\n(.*?)(?=\n## |\Z)', 
            content, re.DOTALL
        )
        if not criteria_match:
            return criteria
        
        criteria_content = criteria_match.group(1)
        
        # Parse criteria items
        criteria_pattern = r'- \[([ x])\] (.*?)(?:\n|$)'
        for match in re.finditer(criteria_pattern, criteria_content):
            completed = match.group(1) == 'x'
            description = match.group(2).strip()
            
            criteria.append({
                'description': description,
                'completed': completed
            })
        
        return criteria
    
    def _extract_progress_info(self, content: str) -> Dict[str, Any]:
        """Extract progress tracking information."""
        progress_info = {}
        
        # Look for time invested
        time_match = re.search(r'Time Invested:\*\*\s*(\d+(?:\.\d+)?)h', content)
        if time_match:
            progress_info['time_invested'] = int(float(time_match.group(1)) * 60)
        
        return progress_info
    
    def _extract_blockers(self, content: str) -> List[str]:
        """Extract any blockers or issues mentioned in the plan."""
        blockers = []
        
        # Look for blockers in notes or implementation notes
        blocker_patterns = [
            r'(?:blocker|blocked|issue):\s*(.*?)(?:\n|$)',
            r'- ⚠️\s*(.*?)(?:\n|$)',
            r'- 🚫\s*(.*?)(?:\n|$)',
        ]
        
        for pattern in blocker_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                blocker = match.group(1).strip()
                if blocker and blocker not in blockers:
                    blockers.append(blocker)
        
        return blockers
    
    def _extract_notes(self, content: str) -> str:
        """Extract implementation notes."""
        notes_match = re.search(
            r'### Implementation Notes\s*\n(.*?)(?=\n### |\n## |\Z)', 
            content, re.DOTALL
        )
        if notes_match:
            return notes_match.group(1).strip()
        return ""
    
    def get_plan_status(self, plan_name: str) -> Optional[PlanStatus]:
        """Get comprehensive status for a specific plan."""
        return self.parse_plan_file(plan_name)
    
    def get_all_plans_status(self) -> List[PlanStatus]:
        """Get status for all discovered plans."""
        plans = self.discover_plans()
        statuses = []
        
        for plan_name in plans:
            status = self.get_plan_status(plan_name)
            if status:
                statuses.append(status)
        
        return statuses
    
    def generate_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report across all plans."""
        all_plans = self.get_all_plans_status()
        
        if not all_plans:
            return {
                'total_plans': 0,
                'summary': 'No plans found',
                'recommendations': ['Create a plan to get started']
            }
        
        # Calculate aggregate statistics
        total_plans = len(all_plans)
        completed_plans = sum(1 for plan in all_plans if plan.status == 'completed')
        in_progress_plans = sum(1 for plan in all_plans if plan.status == 'in_progress')
        
        total_estimated_time = sum(
            plan.estimated_duration or 0 for plan in all_plans
        )
        total_invested_time = sum(plan.time_invested for plan in all_plans)
        
        # Overall completion percentage
        if total_plans > 0:
            overall_completion = sum(
                plan.overall_completion_percentage for plan in all_plans
            ) / total_plans
        else:
            overall_completion = 0.0
        
        # Identify blockers and recommendations
        all_blockers = []
        for plan in all_plans:
            all_blockers.extend(plan.blockers)
        
        recommendations = self._generate_recommendations(all_plans)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_plans': total_plans,
            'completed_plans': completed_plans,
            'in_progress_plans': in_progress_plans,
            'overall_completion_percentage': round(overall_completion, 1),
            'total_estimated_time_hours': round(total_estimated_time / 60, 1),
            'total_invested_time_hours': round(total_invested_time / 60, 1),
            'active_blockers': len(all_blockers),
            'plans': [self._plan_to_dict_with_properties(plan) for plan in all_plans],
            'recommendations': recommendations,
            'plan_objects': all_plans  # Keep original objects for CLI access
        }
    
    def _generate_recommendations(self, plans: List[PlanStatus]) -> List[str]:
        """Generate actionable recommendations based on plan status."""
        recommendations = []
        
        if not plans:
            return ['Create your first plan to get started with the planning system']
        
        # Check for stalled plans
        stalled_plans = [
            plan for plan in plans 
            if plan.status == 'in_progress' and plan.overall_completion_percentage < 10
        ]
        if stalled_plans:
            recommendations.append(
                f"Review stalled plans: {', '.join(plan.plan_name for plan in stalled_plans[:3])}"
            )
        
        # Check for plans with blockers
        blocked_plans = [plan for plan in plans if plan.blockers]
        if blocked_plans:
            recommendations.append(
                f"Address blockers in: {', '.join(plan.plan_name for plan in blocked_plans[:3])}"
            )
        
        # Check for plans near completion
        near_completion = [
            plan for plan in plans 
            if 80 <= plan.overall_completion_percentage < 100
        ]
        if near_completion:
            recommendations.append(
                f"Push to completion: {', '.join(plan.plan_name for plan in near_completion[:3])}"
            )
        
        # Check for unstarted plans
        unstarted = [plan for plan in plans if plan.status == 'planning']
        if unstarted:
            recommendations.append(
                f"Consider starting: {', '.join(plan.plan_name for plan in unstarted[:3])}"
            )
        
        if not recommendations:
            recommendations.append("All plans are progressing well! Keep up the good work.")
        
        return recommendations
    
    def _plan_to_dict_with_properties(self, plan: PlanStatus) -> Dict[str, Any]:
        """Convert PlanStatus to dictionary including calculated properties."""
        plan_dict = asdict(plan)
        # Add calculated properties that aren't included by asdict()
        plan_dict['overall_completion_percentage'] = plan.overall_completion_percentage
        plan_dict['estimated_completion_time'] = plan.estimated_completion_time
        return plan_dict
    
    def save_status_json(self, plan_name: str, status: PlanStatus) -> None:
        """Save plan status to JSON file for caching and external access."""
        status_file = self.plans_directory / f"{plan_name}_status.json"
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(status), f, indent=2, default=str)
    
    def load_status_json(self, plan_name: str) -> Optional[PlanStatus]:
        """Load plan status from JSON file."""
        status_file = self.plans_directory / f"{plan_name}_status.json"
        
        if not status_file.exists():
            return None
        
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct objects from dict
            phases = []
            for phase_data in data.get('phases', []):
                tasks = [TaskStatus(**task_data) for task_data in phase_data.get('tasks', [])]
                phase = PhaseStatus(**{**phase_data, 'tasks': tasks})
                phases.append(phase)
            
            return PlanStatus(**{**data, 'phases': phases})
            
        except (json.JSONDecodeError, TypeError, KeyError):
            return None