#!/usr/bin/env python3
"""
Cross-Platform Build Script for LookAway
Builds installers for both Windows and Linux platforms.
"""

import os
import sys
import subprocess
from pathlib import Path

def detect_platform():
    """Detect the current platform."""
    if sys.platform.startswith('win'):
        return 'windows'
    elif sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform.startswith('darwin'):
        return 'macos'
    else:
        return 'unknown'

def build_windows():
    """Build Windows version."""
    print("=" * 60)
    print("Building Windows Version")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, "build_complete.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("SUCCESS: Windows build completed")
            return True
        else:
            print("ERROR: Windows build failed")
            print("STDERR:", result.stderr)
            return False
    except Exception as e:
        print(f"ERROR: Windows build exception: {e}")
        return False

def build_linux():
    """Build Linux version."""
    print("=" * 60)
    print("Building Linux Version")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, "build_linux_complete.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("SUCCESS: Linux build completed")
            return True
        else:
            print("ERROR: Linux build failed")
            print("STDERR:", result.stderr)
            return False
    except Exception as e:
        print(f"ERROR: Linux build exception: {e}")
        return False

def show_final_results():
    """Show final build results."""
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    
    print("\n" + "=" * 60)
    print("FINAL BUILD RESULTS")
    print("=" * 60)
    
    if not dist_dir.exists():
        print("No distribution directory found!")
        return
    
    windows_files = []
    linux_files = []
    other_files = []
    
    for file in dist_dir.iterdir():
        if file.is_file():
            size_mb = file.stat().st_size / 1024 / 1024
            file_info = f"{file.name}: {size_mb:.1f} MB"
            
            if 'windows' in file.name.lower() or file.suffix == '.exe':
                windows_files.append(file_info)
            elif 'linux' in file.name.lower() or file.name == 'lookaway':
                linux_files.append(file_info)
            else:
                other_files.append(file_info)
    
    if windows_files:
        print("\n🪟 Windows Files:")
        for file_info in windows_files:
            print(f"  📄 {file_info}")
    
    if linux_files:
        print("\n🐧 Linux Files:")
        for file_info in linux_files:
            print(f"  📄 {file_info}")
    
    if other_files:
        print("\n📄 Other Files:")
        for file_info in other_files:
            print(f"  📄 {file_info}")
    
    total_size = sum(f.stat().st_size for f in dist_dir.iterdir() if f.is_file())
    print(f"\nTotal distribution size: {total_size / 1024 / 1024:.1f} MB")

def main():
    """Main cross-platform build process."""
    print("=" * 70)
    print("LookAway Cross-Platform Build System")
    print("=" * 70)
    
    current_platform = detect_platform()
    print(f"Current platform: {current_platform}")
    
    installer_dir = Path(__file__).parent
    os.chdir(installer_dir)
    
    build_windows_success = False
    build_linux_success = False
    
    # Ask user what to build
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
    else:
        print("\nWhat would you like to build?")
        print("1. Windows only")
        print("2. Linux only") 
        print("3. Both platforms")
        print("4. Current platform only")
        
        choice = input("Enter choice (1-4) or platform name: ").strip()
        
        if choice == '1' or choice.lower() == 'windows':
            target = 'windows'
        elif choice == '2' or choice.lower() == 'linux':
            target = 'linux'
        elif choice == '3' or choice.lower() == 'both':
            target = 'both'
        elif choice == '4' or choice.lower() == 'current':
            target = current_platform
        else:
            target = 'both'  # Default
    
    print(f"\nBuilding for: {target}")
    
    # Build Windows
    if target in ['windows', 'both'] or (target == 'current' and current_platform == 'windows'):
        if current_platform != 'windows':
            print("\n⚠️  Warning: Building Windows version on non-Windows platform")
            print("   This may not work properly. Consider using a Windows VM or CI/CD.")
        
        build_windows_success = build_windows()
    
    # Build Linux  
    if target in ['linux', 'both'] or (target == 'current' and current_platform == 'linux'):
        if current_platform != 'linux':
            print("\n⚠️  Warning: Building Linux version on non-Linux platform")
            print("   This may not work properly. Consider using a Linux VM or CI/CD.")
        
        build_linux_success = build_linux()
    
    # Show results
    show_final_results()
    
    # Summary
    print("\n" + "=" * 60)
    print("BUILD SUMMARY")
    print("=" * 60)
    
    if target in ['windows', 'both'] or (target == 'current' and current_platform == 'windows'):
        status = "✅ SUCCESS" if build_windows_success else "❌ FAILED"
        print(f"Windows build: {status}")
    
    if target in ['linux', 'both'] or (target == 'current' and current_platform == 'linux'):
        status = "✅ SUCCESS" if build_linux_success else "❌ FAILED"
        print(f"Linux build: {status}")
    
    # Overall success
    if target == 'both':
        overall_success = build_windows_success and build_linux_success
    elif target == 'windows':
        overall_success = build_windows_success
    elif target == 'linux':
        overall_success = build_linux_success
    elif target == 'current':
        if current_platform == 'windows':
            overall_success = build_windows_success
        elif current_platform == 'linux':
            overall_success = build_linux_success
        else:
            overall_success = False
    else:
        overall_success = False
    
    if overall_success:
        print("\n🎉 All builds completed successfully!")
        
        print("\n📦 Distribution files are ready in the 'dist' directory")
        print("   You can now distribute these installers to users")
        
        if build_windows_success:
            print("\n🪟 Windows users can run:")
            print("   • LookAway-Installer.exe (full installer with setup wizard)")
            print("   • LookAway.exe (standalone application)")
        
        if build_linux_success:
            print("\n🐧 Linux users can run:")
            print("   • ./lookaway-installer-linux (full installer with setup wizard)")
            print("   • ./lookaway (standalone application)")
            print("   Note: May need to install dependencies like python3-tk")
        
    else:
        print("\n❌ Some builds failed. Check the errors above.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)