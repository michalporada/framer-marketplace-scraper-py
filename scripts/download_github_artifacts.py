#!/usr/bin/env python3
"""Download artifacts from latest GitHub Actions workflow run."""

import sys
from pathlib import Path
import subprocess
import httpx
import zipfile
import tempfile
import shutil
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


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
            # Extract owner/repo from URL
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


async def download_artifact(owner, repo, artifact_id, artifact_name, token=None):
    """Download artifact from GitHub Actions."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip"

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    print(f"Downloading artifact '{artifact_name}'...")
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, follow_redirects=True)

    if response.status_code != 200:
        print(f"Error: Failed to download artifact (status {response.status_code})")
        if response.status_code == 401:
            print("Hint: You may need to set GITHUB_TOKEN environment variable")
        return False

    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
        tmp_file.write(response.content)
        tmp_path = tmp_file.name

    # Extract to current directory
    print(f"Extracting artifact to data/ directory...")
    with zipfile.ZipFile(tmp_path, "r") as zip_ref:
        # Extract only data/ directory
        for member in zip_ref.namelist():
            if member.startswith("data/") and not member.endswith("/"):
                zip_ref.extract(member, ".")
            elif member.startswith("data/"):
                # Create directories
                Path(member).mkdir(parents=True, exist_ok=True)

    # Clean up
    Path(tmp_path).unlink()
    print("✓ Artifact downloaded and extracted")
    return True


async def main():
    """Main function."""
    owner, repo = get_repo_info()
    if not owner or not repo:
        print("Error: Could not determine repository from git remote")
        print("Make sure you're in a git repository with a GitHub remote")
        sys.exit(1)

    print(f"Repository: {owner}/{repo}")

    # Get GitHub token from environment
    token = os.environ.get("GITHUB_TOKEN")

    # Get latest workflow runs
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    print("Fetching latest workflow runs...")
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params={"per_page": 10})

    if response.status_code != 200:
        print(f"Error: Failed to fetch runs (status {response.status_code})")
        if response.status_code == 401:
            print("Hint: You may need to set GITHUB_TOKEN environment variable")
            print("      For public repos, you can use the API without auth")
        sys.exit(1)

    runs = response.json().get("workflow_runs", [])
    if not runs:
        print("No workflow runs found")
        sys.exit(1)

    # Find scrape workflow runs
    scrape_runs = [r for r in runs if "scrape" in r.get("name", "").lower()]
    if not scrape_runs:
        print("No scrape workflow runs found")
        sys.exit(1)

    latest_run = scrape_runs[0]
    run_id = latest_run["id"]
    status = latest_run["status"]
    conclusion = latest_run.get("conclusion", "unknown")
    created_at = latest_run["created_at"]

    print(f"\nLatest scrape run:")
    print(f"  ID: {run_id}")
    print(f"  Status: {status}")
    print(f"  Conclusion: {conclusion}")
    print(f"  Created: {created_at}")

    # Get artifacts for this run
    artifacts_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
    async with httpx.AsyncClient() as client:
        artifacts_resp = await client.get(artifacts_url, headers=headers)

    if artifacts_resp.status_code != 200:
        print(f"Error: Failed to fetch artifacts (status {artifacts_resp.status_code})")
        sys.exit(1)

    artifacts = artifacts_resp.json().get("artifacts", [])
    if not artifacts:
        print("No artifacts found for this run")
        sys.exit(1)

    print(f"\nFound {len(artifacts)} artifact(s):")
    for art in artifacts:
        print(f"  - {art['name']} ({art['size_in_bytes']} bytes)")

    # Download scraped-data artifact
    scraped_data = [a for a in artifacts if a["name"] == "scraped-data"]
    if scraped_data:
        success = await download_artifact(
            owner, repo, scraped_data[0]["id"], scraped_data[0]["name"], token
        )
        if success:
            print("\n✓ Latest data downloaded from GitHub Actions")
            # Count products
            data_dir = Path("data/products")
            if data_dir.exists():
                total = sum(1 for _ in data_dir.rglob("*.json"))
                print(f"  Total products: {total}")
        else:
            sys.exit(1)
    else:
        print("No 'scraped-data' artifact found")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

