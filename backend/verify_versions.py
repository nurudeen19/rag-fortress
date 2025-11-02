#!/usr/bin/env python3
"""
Version Verification Script
Checks if all packages in requirements.txt are installed with correct versions
"""

import sys
import subprocess
from pathlib import Path


def get_installed_version(package_name):
    """Get the installed version of a package."""
    try:
        result = subprocess.run(
            ["pip", "show", package_name],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':')[1].strip()
        return None
    except Exception:
        return None


def parse_requirements(file_path):
    """Parse requirements.txt file."""
    requirements = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                # Handle package[extras]==version format
                if '==' in line:
                    package_with_extras = line.split('==')[0]
                    required_version = line.split('==')[1]
                    
                    # Remove extras (e.g., [standard], [cryptography])
                    if '[' in package_with_extras:
                        package = package_with_extras.split('[')[0]
                    else:
                        package = package_with_extras
                    
                    requirements.append((package, required_version))
    return requirements


def main():
    """Main verification function."""
    print("=" * 70)
    print("RAG Fortress - Package Version Verification")
    print("=" * 70)
    print()
    
    # Find requirements.txt
    requirements_file = Path(__file__).parent.parent / 'requirements.txt'
    
    if not requirements_file.exists():
        print(f"❌ Error: requirements.txt not found at {requirements_file}")
        sys.exit(1)
    
    print(f"📋 Reading requirements from: {requirements_file}")
    print()
    
    # Parse requirements
    requirements = parse_requirements(requirements_file)
    
    print(f"🔍 Checking {len(requirements)} packages...")
    print()
    
    # Check each package
    correct = 0
    incorrect = 0
    missing = 0
    
    issues = []
    
    for package, required_version in requirements:
        installed_version = get_installed_version(package)
        
        if installed_version is None:
            status = "❌ NOT INSTALLED"
            missing += 1
            issues.append(f"  - {package}: Not installed (required: {required_version})")
        elif installed_version == required_version:
            status = "✅ CORRECT"
            correct += 1
        else:
            status = f"⚠️  VERSION MISMATCH"
            incorrect += 1
            issues.append(
                f"  - {package}: Installed {installed_version} "
                f"(required: {required_version})"
            )
        
        print(f"{status:20} {package:30} {installed_version or 'N/A':15} → {required_version}")
    
    # Summary
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"✅ Correct versions:    {correct}/{len(requirements)}")
    print(f"⚠️  Version mismatches:  {incorrect}/{len(requirements)}")
    print(f"❌ Missing packages:    {missing}/{len(requirements)}")
    print()
    
    # Print issues if any
    if issues:
        print("=" * 70)
        print("Issues Found")
        print("=" * 70)
        for issue in issues:
            print(issue)
        print()
        print("To fix these issues, run:")
        print("  pip install -r requirements.txt --upgrade")
        print()
        return 1
    else:
        print("🎉 All packages are correctly installed!")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
