#!/usr/bin/env python3
"""
Validate a skill directory structure and content.

Usage:
    python validate_skill.py <skill-directory>

Checks:
    - SKILL.md exists with valid frontmatter
    - Name follows conventions (lowercase, hyphens)
    - Description is present and well-formed
    - SKILL.md body is under 500 lines
    - Reference files are one level deep
    - Internal links are valid
    - No forbidden files (README.md, CHANGELOG.md, etc.)
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


class ValidationError:
    def __init__(self, severity: str, message: str, file: str = None):
        self.severity = severity  # "error" or "warning"
        self.message = message
        self.file = file
    
    def __str__(self):
        prefix = "❌" if self.severity == "error" else "⚠️"
        location = f" ({self.file})" if self.file else ""
        return f"{prefix} {self.message}{location}"


def parse_frontmatter(content: str) -> Tuple[dict, str]:
    """Extract YAML frontmatter and body from SKILL.md content."""
    if not content.startswith("---"):
        return None, content
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content
    
    frontmatter = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()
    
    body = parts[2].strip()
    return frontmatter, body


def validate_skill(skill_dir: Path) -> List[ValidationError]:
    """Validate a skill directory and return list of issues."""
    errors = []
    
    # Check SKILL.md exists
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(ValidationError("error", "SKILL.md not found"))
        return errors
    
    content = skill_md.read_text()
    frontmatter, body = parse_frontmatter(content)
    
    # Validate frontmatter
    if frontmatter is None:
        errors.append(ValidationError("error", "Missing or invalid YAML frontmatter"))
        return errors
    
    # Check name
    name = frontmatter.get("name", "")
    if not name:
        errors.append(ValidationError("error", "Missing 'name' in frontmatter"))
    elif not re.match(r"^[a-z][a-z0-9-]*$", name):
        errors.append(ValidationError("error", f"Invalid name '{name}': must be lowercase letters, numbers, hyphens"))
    elif len(name) > 64:
        errors.append(ValidationError("error", f"Name too long ({len(name)} chars): max 64"))
    elif "claude" in name.lower() or "anthropic" in name.lower():
        errors.append(ValidationError("error", "Name cannot contain reserved words: 'claude', 'anthropic'"))
    
    # Check description
    description = frontmatter.get("description", "")
    if not description:
        errors.append(ValidationError("error", "Missing 'description' in frontmatter"))
    elif len(description) < 50:
        errors.append(ValidationError("warning", f"Description too short ({len(description)} chars): recommend 100+"))
    elif len(description) > 1024:
        errors.append(ValidationError("error", f"Description too long ({len(description)} chars): max 1024"))
    
    # Check description quality
    if description:
        if description.lower().startswith("i ") or "i can" in description.lower():
            errors.append(ValidationError("warning", "Description should be in third person (avoid 'I')"))
        if description.lower().startswith("you "):
            errors.append(ValidationError("warning", "Description should be in third person (avoid 'you')"))
        if "use when" not in description.lower() and "trigger" not in description.lower():
            errors.append(ValidationError("warning", "Description should include trigger context (e.g., 'Use when...')"))
    
    # Check body length
    body_lines = len(body.split("\n"))
    if body_lines > 500:
        errors.append(ValidationError("warning", f"SKILL.md body too long ({body_lines} lines): recommend <500"))
    
    # Check for forbidden files
    forbidden_files = ["README.md", "CHANGELOG.md", "CONTRIBUTING.md", "INSTALLATION.md"]
    for forbidden in forbidden_files:
        if (skill_dir / forbidden).exists():
            errors.append(ValidationError("warning", f"Unnecessary file: {forbidden}"))
    
    # Check reference files depth
    for ref_file in skill_dir.rglob("*.md"):
        rel_path = ref_file.relative_to(skill_dir)
        depth = len(rel_path.parts)
        if depth > 2 and ref_file.name != "SKILL.md":
            errors.append(ValidationError("warning", f"Reference file too deep ({depth} levels)", str(rel_path)))
    
    # Validate internal links
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(link_pattern, content):
        link_text, link_target = match.groups()
        
        # Skip external links
        if link_target.startswith("http"):
            continue
        
        # Check if file exists
        target_path = skill_dir / link_target.split("#")[0]
        if not target_path.exists():
            errors.append(ValidationError("error", f"Broken link: {link_target}"))
    
    # Check for Windows paths
    if "\\" in content:
        errors.append(ValidationError("error", "Windows-style paths found (use forward slashes)"))
    
    # Check scripts are executable
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.glob("*.py"):
            if not script.stat().st_mode & 0o111:
                errors.append(ValidationError("warning", f"Script not executable", str(script.name)))
        for script in scripts_dir.glob("*.sh"):
            if not script.stat().st_mode & 0o111:
                errors.append(ValidationError("warning", f"Script not executable", str(script.name)))
    
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate a skill directory")
    parser.add_argument("skill_dir", type=Path, help="Path to skill directory")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    
    args = parser.parse_args()
    
    if not args.skill_dir.exists():
        print(f"❌ Directory not found: {args.skill_dir}")
        sys.exit(1)
    
    if not args.skill_dir.is_dir():
        print(f"❌ Not a directory: {args.skill_dir}")
        sys.exit(1)
    
    print(f"Validating skill: {args.skill_dir}\n")
    
    errors = validate_skill(args.skill_dir)
    
    if not errors:
        print("✅ All checks passed!")
        sys.exit(0)
    
    # Group by severity
    error_count = sum(1 for e in errors if e.severity == "error")
    warning_count = sum(1 for e in errors if e.severity == "warning")
    
    for error in errors:
        print(error)
    
    print(f"\nSummary: {error_count} error(s), {warning_count} warning(s)")
    
    if error_count > 0 or (args.strict and warning_count > 0):
        sys.exit(1)
    else:
        print("\n✅ Validation passed (with warnings)")
        sys.exit(0)


if __name__ == "__main__":
    main()
