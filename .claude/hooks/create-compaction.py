#!/usr/bin/env python3
"""Compaction Creation Hook for SolarWindPy Creates structured compaction preserving
plan state at token boundaries.

Enhanced with intelligent token estimation and content-aware compression.
"""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def get_git_info():
    """Get current git branch and recent commits."""
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip()

        # Get recent commits
        commits = subprocess.check_output(
            ["git", "log", "--oneline", "-5"], text=True
        ).strip()

        # Get current status
        status = subprocess.check_output(
            ["git", "status", "--short"], text=True
        ).strip()

        return branch, commits, status
    except subprocess.CalledProcessError:
        return "unknown", "", ""


def create_compaction_filename(branch, timestamp, tokens, target_tokens):
    """Create a unique filename for this compaction milestone."""
    try:
        # Create a meaningful filename
        date_part = timestamp.split("T")[0]  # Just the date part
        time_part = timestamp.split("T")[1][:8].replace(":", "")  # HHMMSS format
        compression_pct = int((1 - target_tokens / tokens) * 100) if tokens > 0 else 0
        filename = f"compaction-{date_part}-{time_part}-{compression_pct}pct.md"

        return filename

    except Exception:
        # Fallback to simple timestamp
        return f"compaction-{timestamp.replace(':', '').replace('-', '')}.md"


def get_enhanced_git_info():
    """Get enhanced git information including diff stats and recent activity."""
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip()

        # Get recent commits with more details
        commits = subprocess.check_output(
            ["git", "log", "--oneline", "--decorate", "-5"], text=True
        ).strip()

        # Get current status
        status = subprocess.check_output(
            ["git", "status", "--short"], text=True
        ).strip()

        # Get diff stats for uncommitted changes
        diff_stats = ""
        try:
            diff_output = subprocess.check_output(
                ["git", "diff", "--stat"], text=True
            ).strip()
            if diff_output:
                diff_stats = diff_output
        except subprocess.CalledProcessError:
            pass

        # Get last commit info
        last_commit_info = ""
        try:
            last_commit_info = subprocess.check_output(
                ["git", "log", "-1", "--pretty=format:%h - %s (%an, %ar)"], text=True
            ).strip()
        except subprocess.CalledProcessError:
            pass

        return {
            "branch": branch,
            "commits": commits,
            "status": status,
            "diff_stats": diff_stats,
            "last_commit": last_commit_info,
        }

    except subprocess.CalledProcessError:
        return {
            "branch": "unknown",
            "commits": "",
            "status": "",
            "diff_stats": "",
            "last_commit": "",
        }


def analyze_file_content(file_path):
    """Analyze file content and return detailed metrics."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Basic metrics
        chars = len(content)
        words = len(content.split())
        lines = len(content.splitlines())

        # Content type analysis
        content_breakdown = {
            "code": 0,
            "prose": 0,
            "tables": 0,
            "lists": 0,
            "headers": 0,
        }

        # Analyze content by line
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            # Code patterns (indented, contains brackets/semicolons)
            if (
                line.startswith("    ")
                or line.startswith("\t")
                or any(char in line for char in "{}();[]")
                or line.startswith("def ")
                or line.startswith("class ")
                or line.startswith("import ")
                or line.startswith("from ")
            ):
                content_breakdown["code"] += 1
            # Table patterns (contains |)
            elif "|" in line and line.count("|") >= 2:
                content_breakdown["tables"] += 1
            # List patterns (starts with -, *, number.)
            elif re.match(r"^[-*]\s+", line) or re.match(r"^\d+\.\s+", line):
                content_breakdown["lists"] += 1
            # Header patterns (starts with #)
            elif line.startswith("#"):
                content_breakdown["headers"] += 1
            # Everything else is prose
            else:
                content_breakdown["prose"] += 1

        return chars, words, lines, content_breakdown

    except Exception:
        return 0, 0, 0, {"code": 0, "prose": 0, "tables": 0, "lists": 0, "headers": 0}


def estimate_context_size_enhanced():
    """Enhanced token estimation using character/word-based heuristics."""

    context_files = ["CLAUDE.md", "claude_session_state.md", ".claude/agents/*.md"]

    total_chars = 0
    total_words = 0
    total_lines = 0
    content_breakdown = {"code": 0, "prose": 0, "tables": 0, "lists": 0, "headers": 0}

    # Collect all files to analyze
    files_to_analyze = []
    for pattern in context_files:
        if "*" in pattern:
            # Handle glob patterns
            directory = Path(pattern).parent
            file_pattern = Path(pattern).name
            try:
                for file_path in directory.glob(file_pattern):
                    if file_path.is_file():
                        files_to_analyze.append(file_path)
            except Exception:
                pass
        else:
            if Path(pattern).exists():
                files_to_analyze.append(Path(pattern))

    # Analyze each file
    for file_path in files_to_analyze:
        chars, words, lines, breakdown = analyze_file_content(file_path)
        total_chars += chars
        total_words += words
        total_lines += lines
        for content_type, count in breakdown.items():
            content_breakdown[content_type] += count

    # Multi-heuristic token estimation
    estimates = {
        "line_based": total_lines * 3,  # Original method
        "char_based": total_chars // 4,  # ~4 chars per token
        "word_based": int(total_words * 1.33),  # ~0.75 words per token
    }

    # Content-type weighted estimation
    type_weights = {
        "code": 3.5,  # Code is more token-dense
        "prose": 2.8,  # Regular prose
        "tables": 3.2,  # Tables have formatting overhead
        "lists": 2.5,  # Lists are typically shorter
        "headers": 2.0,  # Headers are usually brief
    }

    weighted_tokens = sum(
        content_breakdown[content_type] * type_weights[content_type]
        for content_type in content_breakdown
    )

    estimates["content_weighted"] = int(weighted_tokens)

    # Take average of all estimates for final result
    final_estimate = int(sum(estimates.values()) / len(estimates))

    # Metadata for debugging and improvement
    estimation_metadata = {
        "estimates": estimates,
        "content_breakdown": content_breakdown,
        "total_files": len(files_to_analyze),
        "final_estimate": final_estimate,
    }

    return final_estimate, total_lines, estimation_metadata


def estimate_context_size():
    """Estimate current context token usage (backward compatibility wrapper)."""
    tokens, lines, metadata = estimate_context_size_enhanced()
    return tokens, lines


def find_active_plan():
    """Find the currently active plan directory."""
    branch, _, _ = get_git_info()

    if branch.startswith("plan/"):
        plan_name = branch[5:]  # Remove 'plan/' prefix
        plan_dir = Path(f"plans/{plan_name}")
        if plan_dir.exists():
            return plan_name, plan_dir

    # Fallback: look for most recent plan
    plans_dir = Path("plans")
    if plans_dir.exists():
        for item in plans_dir.iterdir():
            if item.is_dir() and item.name != "completed":
                return item.name, item

    return None, None


def extract_critical_context(plan_dir, plan_name):
    """Extract and prioritize critical context from plan files."""
    critical_content = {
        "active_tasks": [],
        "recent_decisions": [],
        "blockers": [],
        "next_steps": [],
        "key_accomplishments": [],
    }

    if not plan_dir or not plan_dir.exists():
        return critical_content

    # Analyze overview file for current status
    overview_file = plan_dir / "0-Overview.md"
    if overview_file.exists():
        try:
            with open(overview_file, "r") as f:
                content = f.read()

            # Extract incomplete tasks (marked with [ ])
            incomplete_tasks = re.findall(r"- \[ \] (.+)", content)
            critical_content["active_tasks"] = incomplete_tasks[:5]  # Top 5 priorities

            # Extract recent updates from bottom of file
            lines = content.splitlines()
            for i, line in enumerate(reversed(lines[:50])):  # Check last 50 lines
                if "Implementation Notes" in line or "Progress" in line:
                    recent_notes = lines[-(i + 10) :] if i < 40 else lines[-i:]
                    critical_content["recent_decisions"] = [
                        line.strip()
                        for line in recent_notes
                        if line.strip() and not line.startswith("#")
                    ][:3]
                    break

        except Exception:
            pass

    # Look for phase files with recent activity
    phase_files = list(plan_dir.glob("[0-9]-*.md"))
    phase_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    for phase_file in phase_files[:2]:  # Check 2 most recent
        try:
            with open(phase_file, "r") as f:
                content = f.read()

            # Look for blockers or issues
            if "blocker" in content.lower() or "issue" in content.lower():
                lines = content.splitlines()
                for line in lines:
                    if any(
                        word in line.lower() for word in ["blocker", "issue", "problem"]
                    ):
                        critical_content["blockers"].append(line.strip())

            # Look for next steps
            if "next" in content.lower() or "todo" in content.lower():
                lines = content.splitlines()
                for line in lines:
                    if any(
                        word in line.lower() for word in ["next", "todo", "remaining"]
                    ):
                        critical_content["next_steps"].append(line.strip())

        except Exception:
            continue

    return critical_content


def compress_git_history(commits, status, compression_level="medium"):
    """Intelligently compress git history based on importance."""
    if compression_level == "light":
        return commits, status

    commit_lines = commits.splitlines() if commits else []

    if compression_level == "high":
        # Keep only the most recent commit and any merge commits
        important_commits = []
        for line in commit_lines[:3]:  # Max 3 commits
            if "merge" in line.lower() or len(important_commits) == 0:
                important_commits.append(line)
        compressed_commits = "\n".join(important_commits)
    else:  # medium
        # Keep recent commits but summarize older ones
        compressed_commits = "\n".join(commit_lines[:5])  # Keep top 5

    # Compress status if many files
    if status:
        status_lines = status.splitlines()
        if len(status_lines) > 10:
            status = (
                "\n".join(status_lines[:8])
                + f"\n... and {len(status_lines) - 8} more files"
            )

    return compressed_commits, status


def generate_compression_strategy(tokens, content_breakdown):
    """Determine optimal compression strategy based on content analysis."""

    # Base compression level on token count
    if tokens > 15000:
        base_level = "high"
        target_reduction = 0.5  # 50% reduction
    elif tokens > 8000:
        base_level = "medium"
        target_reduction = 0.35  # 35% reduction
    else:
        base_level = "light"
        target_reduction = 0.2  # 20% reduction

    # Adjust based on content type distribution
    total_content = sum(content_breakdown.values())
    if total_content > 0:
        code_ratio = content_breakdown.get("code", 0) / total_content
        prose_ratio = content_breakdown.get("prose", 0) / total_content

        # Code-heavy content can be compressed more aggressively
        if code_ratio > 0.4:
            target_reduction += 0.1
        # Prose-heavy content should be compressed more carefully
        elif prose_ratio > 0.6:
            target_reduction -= 0.1

    # Ensure target stays within reasonable bounds
    target_reduction = max(0.1, min(0.7, target_reduction))

    return {
        "level": base_level,
        "target_reduction": target_reduction,
        "preserve_code": code_ratio > 0.3 if total_content > 0 else False,
        "preserve_decisions": True,  # Always preserve key decisions
        "compress_git": base_level in ["medium", "high"],
    }


def create_compaction():
    """Create a compacted state file for the current session."""

    print("🗜️  Creating intelligent compaction at token boundary...")

    # Get current state with enhanced analysis
    git_info = get_enhanced_git_info()
    branch, commits, status = (
        git_info["branch"],
        git_info["commits"],
        git_info["status"],
    )
    tokens, lines, estimation_metadata = estimate_context_size_enhanced()
    plan_name, plan_dir = find_active_plan()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Generate intelligent compression strategy
    content_breakdown = estimation_metadata["content_breakdown"]
    compression_strategy = generate_compression_strategy(tokens, content_breakdown)

    # Extract critical context from plan
    critical_context = extract_critical_context(plan_dir, plan_name)

    # Compress git history based on strategy
    if compression_strategy["compress_git"]:
        commits, status = compress_git_history(
            commits, status, compression_strategy["level"]
        )

    # Calculate target tokens based on strategy
    target_tokens = int(tokens * (1 - compression_strategy["target_reduction"]))
    target_description = f"{compression_strategy['level']} ({compression_strategy['target_reduction']*100:.0f}% reduction)"

    compaction_content = f"""# Compacted Context State - {timestamp}

## Compaction Metadata
- **Timestamp**: {timestamp}
- **Branch**: {branch}
- **Plan**: {plan_name or 'No active plan'}
- **Pre-Compaction Context**: ~{tokens:,} tokens ({lines:,} lines)
- **Target Compression**: {target_description}
- **Target Tokens**: ~{target_tokens:,} tokens
- **Strategy**: {compression_strategy['level']} compression with {'code' if compression_strategy['preserve_code'] else 'prose'} focus

## Content Analysis
- **Files Analyzed**: {estimation_metadata['total_files']}
- **Content Breakdown**:
  - Code: {content_breakdown.get('code', 0)} lines
  - Prose: {content_breakdown.get('prose', 0)} lines
  - Tables: {content_breakdown.get('tables', 0)} lines
  - Lists: {content_breakdown.get('lists', 0)} lines
  - Headers: {content_breakdown.get('headers', 0)} lines
- **Token Estimates**:
  - Line-based: {estimation_metadata['estimates']['line_based']:,}
  - Character-based: {estimation_metadata['estimates']['char_based']:,}
  - Word-based: {estimation_metadata['estimates']['word_based']:,}
  - Content-weighted: {estimation_metadata['estimates']['content_weighted']:,}
  - **Final estimate**: {tokens:,} tokens

## Git State
### Current Branch: {branch}
### Last Commit: {git_info['last_commit'] if git_info['last_commit'] else 'No commit info available'}

### Recent Commits:
```
{commits}
```

### Working Directory Status:
```
{status if status else 'Clean working directory'}
```

### Uncommitted Changes Summary:
```
{git_info['diff_stats'] if git_info['diff_stats'] else 'No uncommitted changes'}
```

## Critical Context Summary

### Active Tasks (Priority Focus)
{chr(10).join(f"- {task}" for task in critical_context['active_tasks'][:5]) if critical_context['active_tasks'] else "- No active tasks identified"}

### Recent Key Decisions
{chr(10).join(f"- {decision}" for decision in critical_context['recent_decisions'][:3]) if critical_context['recent_decisions'] else "- No recent decisions captured"}

### Blockers & Issues
{chr(10).join(f"⚠️ {blocker}" for blocker in critical_context['blockers'][:3]) if critical_context['blockers'] else "✅ No blockers identified"}

### Immediate Next Steps
{chr(10).join(f"➡️ {step}" for step in critical_context['next_steps'][:3]) if critical_context['next_steps'] else "- Next steps to be determined"}

## Session Context Summary
"""

    # Add plan-specific context if available
    if plan_dir and plan_dir.exists():
        overview_file = plan_dir / "0-Overview.md"
        if overview_file.exists():
            try:
                with open(overview_file, "r") as f:
                    overview_content = f.read()

                # Extract key metadata
                if "## Plan Metadata" in overview_content:
                    metadata_start = overview_content.find("## Plan Metadata")
                    metadata_end = overview_content.find("\n## ", metadata_start + 1)
                    if metadata_end == -1:
                        metadata_end = len(overview_content)
                    metadata_section = overview_content[metadata_start:metadata_end]

                    compaction_content += f"""
### Active Plan: {plan_name}
{metadata_section}

### Plan Progress Summary
- Plan directory: {plan_dir}
- Last modified: {datetime.fromtimestamp(overview_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}
"""
            except Exception as e:
                compaction_content += (
                    f"\\n### Plan Status: Could not read overview ({e})"
                )

    # Generate intelligent session resumption instructions
    quick_commands = []
    priority_actions = []

    # Generate branch-specific commands
    if branch != "master":
        quick_commands.append(f"git checkout {branch}")

    # Generate plan-specific commands
    if plan_name and plan_dir:
        quick_commands.append(f"cd {plan_dir} && ls -la")
        priority_actions.append(f"Review plan status: cat {plan_dir}/0-Overview.md")

    # Generate task-specific actions based on critical context
    if critical_context["active_tasks"]:
        priority_actions.extend(
            [f"Continue: {task}" for task in critical_context["active_tasks"][:2]]
        )

    if critical_context["blockers"]:
        priority_actions.extend(
            [f"Resolve: {blocker}" for blocker in critical_context["blockers"][:2]]
        )

    # Add git status command if there are uncommitted changes
    if status:
        quick_commands.append("git status")
        priority_actions.append(
            "Review uncommitted changes and decide on commit strategy"
        )

    # Add environment restoration commands
    quick_commands.extend(
        [
            "pwd  # Verify working directory",
            "conda info --envs  # Check active environment",
        ]
    )

    # Add session resumption instructions
    compaction_content += f"""
## Session Resumption Instructions

### 🚀 Quick Start Commands
```bash
# Restore session environment
{chr(10).join(quick_commands)}
```

### 🎯 Priority Actions for Next Session
{chr(10).join(f"{i+1}. {action}" for i, action in enumerate(priority_actions[:5])) if priority_actions else "1. Review compacted state and determine next steps"}

### 🔄 Session Continuity Checklist
- [ ] **Environment**: Verify correct conda environment and working directory
- [ ] **Branch**: Confirm on correct git branch ({branch})
- [ ] **Context**: Review critical context summary above
- [ ] **Plan**: {"Check plan status in " + str(plan_dir) if plan_dir else "Identify or create active plan"}
- [ ] **Changes**: {"Review uncommitted changes" if status else "No uncommitted changes to review"}

### 📊 Efficiency Metrics
- **Context Reduction**: {((tokens - target_tokens) / tokens * 100):.1f}% ({tokens:,} → {target_tokens:,} tokens)
- **Estimated Session Extension**: {int(((tokens - target_tokens) / tokens) * 60)} additional minutes of productive work
- **Compaction Strategy**: {compression_strategy['level']} compression focused on {'code' if compression_strategy['preserve_code'] else 'prose'} optimization

---
*Automated intelligent compaction - {timestamp}*
"""

    # Create unique filename for this compaction milestone
    compaction_filename = create_compaction_filename(
        branch, timestamp, tokens, target_tokens
    )
    compaction_content += f"""
## Compaction File
Filename: `{compaction_filename}` - Unique timestamp-based compaction file
No git tags created - using file-based state preservation
"""

    # Write compaction files
    compaction_file = Path(".claude/compacted_state.md")
    with open(compaction_file, "w") as f:
        f.write(compaction_content)

    # Also save with unique timestamp filename in .claude directory
    unique_compaction = Path(".claude") / compaction_filename
    with open(unique_compaction, "w") as f:
        f.write(compaction_content)

    # Also write to plan directory if available
    if plan_dir:
        plan_compaction = plan_dir / "compacted_state.md"
        with open(plan_compaction, "w") as f:
            f.write(compaction_content)
        print(f"✅ Compaction saved to: {plan_compaction}")

    print(f"✅ Compaction created: {compaction_file}")
    print(f"✅ Timestamped compaction: {unique_compaction}")
    print(
        f"📊 Token reduction: {tokens:,} → {target_tokens:,} ({((tokens - target_tokens) / tokens * 100):.1f}% savings)"
    )


def main():
    """Main entry point for compaction hook."""

    # Check if we're in a git repository
    if not Path(".git").exists():
        print("⚠️  Not in a git repository, skipping compaction")
        return

    print("🔍 Compaction hook triggered")
    create_compaction()


if __name__ == "__main__":
    main()
