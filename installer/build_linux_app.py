#!/usr/bin/env python3
"""
Linux Build Script for LookAway Application
Creates a Linux executable using PyInstaller with proper configuration for Linux systems.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_linux_app(python_executable=None):
    """Build the main LookAway application for Linux using PyInstaller."""
    print("Building LookAway for Linux...")
    
    if python_executable is None:
        python_executable = sys.executable
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Project root: {project_root}")
    
    # Ensure we're in the right directory
    os.chdir(project_root)
    
    # Clean previous builds
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Create PyInstaller command
    main_py = project_root / "main.py"
    
    if not main_py.exists():
        print(f"Error: {main_py} not found!")
        return False
    
    # Build command with proper options for Linux compatibility
    cmd = [
        python_executable, '-m', 'PyInstaller',
        '--onefile',                    # Single executable file
        '--windowed',                   # No console window (for GUI mode)
        '--name=lookaway',              # Output name (lowercase for Linux convention)
        '--hidden-import=pystray',      # System tray support
        '--hidden-import=PIL',          # Image support
        '--hidden-import=plyer',        # Notifications
        '--hidden-import=plyer.platforms', # Plyer platform specific modules
        '--hidden-import=plyer.platforms.linux', # Plyer Linux platform
        '--hidden-import=tkinter',      # GUI support
        '--hidden-import=smtplib',      # Email support
        '--hidden-import=ssl',          # SSL/TLS support
        '--hidden-import=email',        # Email utilities
        '--hidden-import=email.mime',   # Email MIME support
        '--hidden-import=email.mime.text', # Email text MIME
        '--hidden-import=email.mime.multipart', # Email multipart MIME
        '--hidden-import=telegram',     # Telegram bot support
        '--hidden-import=telegram.ext', # Telegram bot extensions
        '--hidden-import=httpx',        # HTTP client for telegram
        '--hidden-import=asyncio',      # Async support
        '--hidden-import=logging',      # Logging support
        '--hidden-import=abc',          # Abstract base classes
        '--hidden-import=typing',       # Type hints
        '--hidden-import=platform',     # Platform detection
        '--hidden-import=json',         # JSON support
        '--hidden-import=threading',    # Threading support
        '--hidden-import=time',         # Time utilities
        '--hidden-import=datetime',     # Date/time utilities
        '--hidden-import=pathlib',      # Path utilities
        '--hidden-import=subprocess',   # Process management
        '--hidden-import=getpass',      # Password input
        '--hidden-import=os',           # Operating system interface
        '--hidden-import=sys',          # System-specific parameters
        '--hidden-import=signal',       # Signal handling
        '--hidden-import=argparse',     # Argument parsing
        '--hidden-import=random',       # Random numbers
        '--collect-all=pystray',        # Collect all pystray dependencies
        '--collect-all=plyer',          # Collect all plyer dependencies
        '--collect-all=telegram',       # Collect all telegram dependencies
        '--collect-all=tkinter',        # Collect all tkinter components
        '--add-data=src:src',           # Include src directory (Linux syntax)
        '--add-data=config:config',     # Include config directory (Linux syntax)
        str(main_py)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            exe_path = dist_dir / "lookaway"
            if exe_path.exists():
                print(f"SUCCESS: Successfully built: {exe_path}")
                print(f"File size: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
                
                # Make sure it's executable
                exe_path.chmod(0o755)
                
                return True
            else:
                print("ERROR: Build completed but executable file not found!")
                return False
        else:
            print("ERROR: PyInstaller failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"ERROR: Error running PyInstaller: {e}")
        return False

def test_linux_exe():
    """Test the built executable."""
    project_root = Path(__file__).parent.parent
    exe_path = project_root / "dist" / "lookaway"
    
    if not exe_path.exists():
        print("ERROR: lookaway executable not found for testing!")
        return False
    
    print("Testing lookaway executable...")
    
    try:
        # Test with --help flag
        result = subprocess.run([str(exe_path), '--help'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("SUCCESS: lookaway executable responds to --help")
            return True
        else:
            print(f"ERROR: lookaway executable test failed (exit code: {result.returncode})")
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("ERROR: lookaway executable test timed out")
        return False
    except Exception as e:
        print(f"ERROR: Error testing lookaway executable: {e}")
        return False

def check_linux_dependencies():
    """Check for Linux-specific dependencies."""
    print("Checking Linux dependencies...")
    
    # Check for required system packages
    missing_packages = []
    
    # Check for tkinter
    try:
        import tkinter
        print("✓ tkinter is available")
    except ImportError:
        print("✗ tkinter is missing")
        missing_packages.append("python3-tk")
    
    # Check for notification support
    try:
        result = subprocess.run(['which', 'notify-send'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ notify-send is available")
        else:
            print("✗ notify-send is missing (desktop notifications may not work)")
            missing_packages.append("libnotify-bin")
    except Exception:
        print("✗ Cannot check notify-send")
    
    # Check for system tray support (optional)
    desktop_env = os.environ.get('DESKTOP_SESSION', '').lower()
    if desktop_env:
        print(f"✓ Desktop environment detected: {desktop_env}")
    else:
        print("? Desktop environment not detected")
    
    if missing_packages:
        print("\nMissing packages detected:")
        print("Ubuntu/Debian: sudo apt-get install " + " ".join(missing_packages))
        print("Fedora: sudo dnf install " + " ".join(missing_packages).replace('python3-tk', 'tkinter').replace('libnotify-bin', 'libnotify'))
        print("Arch: sudo pacman -S " + " ".join(missing_packages).replace('python3-tk', 'tk').replace('libnotify-bin', 'libnotify'))
        return False
    
    return True

def main():
    """Main build process for Linux."""
    print("=" * 60)
    print("Building LookAway Application for Linux")
    print("=" * 60)
    
    # Check platform
    if not sys.platform.startswith('linux'):
        print(f"Warning: This script is designed for Linux. Current platform: {sys.platform}")
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            return False
    
    # Check dependencies
    if not check_linux_dependencies():
        print("\nSome dependencies are missing. Install them and try again.")
        return False
    
    # Check for virtual environment or try to use one
    venv_python = None
    venv_paths = [
        os.path.expanduser("~/lookaway_build_env/bin/python3"),
        os.path.expanduser("~/lookaway_build_env/bin/python"),
        os.path.join(os.path.dirname(__file__), "..", "venv_linux", "bin", "python3"),
        os.path.join(os.path.dirname(__file__), "..", ".venv", "bin", "python3")
    ]
    
    for venv_path in venv_paths:
        if os.path.exists(venv_path):
            try:
                # Test if PyInstaller is available in this venv
                result = subprocess.run([venv_path, '-m', 'PyInstaller', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    venv_python = venv_path
                    print(f"SUCCESS: Using virtual environment Python at {venv_python}")
                    print(f"PyInstaller version: {result.stdout.strip()}")
                    break
            except Exception:
                continue
    
    if not venv_python:
        # Fall back to system Python but warn about externally-managed-environment issue
        print("WARNING: No virtual environment with PyInstaller found.")
        print("This may fail on externally-managed Python environments.")
        print("Consider creating a virtual environment:")
        print("  python3 -m venv ~/lookaway_build_env")
        print("  source ~/lookaway_build_env/bin/activate")
        print("  pip install pyinstaller")
        
        try:
            subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                          capture_output=True, check=True)
            print("SUCCESS: PyInstaller is available in system Python")
            venv_python = sys.executable
        except subprocess.CalledProcessError:
            print("ERROR: PyInstaller not found! Cannot proceed without virtual environment.")
            print("Please set up a virtual environment with PyInstaller installed.")
            return False
    
    # Build the application
    if build_linux_app(venv_python):
        print("\n" + "=" * 60)
        print("Testing built executable...")
        print("=" * 60)
        
        if test_linux_exe():
            print("\nSUCCESS: Build completed successfully!")
            project_root = Path(__file__).parent.parent
            exe_path = project_root / "dist" / "lookaway"
            print(f"Executable location: {exe_path}")
            
            # Show system info
            print(f"\nSystem information:")
            print(f"Platform: {sys.platform}")
            print(f"Architecture: {os.uname().machine if hasattr(os, 'uname') else 'unknown'}")
            print(f"Python version: {sys.version}")
            
            # Show usage instructions
            print(f"\nUsage:")
            print(f"  {exe_path} --help")
            print(f"  {exe_path} setup")
            print(f"  {exe_path} start")
            
        else:
            print("\nERROR: Build completed but executable test failed!")
            return False
    else:
        print("\nERROR: Build failed!")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)