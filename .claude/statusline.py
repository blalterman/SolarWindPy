#!/usr/bin/env python3
import json
import sys
import os
import subprocess
from pathlib import Path
import time

def get_model_name(data):
    """Extract model display name from JSON data."""
    return data.get('model', {}).get('display_name', 'Claude')

def get_current_dir(data):
    """Get basename of current directory."""
    current_dir = data.get('workspace', {}).get('current_dir', os.getcwd())
    return os.path.basename(current_dir)

def get_git_branch():
    """Get current git branch name."""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            return result.stdout.strip() or 'main'
        return ''
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ''

def get_conda_env():
    """Get current conda environment name."""
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', '')
    if conda_env and conda_env != 'base':
        return conda_env
    return ''

def estimate_token_usage(data):
    """Estimate token usage from transcript file."""
    try:
        transcript_path = data.get('transcript_path', '')
        if not transcript_path or not os.path.exists(transcript_path):
            return '0'
        
        # Rough estimate: ~4 chars per token
        file_size = os.path.getsize(transcript_path)
        estimated_tokens = file_size // 4
        
        if estimated_tokens > 1000000:
            return f"{estimated_tokens//1000000:.1f}M"
        elif estimated_tokens > 1000:
            return f"{estimated_tokens//1000:.0f}k"
        else:
            return str(estimated_tokens)
    except:
        return '0'

def get_compaction_indicator(data):
    """Estimate time until context compaction based on file size."""
    try:
        transcript_path = data.get('transcript_path', '')
        if not transcript_path or not os.path.exists(transcript_path):
            return '∞'
        
        file_size = os.path.getsize(transcript_path)
        # Rough estimate: compaction around 200k tokens (~800KB)
        compaction_threshold = 800 * 1024
        
        if file_size < compaction_threshold * 0.5:
            return '●●●'  # Far from compaction
        elif file_size < compaction_threshold * 0.8:
            return '●●○'  # Getting closer
        else:
            return '●○○'  # Near compaction
    except:
        return '?'

def get_usage_indicator():
    """Approximate usage indicator based on session duration."""
    try:
        # Check if there's a session start time file
        session_file = Path.home() / '.claude' / 'session_start'
        if session_file.exists():
            start_time = float(session_file.read_text().strip())
            elapsed_hours = (time.time() - start_time) / 3600
            
            if elapsed_hours < 1:
                return '█████'  # Fresh session
            elif elapsed_hours < 3:
                return '████○'  # Light usage
            elif elapsed_hours < 6:
                return '███○○'  # Medium usage
            elif elapsed_hours < 12:
                return '██○○○'  # Heavy usage
            else:
                return '█○○○○'  # Very heavy usage
        else:
            # Create session start file
            session_file.parent.mkdir(exist_ok=True)
            session_file.write_text(str(time.time()))
            return '█████'
    except:
        return '?????'

def create_status_line(data):
    """Create the formatted status line."""
    model = get_model_name(data)
    current_dir = get_current_dir(data)
    git_branch = get_git_branch()
    conda_env = get_conda_env()
    tokens = estimate_token_usage(data)
    compaction = get_compaction_indicator(data)
    usage = get_usage_indicator()
    
    # Build status line components
    parts = [f"[{model}]", f"📁 {current_dir}"]
    
    if conda_env:
        parts.append(f"🐍 {conda_env}")
        
    if git_branch:
        parts.append(f"🌿 {git_branch}")
    
    parts.extend([
        f"🔤 {tokens}",
        f"⏱️ {compaction}",
        f"📊 {usage}"
    ])
    
    return " | ".join(parts)

if __name__ == "__main__":
    try:
        # Read JSON from stdin
        data = json.load(sys.stdin)
        print(create_status_line(data))
    except Exception as e:
        # Fallback status line
        print(f"[Claude] 📁 {os.path.basename(os.getcwd())} | ❌ Error")