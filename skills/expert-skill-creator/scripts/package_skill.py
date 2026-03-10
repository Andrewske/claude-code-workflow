#!/usr/bin/env python3
"""
Package a skill directory into a distributable .skill file.

Usage:
    python package_skill.py <skill-directory> [output-directory]

The script will:
1. Validate the skill (fails if errors found)
2. Create a .skill file (ZIP with proper structure)

Example:
    python package_skill.py ./my-skill
    python package_skill.py ./my-skill ./dist
"""

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path


def get_skill_name(skill_dir: Path) -> str:
    """Extract skill name from SKILL.md frontmatter."""
    skill_md = skill_dir / "SKILL.md"
    
    if not skill_md.exists():
        raise FileNotFoundError("SKILL.md not found")
    
    content = skill_md.read_text()
    
    for line in content.split("\n"):
        if line.strip().startswith("name:"):
            return line.split(":", 1)[1].strip()
    
    raise ValueError("Could not find 'name' in SKILL.md frontmatter")


def validate_skill(skill_dir: Path) -> bool:
    """Run validation and return True if passed."""
    script_dir = Path(__file__).parent
    validate_script = script_dir / "validate_skill.py"
    
    result = subprocess.run(
        [sys.executable, str(validate_script), str(skill_dir)],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0


def package_skill(skill_dir: Path, output_dir: Path) -> Path:
    """Create .skill package from directory."""
    
    # Get skill name
    skill_name = get_skill_name(skill_dir)
    
    # Create output path
    output_file = output_dir / f"{skill_name}.skill"
    
    # Create ZIP file
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in skill_dir.rglob("*"):
            if file_path.is_file():
                # Skip common unwanted files
                if file_path.name.startswith("."):
                    continue
                if file_path.name == "__pycache__":
                    continue
                if file_path.suffix == ".pyc":
                    continue
                
                # Add to ZIP with relative path
                arc_name = file_path.relative_to(skill_dir)
                zf.write(file_path, arc_name)
    
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Package a skill into a .skill file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
The .skill file is a ZIP archive that can be:
- Shared with team members
- Installed via: /plugin add ./skill-name.skill
- Uploaded to skill marketplaces

Example:
    %(prog)s ./my-skill
    %(prog)s ./my-skill ./dist
        """
    )
    
    parser.add_argument(
        "skill_dir",
        type=Path,
        help="Path to skill directory"
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        nargs="?",
        default=Path("."),
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation (not recommended)"
    )
    
    args = parser.parse_args()
    
    # Check skill directory exists
    if not args.skill_dir.exists():
        print(f"❌ Skill directory not found: {args.skill_dir}")
        sys.exit(1)
    
    if not args.skill_dir.is_dir():
        print(f"❌ Not a directory: {args.skill_dir}")
        sys.exit(1)
    
    # Validate
    if not args.skip_validation:
        print("Step 1: Validating skill...\n")
        if not validate_skill(args.skill_dir):
            print("\n❌ Validation failed. Fix errors before packaging.")
            sys.exit(1)
        print()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Package
    print("Step 2: Creating package...")
    
    try:
        output_file = package_skill(args.skill_dir, args.output_dir)
        
        # Get file size
        size_kb = output_file.stat().st_size / 1024
        
        print(f"\n✅ Created: {output_file} ({size_kb:.1f} KB)")
        print(f"\nTo install:")
        print(f"  /plugin add {output_file}")
        
    except Exception as e:
        print(f"\n❌ Packaging failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
