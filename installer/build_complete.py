#!/usr/bin/env python3
"""
Complete Build Script for LookAway Project
Builds both the main application and the installer in the correct locations.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Main build process"""
    print("=" * 60)
    print("LookAway Complete Build Process")
    print("=" * 60)
    
    # Get directories
    installer_dir = Path(__file__).parent
    project_root = installer_dir.parent
    dist_dir = project_root / "dist"
    
    print(f"Project root: {project_root}")
    print(f"Installer directory: {installer_dir}")
    print(f"Distribution directory: {dist_dir}")
    
    # Ensure we're in the installer directory
    os.chdir(installer_dir)
    
    try:
        # Step 1: Build the main LookAway application
        print(f"\n{'='*40}")
        print("Step 1: Building LookAway.exe")
        print(f"{'='*40}")
        
        result = subprocess.run([
            sys.executable, "build_app.py"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Failed to build LookAway.exe")
            print("STDERR:", result.stderr)
            return False
        
        print("✅ LookAway.exe built successfully")
        
        # Step 2: Create installer with embedded files
        print(f"\n{'='*40}")
        print("Step 2: Creating installer with embedded files")
        print(f"{'='*40}")
        
        result = subprocess.run([
            sys.executable, "create_installer.py"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Failed to create installer with embedded files")
            print("STDERR:", result.stderr)
            return False
        
        print("✅ Installer with embedded files created")
        
        # Step 3: Build the installer executable
        print(f"\n{'='*40}")
        print("Step 3: Building installer executable")
        print(f"{'='*40}")
        
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--onefile", "--windowed", 
            "--name=LookAway-Installer",
            "--hidden-import=tkinter", "--collect-submodules=tkinter",
            "--hidden-import=winreg", "--hidden-import=subprocess",
            "--hidden-import=gzip", "--hidden-import=base64",
            "windows_installer_with_files.py"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Failed to build installer executable")
            print("STDERR:", result.stderr)
            return False
        
        print("✅ Installer executable built successfully")
        
        # Step 4: Move files to correct locations and clean up
        print(f"\n{'='*40}")
        print("Step 4: Organizing files")
        print(f"{'='*40}")
        
        # Ensure dist directory exists
        dist_dir.mkdir(exist_ok=True)
        
        # Move installer to main dist
        installer_exe = installer_dir / "dist" / "LookAway-Installer.exe"
        if installer_exe.exists():
            shutil.move(str(installer_exe), str(dist_dir / "LookAway-Installer.exe"))
            print("✅ Moved installer to main dist directory")
        
        # Clean up installer directory
        cleanup_items = [
            installer_dir / "dist",
            installer_dir / "build", 
            installer_dir / "windows_installer_with_files.py"
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
        
        print("✅ Cleaned up build artifacts")
        
        # Step 5: Show results
        print(f"\n{'='*60}")
        print("Build Complete! 🎉")
        print(f"{'='*60}")
        
        print(f"\nFinal files in {dist_dir}:")
        if dist_dir.exists():
            for file in sorted(dist_dir.glob("*.exe")):
                size_mb = file.stat().st_size / 1024 / 1024
                print(f"  📄 {file.name}: {size_mb:.1f} MB")
        
        print(f"\nInstaller directory now contains:")
        for file in sorted(installer_dir.iterdir()):
            if file.is_file() and not file.name.startswith('.'):
                print(f"  📄 {file.name}")
        
        print(f"\n✅ Ready to distribute!")
        print(f"   Main application: {dist_dir / 'LookAway.exe'}")
        print(f"   Installer: {dist_dir / 'LookAway-Installer.exe'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Build failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)