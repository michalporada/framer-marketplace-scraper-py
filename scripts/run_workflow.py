#!/usr/bin/env python3
"""Script to manually trigger GitHub Actions workflow."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import subprocess
import asyncio


def get_repo_info():
    """Get repository owner and name from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        url = result.stdout.strip()
        if "github.com" in url:
            if url.startswith("https://"):
                repo_path = url.replace("https://github.com/", "").replace(".git", "")
            elif url.startswith("git@"):
                repo_path = url.replace("git@github.com:", "").replace(".git", "")
            else:
                return None, None

            parts = repo_path.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
    except Exception:
        pass
    return None, None


async def run_workflow(owner, repo, workflow_file, token):
    """Run GitHub Actions workflow."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    # Get workflow ID
    workflows_url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows"
    async with httpx.AsyncClient() as client:
        response = await client.get(workflows_url, headers=headers)
        if response.status_code != 200:
            print(f"Error: Failed to fetch workflows (status {response.status_code})")
            if response.status_code == 401:
                print("Hint: You may need to set GITHUB_TOKEN environment variable")
            return False

        workflows = response.json().get("workflows", [])
        workflow = [
            w for w in workflows if w.get("path") == workflow_file or workflow_file in w.get("name", "").lower()
        ]

        if not workflow:
            print(f"Error: Workflow '{workflow_file}' not found")
            return False

        workflow_id = workflow[0]["id"]
        workflow_name = workflow[0]["name"]

        print(f"Found workflow: {workflow_name} (ID: {workflow_id})")

        # Run workflow
        run_url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        run_response = await client.post(
            run_url, headers=headers, json={"ref": "main"}
        )

        if run_response.status_code == 204:
            print(f"✓ Workflow '{workflow_name}' triggered successfully!")
            print(f"\nView run: https://github.com/{owner}/{repo}/actions")
            return True
        else:
            print(f"Error: Failed to trigger workflow (status {run_response.status_code})")
            print(f"Response: {run_response.text}")
            return False


async def main():
    """Main function."""
    owner, repo = get_repo_info()
    if not owner or not repo:
        print("Error: Could not determine repository from git remote")
        sys.exit(1)

    print(f"Repository: {owner}/{repo}")

    # Get workflow file from args or use default
    workflow_file = sys.argv[1] if len(sys.argv) > 1 else ".github/workflows/scrape.yml"

    # Get GitHub token from environment
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("\n⚠️  GITHUB_TOKEN not set")
        print("To trigger workflow via API, you need a GitHub Personal Access Token")
        print("Set it as: export GITHUB_TOKEN=your_token")
        print("\nAlternatively, run workflow manually on GitHub:")
        print(f"  https://github.com/{owner}/{repo}/actions/workflows/scrape.yml")
        print("  → Click 'Run workflow' → 'Run workflow'")
        sys.exit(1)

    success = await run_workflow(owner, repo, workflow_file, token)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

