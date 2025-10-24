#!/usr/bin/env python3
"""
Build script for LookAway application executable.
Creates LookAway.exe using PyInstaller with proper configuration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_main_app():
    """Build the main LookAway application using PyInstaller."""
    print("Building LookAway.exe...")
    
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
    
    # Build command with proper options for Windows compatibility
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',                    # Single executable file
        '--windowed',                   # No console window
        '--name=LookAway',              # Output name
        '--hidden-import=pystray',      # System tray support
        '--hidden-import=PIL',          # Image support
        '--hidden-import=plyer',        # Notifications
        '--hidden-import=win10toast',   # Windows toast notifications
        '--hidden-import=tkinter',      # GUI support
        '--hidden-import=smtplib',      # Email support
        '--hidden-import=ssl',          # SSL/TLS support
        '--hidden-import=email',        # Email utilities
        '--hidden-import=email.mime',   # Email MIME support
        '--hidden-import=email.mime.text', # Email text MIME
        '--hidden-import=email.mime.multipart', # Email multipart MIME
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
        '--hidden-import=winreg',       # Windows registry
        '--hidden-import=subprocess',   # Process management
        '--hidden-import=getpass',      # Password input
        '--hidden-import=os',           # Operating system interface
        '--hidden-import=sys',          # System-specific parameters
        '--hidden-import=signal',       # Signal handling
        '--hidden-import=argparse',     # Argument parsing
        '--hidden-import=random',       # Random numbers
        '--collect-all=pystray',        # Collect all pystray dependencies
        '--collect-all=plyer',          # Collect all plyer dependencies
        '--collect-all=tkinter',        # Collect all tkinter components
        '--add-data=src;src',           # Include src directory
        '--add-data=config;config',     # Include config directory
        str(main_py)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            exe_path = dist_dir / "LookAway.exe"
            if exe_path.exists():
                print(f"SUCCESS: Successfully built: {exe_path}")
                print(f"File size: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
                return True
            else:
                print("ERROR: Build completed but exe file not found!")
                return False
        else:
            print("ERROR: PyInstaller failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running PyInstaller: {e}")
        return False

def test_exe():
    """Test the built executable."""
    project_root = Path(__file__).parent.parent
    exe_path = project_root / "dist" / "LookAway.exe"
    
    if not exe_path.exists():
        print("❌ LookAway.exe not found for testing!")
        return False
    
    print("Testing LookAway.exe...")
    
    try:
        # Test with --help flag
        result = subprocess.run([str(exe_path), '--help'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("SUCCESS: LookAway.exe responds to --help")
            return True
        else:
            print(f"ERROR: LookAway.exe test failed (exit code: {result.returncode})")
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("ERROR: LookAway.exe test timed out")
        return False
    except Exception as e:
        print(f"ERROR: Error testing LookAway.exe: {e}")
        return False

def main():
    """Main build process."""
    print("=" * 60)
    print("Building LookAway Application")
    print("=" * 60)
    
    # Check if PyInstaller is available
    try:
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                      capture_output=True, check=True)
        print("SUCCESS: PyInstaller is available")
    except subprocess.CalledProcessError:
        print("❌ PyInstaller not found! Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    # Build the application
    if build_main_app():
        print("\n" + "=" * 60)
        print("Testing built executable...")
        print("=" * 60)
        
        if test_exe():
            print("\nSUCCESS: Build completed successfully!")
            project_root = Path(__file__).parent.parent
            exe_path = project_root / "dist" / "LookAway.exe"
            print(f"Executable location: {exe_path}")
            
            # Show architecture info
            print(f"\nSystem architecture: {os.environ.get('PROCESSOR_ARCHITECTURE', 'Unknown')}")
            print(f"Python architecture: {sys.maxsize > 2**32 and '64-bit' or '32-bit'}")
            
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