import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


def archive_digest():
    """
    Archive the current digest.json and update the history index.
    This script manages the history directory structure for Artifact persistence.
    """
    # Paths
    # Assuming script is run from project root
    project_root = Path.cwd()
    frontend_public_dir = project_root / "frontend" / "public"
    digest_file = frontend_public_dir / "digest.json"

    # The directory where we store the history artifact content
    # We will download the artifact here, update it, and then upload it back
    history_artifact_dir = project_root / "digest-history"
    history_data_dir = history_artifact_dir / "history"
    index_file = history_data_dir / "index.json"

    # Ensure directories exist
    history_data_dir.mkdir(parents=True, exist_ok=True)

    if not digest_file.exists():
        print(f"Error: {digest_file} not found.")
        sys.exit(1)

    # Get current date (UTC)
    # Use full timestamp for filename to avoid collisions and keep precision
    # Format: YYYY-MM-DD_HH-MM-SS
    now = datetime.utcnow()
    timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    archive_file = history_data_dir / f"{timestamp_str}.json"

    # Copy digest.json to history/YYYY-MM-DD_HH-MM-SS.json
    print(f"Archiving {digest_file} to {archive_file}...")
    shutil.copy2(digest_file, archive_file)

    # Update index.json
    history_dates = []
    if index_file.exists():
        try:
            with open(index_file) as f:
                history_dates = json.load(f)
        except json.JSONDecodeError:
            print("Warning: index.json is corrupt, starting fresh.")
            history_dates = []

    if timestamp_str not in history_dates:
        history_dates.append(timestamp_str)
        history_dates.sort(reverse=True)  # Keep sorted descending

        print(f"Updating index.json with {timestamp_str}...")
        with open(index_file, "w") as f:
            json.dump(history_dates, f, indent=2)
    else:
        print(f"Date {timestamp_str} already in index.")

    # Also copy the history directory back to frontend/public so it's included in the build
    # This ensures the deployed site has the history data
    frontend_history_dir = frontend_public_dir / "history"
    if frontend_history_dir.exists():
        shutil.rmtree(frontend_history_dir)
    shutil.copytree(history_data_dir, frontend_history_dir)
    print(f"Copied history to {frontend_history_dir} for deployment.")


if __name__ == "__main__":
    archive_digest()
