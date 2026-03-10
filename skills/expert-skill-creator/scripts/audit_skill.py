#!/usr/bin/env python3
"""
Audit project skill against current codebase.

Usage:
    python audit_skill.py [--commits N] [--area AREA] [--full]

Options:
    --commits N    Check against last N commits (default: 10)
    --area AREA    Focus on specific area (architecture, flows, errors, commands)
    --full         Run comprehensive audit of all areas

Output:
    Report of potential staleness and suggested updates
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional


def run_cmd(cmd: str) -> str:
    """Run shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return ""


def get_recent_changes(num_commits: int) -> Dict:
    """Analyze recent git commits."""
    
    changes = {
        "commits": [],
        "files_changed": [],
        "new_files": [],
        "deleted_files": [],
        "api_changes": [],
        "schema_changes": [],
    }
    
    # Get commit summaries
    commits = run_cmd(f"git log --oneline -{num_commits}")
    changes["commits"] = commits.split("\n") if commits else []
    
    # Get changed files
    files = run_cmd(f"git diff --name-status HEAD~{num_commits}..HEAD 2>/dev/null")
    if files:
        for line in files.split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                status, filepath = parts[0], parts[-1]
                changes["files_changed"].append(filepath)
                
                if status == "A":
                    changes["new_files"].append(filepath)
                elif status == "D":
                    changes["deleted_files"].append(filepath)
                
                # Categorize important changes
                if "/api/" in filepath or "route.ts" in filepath:
                    changes["api_changes"].append(filepath)
                if "schema" in filepath.lower() or "prisma" in filepath.lower():
                    changes["schema_changes"].append(filepath)
    
    return changes


def get_current_structure() -> Dict:
    """Get current codebase structure."""
    
    structure = {
        "directories": [],
        "api_routes": [],
        "services": [],
        "components": [],
    }
    
    # Top-level src directories
    dirs = run_cmd("find src -type d -maxdepth 2 2>/dev/null")
    structure["directories"] = dirs.split("\n") if dirs else []
    
    # API routes
    routes = run_cmd("find src -path '*/api/*' -name '*.ts' 2>/dev/null")
    structure["api_routes"] = routes.split("\n") if routes else []
    
    # Services
    services = run_cmd("find src -name '*[Ss]ervice*' -type f 2>/dev/null")
    structure["services"] = services.split("\n") if services else []
    
    return structure


def get_error_patterns() -> List[str]:
    """Find error patterns in codebase."""
    
    errors = []
    
    # Custom error classes
    classes = run_cmd("grep -r 'class.*Error' --include='*.ts' src/ 2>/dev/null")
    if classes:
        errors.extend(classes.split("\n"))
    
    # Throw statements
    throws = run_cmd("grep -r 'throw new' --include='*.ts' src/ 2>/dev/null | head -20")
    if throws:
        errors.extend(throws.split("\n"))
    
    return errors


def get_package_scripts() -> Dict[str, str]:
    """Get npm scripts from package.json."""
    
    try:
        content = Path("package.json").read_text()
        data = json.loads(content)
        return data.get("scripts", {})
    except:
        return {}


def check_skill_exists() -> Optional[Path]:
    """Find project skill location."""
    
    locations = [
        Path(".claude/skills/project-knowledge"),
        Path(".claude/skills/understanding-project"),
    ]
    
    # Also check for any skill with "project" or "knowledge" in name
    skills_dir = Path(".claude/skills")
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and ("project" in skill_dir.name or "knowledge" in skill_dir.name):
                if (skill_dir / "SKILL.md").exists():
                    return skill_dir
    
    for loc in locations:
        if (loc / "SKILL.md").exists():
            return loc
    
    return None


def audit_commits(num_commits: int) -> None:
    """Audit based on recent commits."""
    
    print(f"\n📊 Analyzing last {num_commits} commits...\n")
    
    changes = get_recent_changes(num_commits)
    
    print(f"Commits analyzed: {len(changes['commits'])}")
    print(f"Files changed: {len(changes['files_changed'])}")
    print(f"New files: {len(changes['new_files'])}")
    print(f"Deleted files: {len(changes['deleted_files'])}")
    
    if changes["api_changes"]:
        print(f"\n⚠️  API changes detected ({len(changes['api_changes'])} files):")
        for f in changes["api_changes"][:5]:
            print(f"   - {f}")
        print("   → Consider updating: reference/data-flows.md")
    
    if changes["schema_changes"]:
        print(f"\n⚠️  Schema changes detected ({len(changes['schema_changes'])} files):")
        for f in changes["schema_changes"][:5]:
            print(f"   - {f}")
        print("   → Consider updating: reference/architecture.md")
    
    if changes["new_files"]:
        print(f"\n📁 New files ({len(changes['new_files'])}):")
        for f in changes["new_files"][:10]:
            print(f"   + {f}")
    
    if changes["deleted_files"]:
        print(f"\n🗑️  Deleted files ({len(changes['deleted_files'])}):")
        for f in changes["deleted_files"][:10]:
            print(f"   - {f}")


def audit_full() -> None:
    """Run comprehensive audit."""
    
    print("\n🔍 Running full skill audit...\n")
    
    skill_path = check_skill_exists()
    if not skill_path:
        print("❌ No project skill found in .claude/skills/")
        print("   Create one with: /project:create-skill project knowledge skill")
        return
    
    print(f"✅ Found skill: {skill_path}\n")
    
    # Check structure
    print("=" * 50)
    print("ARCHITECTURE CHECK")
    print("=" * 50)
    structure = get_current_structure()
    print(f"Directories: {len(structure['directories'])}")
    print(f"API routes: {len(structure['api_routes'])}")
    print(f"Services: {len(structure['services'])}")
    print("\n→ Compare to: reference/architecture.md")
    
    # Check errors
    print("\n" + "=" * 50)
    print("ERROR PATTERNS CHECK")
    print("=" * 50)
    errors = get_error_patterns()
    print(f"Error patterns found in code: {len(errors)}")
    print("\n→ Compare to: reference/error-patterns.md")
    
    # Check commands
    print("\n" + "=" * 50)
    print("COMMANDS CHECK")
    print("=" * 50)
    scripts = get_package_scripts()
    print(f"npm scripts defined: {len(scripts)}")
    if scripts:
        print("Key scripts:")
        for name in ["dev", "build", "test", "lint", "start"]:
            if name in scripts:
                print(f"   {name}: {scripts[name][:50]}...")
    print("\n→ Compare to commands table in SKILL.md")
    
    # Recent changes
    print("\n" + "=" * 50)
    print("RECENT CHANGES")
    print("=" * 50)
    audit_commits(10)


def main():
    parser = argparse.ArgumentParser(description="Audit project skill")
    parser.add_argument("--commits", "-c", type=int, default=10,
                        help="Number of commits to analyze")
    parser.add_argument("--area", "-a", choices=["architecture", "flows", "errors", "commands"],
                        help="Focus on specific area")
    parser.add_argument("--full", "-f", action="store_true",
                        help="Run full audit")
    
    args = parser.parse_args()
    
    # Check we're in a git repo
    if not Path(".git").exists():
        print("❌ Not in a git repository")
        sys.exit(1)
    
    if args.full:
        audit_full()
    elif args.area:
        print(f"\n🔍 Auditing area: {args.area}")
        # Could add area-specific logic here
        audit_full()  # For now, run full
    else:
        audit_commits(args.commits)
    
    print("\n" + "=" * 50)
    print("NEXT STEPS")
    print("=" * 50)
    print("1. Review the changes above")
    print("2. Update relevant reference files")
    print("3. Run: /project:update-skill [specific area]")
    print("   or ask Claude to update based on this report")


if __name__ == "__main__":
    main()
