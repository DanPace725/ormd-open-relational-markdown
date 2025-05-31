#!/usr/bin/env python3
"""
Setup script for ORMD git hooks.

This script installs the pre-commit hook that validates ORMD files.
"""

import sys
import shutil
from pathlib import Path
import stat
import os


def find_git_directory():
    """Find the .git directory in the current repository."""
    current = Path.cwd()
    
    while current != current.parent:
        git_dir = current / '.git'
        if git_dir.exists():
            if git_dir.is_file():
                # Git worktree case - read the .git file to find actual git dir
                with open(git_dir, 'r') as f:
                    content = f.read().strip()
                    if content.startswith('gitdir: '):
                        git_path = Path(content[8:])
                        if not git_path.is_absolute():
                            git_path = current / git_path
                        return git_path
            else:
                return git_dir
        current = current.parent
    
    return None


def install_pre_commit_hook():
    """Install the ORMD pre-commit hook."""
    # Find git directory
    git_dir = find_git_directory()
    if not git_dir:
        print("❌ Error: Not in a git repository")
        return False
    
    hooks_dir = git_dir / 'hooks'
    hooks_dir.mkdir(exist_ok=True)
    
    # Find the pre-commit hook source
    script_dir = Path(__file__).parent
    hook_source = script_dir / 'pre-commit-ormd'
    
    if not hook_source.exists():
        print(f"❌ Error: Hook source not found at {hook_source}")
        return False
    
    # Install the hook
    hook_dest = hooks_dir / 'pre-commit'
    
    # Check if hook already exists
    if hook_dest.exists():
        print(f"⚠️  Warning: {hook_dest} already exists")
        
        # Check if it's our hook
        try:
            with open(hook_dest, 'r') as f:
                content = f.read()
                if 'ORMD file validation' in content:
                    print("✅ ORMD pre-commit hook is already installed")
                    return True
        except Exception:
            pass
        
        response = input("Do you want to replace it? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Installation cancelled")
            return False
        
        # Backup existing hook
        backup_path = hook_dest.with_suffix('.backup')
        shutil.copy2(hook_dest, backup_path)
        print(f"📋 Backed up existing hook to {backup_path}")
    
    # Copy the hook
    shutil.copy2(hook_source, hook_dest)
    
    # Make it executable
    current_mode = hook_dest.stat().st_mode
    hook_dest.chmod(current_mode | stat.S_IEXEC)
    
    print(f"✅ Installed ORMD pre-commit hook at {hook_dest}")
    return True


def test_hook():
    """Test the installed hook."""
    print("\n🧪 Testing the hook...")
    
    # Create a test file
    test_file = Path('test_hook.ormd')
    test_content = '''<!-- ormd:0.1 -->
---
title: "Test Hook Document"
authors: ["Test Author"]
links: []
---

# Test Hook

This is a test document for the pre-commit hook.
'''
    
    try:
        test_file.write_text(test_content)
        
        # Stage the test file
        import subprocess
        subprocess.run(['git', 'add', str(test_file)], check=True)
        
        # Run the hook
        git_dir = find_git_directory()
        hook_path = git_dir / 'hooks' / 'pre-commit'
        
        result = subprocess.run([sys.executable, str(hook_path)], capture_output=True, text=True)
        
        print("Hook output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Hook test passed!")
        else:
            print("❌ Hook test failed")
        
        # Clean up
        subprocess.run(['git', 'reset', 'HEAD', str(test_file)], check=True)
        test_file.unlink()
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Hook test failed: {e}")
        # Clean up
        if test_file.exists():
            test_file.unlink()
        return False


def uninstall_hook():
    """Uninstall the ORMD pre-commit hook."""
    git_dir = find_git_directory()
    if not git_dir:
        print("❌ Error: Not in a git repository")
        return False
    
    hook_path = git_dir / 'hooks' / 'pre-commit'
    
    if not hook_path.exists():
        print("✅ No pre-commit hook found")
        return True
    
    # Check if it's our hook
    try:
        with open(hook_path, 'r') as f:
            content = f.read()
            if 'ORMD file validation' not in content:
                print("⚠️  Warning: pre-commit hook exists but doesn't appear to be ORMD hook")
                response = input("Do you want to remove it anyway? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("❌ Uninstall cancelled")
                    return False
    except Exception:
        pass
    
    hook_path.unlink()
    print(f"✅ Removed pre-commit hook at {hook_path}")
    return True


def main():
    """Main setup function."""
    print("🔧 ORMD Git Hooks Setup")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
    else:
        print("Available actions:")
        print("  install   - Install the pre-commit hook")
        print("  test      - Test the installed hook")
        print("  uninstall - Remove the pre-commit hook")
        print()
        action = input("What would you like to do? (install/test/uninstall): ").strip().lower()
    
    if action in ['install', 'i']:
        if install_pre_commit_hook():
            print("\n📋 Hook installed successfully!")
            print("\nThe hook will now:")
            print("  • Validate all staged .ormd files before commits")
            print("  • Block commits if validation fails")
            print("  • Show detailed error messages for invalid files")
            print("\nTo test the hook, run: python hooks/setup_hooks.py test")
            print("To bypass validation: git commit --no-verify")
            
            # Ask if they want to test
            response = input("\nWould you like to test the hook now? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                test_hook()
        
    elif action in ['test', 't']:
        if not test_hook():
            sys.exit(1)
            
    elif action in ['uninstall', 'u', 'remove']:
        if uninstall_hook():
            print("✅ Hook uninstalled successfully")
        
    else:
        print(f"❌ Unknown action: {action}")
        print("Use: install, test, or uninstall")
        sys.exit(1)


if __name__ == '__main__':
    main() 