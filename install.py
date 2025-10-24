#!/usr/bin/env python3
"""
Quick Installation Script for LookAway

This script provides a quick way to install and set up LookAway
on both Windows and Linux systems.
"""

import os
import sys
import subprocess
import platform


def run_command(command, shell=False):
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=shell, check=True, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def install_dependencies():
    """Install required Python packages."""
    print("📦 Installing dependencies...")
    
    # Check if pip is available
    success, _ = run_command([sys.executable, "-m", "pip", "--version"])
    if not success:
        print("❌ pip is not available. Please install pip first.")
        return False
    
    # Install requirements
    success, output = run_command([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
    ])
    
    if success:
        print("✅ Dependencies installed successfully!")
        return True
    else:
        print(f"❌ Failed to install dependencies: {output}")
        return False


def setup_virtual_environment():
    """Create and setup virtual environment."""
    print("🐍 Creating virtual environment...")
    
    venv_dir = "lookaway-env"
    
    # Create virtual environment
    success, output = run_command([sys.executable, "-m", "venv", venv_dir])
    if not success:
        print(f"❌ Failed to create virtual environment: {output}")
        return False
    
    print(f"✅ Virtual environment created: {venv_dir}")
    
    # Get activation command
    if platform.system() == "Windows":
        activate_script = os.path.join(venv_dir, "Scripts", "activate.bat")
        pip_executable = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        activate_script = os.path.join(venv_dir, "bin", "activate")
        pip_executable = os.path.join(venv_dir, "bin", "pip")
    
    # Install requirements in virtual environment
    success, output = run_command([pip_executable, "install", "-r", "requirements.txt"])
    if success:
        print("✅ Dependencies installed in virtual environment!")
        return True, venv_dir, activate_script
    else:
        print(f"❌ Failed to install dependencies in venv: {output}")
        return False, None, None


def main():
    """Main installation process."""
    print("🔔 LookAway Installation Script")
    print("=" * 40)
    print()
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required.")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Ask about virtual environment
    print()
    use_venv = input("Create virtual environment? (recommended) [Y/n]: ").strip().lower()
    use_venv = use_venv in ('', 'y', 'yes')
    
    if use_venv:
        result = setup_virtual_environment()
        if isinstance(result, tuple) and result[0]:
            success, venv_dir, activate_script = result
            print(f"\n📝 To activate virtual environment:")
            if platform.system() == "Windows":
                print(f"   {activate_script}")
            else:
                print(f"   source {activate_script}")
        else:
            print("❌ Virtual environment setup failed. Trying system-wide installation...")
            if not install_dependencies():
                sys.exit(1)
    else:
        if not install_dependencies():
            sys.exit(1)
    
    print()
    print("🚀 Running initial setup...")
    
    # Run setup wizard
    success, output = run_command([sys.executable, "main.py", "setup"])
    if success:
        print("\n✅ LookAway installed and configured successfully!")
        print()
        print("📋 Next steps:")
        print("   1. Run 'python main.py start' to start the application")
        print("   2. Use system tray icon to control the application")
        print("   3. Run startup scripts in 'scripts/' folder for auto-start")
        print()
        
        # Ask about auto-start installation
        setup_autostart = input("Install auto-start now? [y/N]: ").strip().lower()
        if setup_autostart in ('y', 'yes'):
            if platform.system() == "Windows":
                print("Running Windows startup installation...")
                run_command(["scripts\\install_windows_startup.bat"], shell=True)
            else:
                print("Running Linux startup installation...")
                run_command(["chmod", "+x", "scripts/install_linux_startup.sh"])
                run_command(["./scripts/install_linux_startup.sh"], shell=True)
        
    else:
        print(f"❌ Setup failed: {output}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation error: {e}")
        sys.exit(1)