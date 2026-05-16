#!/usr/bin/env python3
"""
Launcher for the CRM, Invoice System, and AI Agent.
Starts the web servers as background processes, then runs the AI Agent.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

# Subproject directories
CRM_DIR = BASE_DIR / "crm"
AI_DIR = BASE_DIR / "ai_agent"
INVOICE_DIR = BASE_DIR / "invoice_system"

# Server definitions: (directory, script, display name, URL)
SERVERS = [
    (CRM_DIR, "app.py", "CRM", "http://localhost:5000"),
    (INVOICE_DIR, "run.py", "Invoice System", "http://localhost:5001"),
]

# AI Agent command
AI_AGENT_CMD = [sys.executable, "-m", "ai_agent.main"]


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def _validate_directories() -> None:
    """Check that all required subproject directories exist."""
    missing = [str(d) for d in (CRM_DIR, AI_DIR, INVOICE_DIR) if not d.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required folders: {', '.join(missing)}")


def _build_environment() -> dict:
    """
    Build the environment dictionary for subprocesses.
    Adds the base directory to PYTHONPATH so that modules can be imported.
    """
    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH", "")
    new_pythonpath = str(BASE_DIR)
    if existing_pythonpath:
        new_pythonpath += os.pathsep + existing_pythonpath
    env["PYTHONPATH"] = new_pythonpath
    return env


def _start_server(work_dir: Path, script: str, name: str, url: str, env: dict) -> subprocess.Popen:
    """
    Start a web server as a background process.

    Returns:
        subprocess.Popen: The process handle.
    """
    print(f"Starting {name}...")
    process = subprocess.Popen(
        [sys.executable, script],
        cwd=str(work_dir),
        env=env
    )
    print(f"{name} started in background on {url}")
    return process


def _stop_process(process: Optional[subprocess.Popen]) -> None:
    """
    Gracefully terminate a subprocess.
    Sends SIGTERM, waits up to 5 seconds, then kills if still alive.
    """
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def _stop_all_servers(processes: List[Optional[subprocess.Popen]]) -> None:
    """Stop all given server processes."""
    for proc in processes:
        _stop_process(proc)
    print("All servers stopped.")


# -----------------------------------------------------------------------------
# Main orchestration
# -----------------------------------------------------------------------------

def run_all() -> None:
    """Launch all servers, run the AI Agent, then shut down gracefully."""
    print("=" * 60)
    print("Starting CRM, Invoice System, and AI Agent")
    print("=" * 60)

    # Pre-flight checks
    _validate_directories()
    env = _build_environment()

    # Start all web servers
    server_processes = []
    for work_dir, script, name, url in SERVERS:
        proc = _start_server(work_dir, script, name, url, env)
        server_processes.append(proc)

    try:
        # Run the AI Agent (blocks until it finishes)
        print("\nStarting AI Agent...")
        subprocess.run(AI_AGENT_CMD, cwd=str(BASE_DIR), env=env, check=False)

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user. Shutting down...")
    finally:
        _stop_all_servers(server_processes)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        run_all()
    except KeyboardInterrupt:
        # This handles Ctrl+C while the launcher is still setting up
        print("\nApplication terminated by user.")
    except FileNotFoundError as e:
        print(f"\n❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)