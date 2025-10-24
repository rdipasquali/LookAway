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
        '--windowed',                   # No console window (for tray mode)
        '--name=LookAway',              # Output name
        # System tray and GUI support  
        '--hidden-import=pystray',
        '--hidden-import=pystray._base',
        '--hidden-import=pystray._win32', 
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=PIL.ImageFont',
        '--hidden-import=six',
        '--hidden-import=six.moves',
        '--hidden-import=tkinter',
        
        # Notification system
        '--hidden-import=plyer',
        '--hidden-import=plyer.platforms',
        '--hidden-import=plyer.platforms.win',
        '--hidden-import=plyer.platforms.win.notification',
        '--hidden-import=win10toast',
        
        # Email support
        '--hidden-import=smtplib',
        '--hidden-import=ssl',
        '--hidden-import=socket',
        '--hidden-import=base64',
        '--hidden-import=email',
        '--hidden-import=email.mime',
        '--hidden-import=email.mime.text',
        '--hidden-import=email.mime.multipart',
        
        # Telegram bot support
        '--hidden-import=telegram',
        '--hidden-import=telegram.ext',
        '--hidden-import=httpx',
        
        # Standard library modules (Python 3.14 compatibility)
        '--hidden-import=asyncio',
        '--hidden-import=logging',
        '--hidden-import=abc',
        '--hidden-import=typing',
        '--hidden-import=platform',
        '--hidden-import=json',
        '--hidden-import=threading',
        '--hidden-import=time',
        '--hidden-import=datetime',
        '--hidden-import=pathlib',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=signal',
        '--hidden-import=argparse',
        '--hidden-import=random',
        '--hidden-import=traceback',
        '--hidden-import=getpass',
        
        # Windows-specific
        '--hidden-import=winreg',
        '--hidden-import=subprocess',
        '--collect-all=pystray',        # Collect all pystray dependencies
        '--collect-all=PIL',            # Collect all PIL/Pillow dependencies
        '--collect-all=six',            # Collect all six compatibility library
        '--collect-all=plyer',          # Collect all plyer dependencies
        '--collect-all=telegram',       # Collect all telegram dependencies
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