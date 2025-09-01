#!/usr/bin/env python3
"""Cleanup script for compaction tags in SolarWindPy repository.

This script removes all claude/compaction/* tags from both local and remote repositories
as part of migrating from tag-based to file-based compaction.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True, capture_output=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=capture_output, text=True
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return (
            False,
            e.stdout.strip() if e.stdout else "",
            e.stderr.strip() if e.stderr else "",
        )


def main():
    """Main cleanup function."""

    print("🧹 Cleaning up compaction tags from SolarWindPy repository...")

    # Check if we're in a git repository
    if not Path(".git").exists():
        print("❌ Not in a git repository")
        sys.exit(1)

    # Get all compaction tags
    success, tags_output, error = run_command("git tag -l 'claude/compaction/*'")
    if not success:
        print(f"❌ Failed to list tags: {error}")
        sys.exit(1)

    if not tags_output:
        print("✅ No compaction tags found - cleanup complete")
        return

    tags = tags_output.splitlines()
    print(f"🏷️  Found {len(tags)} compaction tags to remove:")
    for tag in tags[:10]:  # Show first 10
        print(f"   - {tag}")
    if len(tags) > 10:
        print(f"   ... and {len(tags) - 10} more")

    # Confirm deletion
    response = (
        input(f"\nDelete all {len(tags)} compaction tags? [y/N]: ").strip().lower()
    )
    if response not in ("y", "yes"):
        print("🚫 Cleanup cancelled")
        return

    # Delete local tags
    print("\n🗑️  Deleting local compaction tags...")
    deleted_local = 0
    for tag in tags:
        success, _, error = run_command(f"git tag -d '{tag}'")
        if success:
            deleted_local += 1
        else:
            print(f"⚠️  Failed to delete local tag {tag}: {error}")

    print(f"✅ Deleted {deleted_local} local tags")

    # Delete remote tags (if they exist)
    print("\n🌐 Checking for remote compaction tags...")
    success, remote_tags, error = run_command(
        "git ls-remote --tags origin | grep 'claude/compaction/'"
    )

    if success and remote_tags:
        remote_tag_list = []
        for line in remote_tags.splitlines():
            if "claude/compaction/" in line:
                tag_ref = line.split("\t")[1]  # refs/tags/claude/compaction/...
                tag_name = tag_ref.replace("refs/tags/", "")
                remote_tag_list.append(tag_name)

        if remote_tag_list:
            print(f"🌐 Found {len(remote_tag_list)} remote compaction tags")
            response = (
                input(f"Delete {len(remote_tag_list)} remote compaction tags? [y/N]: ")
                .strip()
                .lower()
            )

            if response in ("y", "yes"):
                print("🗑️  Deleting remote compaction tags...")
                deleted_remote = 0
                for tag in remote_tag_list:
                    success, _, error = run_command(f"git push origin --delete '{tag}'")
                    if success:
                        deleted_remote += 1
                        print(f"   ✅ Deleted remote tag: {tag}")
                    else:
                        print(f"   ⚠️  Failed to delete remote tag {tag}: {error}")

                print(f"✅ Deleted {deleted_remote} remote tags")
            else:
                print("🚫 Remote tag deletion cancelled")
        else:
            print("✅ No remote compaction tags found")
    else:
        print("✅ No remote compaction tags found")

    # Final verification
    success, remaining_tags, _ = run_command("git tag -l 'claude/compaction/*'")
    if success and remaining_tags:
        print(
            f"⚠️  Warning: {len(remaining_tags.splitlines())} compaction tags still remain"
        )
    else:
        print("🎉 All compaction tags successfully removed!")

    print("\n📝 Compaction is now file-based only:")
    print("   - No more git tags for compaction")
    print("   - Compaction files stored in .claude/ directory")
    print("   - Unique timestamped filenames prevent conflicts")

    print("\n✅ Cleanup complete!")


if __name__ == "__main__":
    main()
