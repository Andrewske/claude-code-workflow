#!/usr/bin/env python3
"""
Initialize a new skill directory with template files.

Usage:
    python init_skill.py <skill-name> --type <type> --path <output-dir>

Types:
    simple   - Simple utility skill (single-file pattern)
    domain   - Domain knowledge skill (reference-heavy)
    project  - Project knowledge skill (architecture, debugging)
    workflow - Complex workflow skill (multi-step, validation)

Example:
    python init_skill.py image-converter --type simple --path ./skills
    python init_skill.py my-project --type project --path ~/.claude/skills
"""

import argparse
import shutil
import sys
from pathlib import Path


SKILL_TYPES = {
    "simple": "simple-utility",
    "domain": "domain-knowledge", 
    "project": "project-knowledge",
    "workflow": "complex-workflow"
}


def get_template_dir(skill_type: str) -> Path:
    """Get the template directory for the given skill type."""
    script_dir = Path(__file__).parent.parent
    template_name = SKILL_TYPES.get(skill_type)
    
    if not template_name:
        raise ValueError(f"Unknown skill type: {skill_type}")
    
    template_dir = script_dir / "templates" / template_name
    
    if not template_dir.exists():
        raise FileNotFoundError(f"Template not found: {template_dir}")
    
    return template_dir


def create_skill(name: str, skill_type: str, output_path: Path) -> Path:
    """Create a new skill from template."""
    
    # Validate skill name
    if not name.replace("-", "").isalnum():
        raise ValueError("Skill name must contain only letters, numbers, and hyphens")
    
    if name != name.lower():
        raise ValueError("Skill name must be lowercase")
    
    # Get template
    template_dir = get_template_dir(skill_type)
    
    # Create output directory
    skill_dir = output_path / name
    
    if skill_dir.exists():
        raise FileExistsError(f"Skill directory already exists: {skill_dir}")
    
    # Copy template
    shutil.copytree(template_dir, skill_dir)
    
    # Update SKILL.md with actual name
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text()
        
        # Replace placeholder name
        content = content.replace(
            "name: [skill-name]",
            f"name: {name}"
        )
        content = content.replace(
            "name: querying-[domain]",
            f"name: {name}"
        )
        content = content.replace(
            "name: understanding-[project-name]",
            f"name: {name}"
        )
        content = content.replace(
            "name: processing-[resource]",
            f"name: {name}"
        )
        
        # Replace placeholder titles
        content = content.replace(
            "# [Skill Name]",
            f"# {name.replace('-', ' ').title()}"
        )
        content = content.replace(
            "# [Domain] Data Access",
            f"# {name.replace('-', ' ').title()}"
        )
        content = content.replace(
            "# [Project Name] Knowledge Base",
            f"# {name.replace('-', ' ').title()}"
        )
        content = content.replace(
            "# [Resource] Processing",
            f"# {name.replace('-', ' ').title()}"
        )
        
        skill_md.write_text(content)
    
    # Make scripts executable
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.glob("*.py"):
            script.chmod(script.stat().st_mode | 0o111)
        for script in scripts_dir.glob("*.sh"):
            script.chmod(script.stat().st_mode | 0o111)
    
    return skill_dir


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new skill directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Types:
    simple   - Simple utility skill (converters, single-purpose tools)
    domain   - Domain knowledge skill (schemas, APIs, business logic)
    project  - Project knowledge skill (architecture, debugging)
    workflow - Complex workflow skill (multi-step with validation)

Examples:
    %(prog)s image-converter --type simple --path ./skills
    %(prog)s company-data --type domain --path ./skills
    %(prog)s my-project --type project --path ~/.claude/skills
    %(prog)s pdf-processor --type workflow --path ./skills
        """
    )
    
    parser.add_argument(
        "name",
        help="Skill name (lowercase, hyphens allowed)"
    )
    parser.add_argument(
        "--type", "-t",
        required=True,
        choices=SKILL_TYPES.keys(),
        help="Type of skill to create"
    )
    parser.add_argument(
        "--path", "-p",
        required=True,
        type=Path,
        help="Output directory for the skill"
    )
    
    args = parser.parse_args()
    
    try:
        # Ensure output path exists
        args.path.mkdir(parents=True, exist_ok=True)
        
        # Create skill
        skill_dir = create_skill(args.name, args.type, args.path)
        
        print(f"✅ Created skill: {skill_dir}")
        print(f"\nNext steps:")
        print(f"  1. Edit {skill_dir}/SKILL.md")
        print(f"     - Update the description with specific triggers")
        print(f"     - Fill in the template sections")
        print(f"  2. Add reference files to {skill_dir}/reference/ (if needed)")
        print(f"  3. Add scripts to {skill_dir}/scripts/ (if needed)")
        print(f"  4. Validate: python scripts/validate_skill.py {skill_dir}")
        print(f"  5. Package: python scripts/package_skill.py {skill_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
