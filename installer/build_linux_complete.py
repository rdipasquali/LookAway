#!/usr/bin/env python3
"""
Complete Linux Build Script for LookAway Project
Builds both the main Linux application and the Linux installer.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Main build process for Linux."""
    print("=" * 60)
    print("LookAway Complete Linux Build Process")
    print("=" * 60)
    
    # Get directories
    installer_dir = Path(__file__).parent
    project_root = installer_dir.parent
    dist_dir = project_root / "dist"
    
    print(f"Project root: {project_root}")
    print(f"Installer directory: {installer_dir}")
    print(f"Distribution directory: {dist_dir}")
    
    # Check for virtual environment
    venv_python = Path.home() / "lookaway_build_env" / "bin" / "python3"
    if venv_python.exists():
        print(f"SUCCESS: Using virtual environment Python at {venv_python}")
        python_executable = str(venv_python)
    else:
        print("WARNING: Virtual environment not found, using system Python")
        print("This may fail due to externally-managed-environment restrictions")
        python_executable = sys.executable
    
    # Ensure we're in the installer directory
    os.chdir(installer_dir)
    
    try:
        # Step 1: Build the main LookAway Linux application
        print(f"\n{'='*40}")
        print("Step 1: Building lookaway executable for Linux")
        print(f"{'='*40}")
        
        result = subprocess.run([
            python_executable, "build_linux_app.py"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("ERROR: Failed to build lookaway executable")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            return False
        
        print("SUCCESS: lookaway executable built successfully")
        
        # Step 2: Create installer with embedded files
        print(f"\n{'='*40}")
        print("Step 2: Creating installer with embedded files")
        print(f"{'='*40}")
        
        result = subprocess.run([
            python_executable, "create_linux_installer.py"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("ERROR: Failed to create installer with embedded files")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            return False
        
        print("SUCCESS: Linux installer with embedded files created")
        
        # Step 3: Build the unified Linux installer executable
        print(f"\n{'='*40}")
        print("Step 3: Building unified Linux installer executable")
        print(f"{'='*40}")
        
        result = subprocess.run([
            python_executable, "-m", "PyInstaller", 
            "--onefile", 
            "--name=lookaway-installer-linux",
            "--hidden-import=tkinter", 
            "--collect-submodules=tkinter",
            "--hidden-import=subprocess", 
            "--hidden-import=shutil",
            "--hidden-import=gzip", 
            "--hidden-import=base64",
            "--hidden-import=json", 
            "--hidden-import=pathlib",
            "--hidden-import=threading",
            "--add-data=../LICENSE:.",
            "linux_installer_with_files.py"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("ERROR: Failed to build Linux installer executable")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            return False
        
        print("SUCCESS: Linux installer executable built successfully")
        
        # Step 4: Move files to correct locations and clean up
        print(f"\n{'='*40}")
        print("Step 4: Organizing files")
        print(f"{'='*40}")
        
        # Ensure dist directory exists
        dist_dir.mkdir(exist_ok=True)
        
        # Move Linux installer to main dist
        linux_installer_exe = installer_dir / "dist" / "lookaway-installer-linux"
        if linux_installer_exe.exists():
            shutil.move(str(linux_installer_exe), str(dist_dir / "lookaway-installer-linux"))
            print("SUCCESS: Moved Linux installer to main dist directory")
        
        # Clean up installer directory
        cleanup_items = [
            installer_dir / "dist",
            installer_dir / "build",
            installer_dir / "linux_installer_with_files.py"
        ]
        
        for item in cleanup_items:
            if item.exists():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        
        # Remove spec files
        for spec_file in installer_dir.glob("*.spec"):
            spec_file.unlink()
        
        print("SUCCESS: Cleaned up build artifacts")
        
        # Step 5: Show results
        print(f"\n{'='*60}")
        print("Linux Build Complete! 🐧")
        print(f"{'='*60}")
        
        print(f"\nFinal Linux files in {dist_dir}:")
        if dist_dir.exists():
            for file in sorted(dist_dir.glob("*linux*")):
                size_mb = file.stat().st_size / 1024 / 1024
                print(f"  📄 {file.name}: {size_mb:.1f} MB")
            
            # Also show the main executable
            lookaway_exe = dist_dir / "lookaway"
            if lookaway_exe.exists():
                size_mb = lookaway_exe.stat().st_size / 1024 / 1024
                print(f"  📄 {lookaway_exe.name}: {size_mb:.1f} MB")
        
        print(f"\nInstaller directory now contains:")
        for file in sorted(installer_dir.iterdir()):
            if file.is_file() and not file.name.startswith('.'):
                print(f"  📄 {file.name}")
        
        print(f"\n✅ Ready for Linux distribution!")
        print(f"   Main Linux application: {dist_dir / 'lookaway'}")
        print(f"   Linux installer: {dist_dir / 'lookaway-installer-linux'}")
        
        print(f"\n📋 Usage on Linux systems:")
        print(f"   ./lookaway --help")
        print(f"   ./lookaway-installer-linux")
        
        print(f"\n⚠️  Note: These files need to be tested on actual Linux systems")
        print(f"   The installer includes dependency checks for:")
        print(f"   • tkinter (python3-tk)")
        print(f"   • notify-send (libnotify-bin)")
        print(f"   • Desktop environment detection")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Linux build failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)