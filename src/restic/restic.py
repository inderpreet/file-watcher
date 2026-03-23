import subprocess
import os
from typing import List, Optional

from dotenv import load_dotenv
from src.logger import logger

# Load environment variables from .env file
load_dotenv()


class ResticError(Exception):
    pass


def _run_restic_command(command: List[str], password: Optional[str] = None, cwd: Optional[str] = None) -> str:
    """Helper to run restic commands with optional password."""
    env = os.environ.copy()
    if password:
        env['RESTIC_PASSWORD'] = password
    logger.debug("Running restic command: {}", command)
    try:
        result = subprocess.run(
            ['restic'] + command,
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error("Restic command failed: {}", e.stderr)
        raise ResticError(f"Restic command failed: {e.stderr}")


def init_repo(repo_path: str, password: Optional[str] = None) -> None:
    """Initialize a new restic repository."""
    logger.info("Initializing restic repository at {}", repo_path)
    _run_restic_command(['init', '--repo', repo_path], password)


def backup(repo_path: str, sources: List[str], password: Optional[str] = None,
           exclude: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> None:
    """Create a backup."""
    logger.info("Starting backup of {} to repo {}", sources, repo_path)
    command = ['backup', '--repo', repo_path]
    if exclude:
        for ex in exclude:
            command.extend(['--exclude', ex])
    if tags:
        for tag in tags:
            command.extend(['--tag', tag])
    command.extend(sources)
    _run_restic_command(command, password)


def backup_with_output(
    repo_path: str,
    sources: List[str],
    password: Optional[str] = None,
    exclude: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
) -> tuple[bool, str, str, int]:
    """
    Run restic backup and capture full output without raising on failure.

    Returns:
        (success, stdout, stderr, return_code)
    """
    logger.info("Starting backup of {} to repo {}", sources, repo_path)
    env = os.environ.copy()
    if password:
        env['RESTIC_PASSWORD'] = password
    command = ['backup', '--repo', repo_path]
    if exclude:
        for ex in exclude:
            command.extend(['--exclude', ex])
    if tags:
        for tag in tags:
            command.extend(['--tag', tag])
    command.extend(sources)
    logger.debug("Running restic command: {}", command)
    result = subprocess.run(
        ['restic'] + command,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    success = result.returncode == 0
    if not success:
        logger.error("Restic command failed: {}", result.stderr)
    return success, result.stdout or '', result.stderr or '', result.returncode


def list_snapshots(repo_path: str, password: Optional[str] = None) -> str:
    """List snapshots in the repository."""
    logger.debug("Listing snapshots in repo {}", repo_path)
    return _run_restic_command(['snapshots', '--repo', repo_path], password)


def restore(repo_path: str, snapshot_id: str, target: str, password: Optional[str] = None,
            include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> None:
    """Restore from a snapshot."""
    logger.info("Restoring snapshot {} to {}", snapshot_id, target)
    command = ['restore', snapshot_id, '--repo', repo_path, '--target', target]
    if include:
        for inc in include:
            command.extend(['--include', inc])
    if exclude:
        for ex in exclude:
            command.extend(['--exclude', ex])
    _run_restic_command(command, password)


def forget(repo_path: str, policy: dict, password: Optional[str] = None) -> None:
    """Forget snapshots according to policy."""
    logger.info("Forgetting snapshots in repo {} with policy {}", repo_path, policy)
    command = ['forget', '--repo', repo_path]
    if 'keep-daily' in policy:
        command.extend(['--keep-daily', str(policy['keep-daily'])])
    if 'keep-weekly' in policy:
        command.extend(['--keep-weekly', str(policy['keep-weekly'])])
    if 'keep-monthly' in policy:
        command.extend(['--keep-monthly', str(policy['keep-monthly'])])
    # Add more policy options as needed
    _run_restic_command(command, password)


def prune(repo_path: str, password: Optional[str] = None) -> None:
    """Prune the repository."""
    logger.info("Pruning repository {}", repo_path)
    _run_restic_command(['prune', '--repo', repo_path], password)


# Additional APIs can be added here
