"""Configuration settings for conda feedstock automation.

This module contains all configuration constants and settings
used by the conda feedstock update automation scripts.
"""

from typing import Dict, Any

# Timeout settings (in seconds)
TIMEOUTS = {
    'pypi_check': 10,           # PyPI API request timeout
    'download': 60,             # Package download timeout
    'github_api': 15,           # GitHub API request timeout
    'pypi_availability': 300,   # Wait for PyPI availability (5 minutes)
}

# Retry configuration
RETRY_CONFIG = {
    'max_attempts': 3,          # Maximum retry attempts
    'backoff_factor': 1.5,      # Exponential backoff multiplier
    'base_delay': 1,            # Base delay in seconds
    'max_delay': 60,            # Maximum delay between retries
}

# PyPI configuration
PYPI_CONFIG = {
    'base_url': 'https://pypi.org',
    'api_timeout': TIMEOUTS['pypi_check'],
    'source_url_template': 'https://pypi.org/packages/source/{first_letter}/{package}/{package}-{version}.tar.gz',
    'json_api_template': 'https://pypi.org/pypi/{package}/{version}/json',
    'package_info_template': 'https://pypi.org/pypi/{package}/json',
}

# GitHub configuration
GITHUB_CONFIG = {
    'api_base': 'https://api.github.com',
    'timeout': TIMEOUTS['github_api'],
    'feedstock_template': 'conda-forge/{package}-feedstock',
    'issue_labels': ['conda-feedstock', 'automation'],
    'pr_labels': ['automated-update'],
}

# conda-forge specific settings
CONDA_FORGE_CONFIG = {
    'feedstock_suffix': '-feedstock',
    'recipe_path': 'recipe/meta.yaml',
    'org_name': 'conda-forge',
    'bot_name': 'conda-forge-admin',
    'review_team': 'conda-forge/core',
}

# Package-specific settings
PACKAGE_CONFIG = {
    'solarwindpy': {
        'name': 'solarwindpy',
        'homepage': 'https://github.com/blalterman/SolarWindPy',
        'license': 'BSD-3-Clause',
        'license_file': 'LICENSE.rst',
        'summary': 'Python package for solar wind data analysis.',
        'maintainers': ['blalterman'],
        'min_python': '3.11',
    }
}

# Automation settings
AUTOMATION_CONFIG = {
    'enabled_for_prereleases': False,   # Skip RC, alpha, beta versions
    'create_tracking_issues': True,     # Create GitHub issues for tracking
    'auto_create_pr': False,           # Currently manual PR creation
    'update_dependencies': False,       # Currently keep dependencies static
    'dry_run_default': False,          # Default dry run setting
}

# Validation settings
VALIDATION_CONFIG = {
    'require_pypi_availability': True,  # Must confirm PyPI availability
    'validate_version_format': True,    # Validate semantic versioning
    'check_existing_version': True,     # Check if version already exists in feedstock
    'verify_sha256': True,              # Always verify SHA256 hashes
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'show_progress': True,              # Show progress indicators
    'use_emoji': True,                  # Use emoji in output
}

# File paths (relative to project root)
PATHS = {
    'project_root': '.',
    'scripts_dir': 'scripts',
    'temp_dir': '/tmp/conda-feedstock-automation',
    'log_file': 'logs/conda-automation.log',
}

# Command templates
COMMANDS = {
    'gh_fork': ['gh', 'repo', 'fork', '{repo}', '--clone'],
    'gh_create_issue': ['gh', 'issue', 'create', '--title', '{title}', '--body', '{body}', '--label', '{labels}'],
    'gh_create_pr': ['gh', 'pr', 'create', '--title', '{title}', '--body', '{body}', '--label', '{labels}'],
    'git_checkout': ['git', 'checkout', '-b', '{branch}'],
    'git_add': ['git', 'add', '{files}'],
    'git_commit': ['git', 'commit', '-m', '{message}'],
    'git_push': ['git', 'push', 'origin', '{branch}'],
}


def get_package_config(package_name: str) -> Dict[str, Any]:
    """Get configuration for a specific package.
    
    Parameters
    ----------
    package_name : str
        Name of the package
        
    Returns
    -------
    dict
        Package configuration dictionary
    """
    return PACKAGE_CONFIG.get(package_name, {
        'name': package_name,
        'homepage': f'https://pypi.org/project/{package_name}/',
        'license': 'Unknown',
        'summary': f'{package_name} conda package',
        'maintainers': [],
    })


def get_feedstock_repo(package_name: str) -> str:
    """Get the conda-forge feedstock repository name.
    
    Parameters
    ----------
    package_name : str
        Name of the package
        
    Returns
    -------
    str
        Full feedstock repository name (org/repo)
    """
    return GITHUB_CONFIG['feedstock_template'].format(package=package_name)


def get_pypi_source_url(package_name: str, version: str) -> str:
    """Get the PyPI source distribution URL.
    
    Parameters
    ----------
    package_name : str
        Name of the package
    version : str
        Version string
        
    Returns
    -------
    str
        PyPI source distribution URL
    """
    return PYPI_CONFIG['source_url_template'].format(
        first_letter=package_name[0].lower(),
        package=package_name,
        version=version
    )


def get_pypi_json_url(package_name: str, version: str = None) -> str:
    """Get the PyPI JSON API URL.
    
    Parameters
    ----------
    package_name : str
        Name of the package
    version : str, optional
        Specific version, if None gets latest info
        
    Returns
    -------
    str
        PyPI JSON API URL
    """
    if version:
        return PYPI_CONFIG['json_api_template'].format(
            package=package_name, version=version
        )
    else:
        return PYPI_CONFIG['package_info_template'].format(
            package=package_name
        )


def is_automation_enabled() -> bool:
    """Check if automation is enabled.
    
    Returns
    -------
    bool
        True if automation is enabled
    """
    return AUTOMATION_CONFIG.get('enabled', True)


def should_skip_prereleases() -> bool:
    """Check if pre-releases should be skipped.
    
    Returns
    -------
    bool
        True if pre-releases should be skipped
    """
    return not AUTOMATION_CONFIG['enabled_for_prereleases']


# Environment-specific overrides
def load_env_config():
    """Load configuration overrides from environment variables.
    
    Environment variables can override default settings:
    - CONDA_AUTOMATION_TIMEOUT: Override default timeouts
    - CONDA_AUTOMATION_DRY_RUN: Set default dry run mode
    - CONDA_AUTOMATION_GITHUB_TOKEN: GitHub API token
    - CONDA_AUTOMATION_DEBUG: Enable debug logging
    """
    import os
    
    # Override timeout if specified
    if 'CONDA_AUTOMATION_TIMEOUT' in os.environ:
        try:
            timeout = int(os.environ['CONDA_AUTOMATION_TIMEOUT'])
            TIMEOUTS['pypi_check'] = timeout
            TIMEOUTS['github_api'] = timeout
            GITHUB_CONFIG['timeout'] = timeout
        except ValueError:
            pass
    
    # Override dry run default
    if 'CONDA_AUTOMATION_DRY_RUN' in os.environ:
        AUTOMATION_CONFIG['dry_run_default'] = (
            os.environ['CONDA_AUTOMATION_DRY_RUN'].lower() in ('true', '1', 'yes')
        )
    
    # Enable debug logging
    if 'CONDA_AUTOMATION_DEBUG' in os.environ:
        LOGGING_CONFIG['level'] = 'DEBUG'


# Load environment overrides on import
load_env_config()
