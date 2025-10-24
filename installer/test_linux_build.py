#!/usr/bin/env python3
"""
Test script to verify Linux build scripts can be imported and basic functionality works.
Since we're on Windows, this tests the syntax and basic logic without actually building.
"""

import sys
import os
from pathlib import Path

# Add installer directory to path
installer_dir = Path(__file__).parent
sys.path.insert(0, str(installer_dir))

def test_linux_imports():
    """Test that Linux build scripts can be imported."""
    print("Testing Linux build script imports...")
    
    try:
        print("  Importing installer_wizard_linux...")
        import installer_wizard_linux
        print("  ✓ installer_wizard_linux imported successfully")
    except Exception as e:
        print(f"  ✗ Error importing installer_wizard_linux: {e}")
        return False
    
    try:
        print("  Importing build_linux_app...")  
        import build_linux_app
        print("  ✓ build_linux_app imported successfully")
    except Exception as e:
        print(f"  ✗ Error importing build_linux_app: {e}")
        return False
    
    try:
        print("  Importing create_linux_installer...")
        import create_linux_installer
        print("  ✓ create_linux_installer imported successfully")
    except Exception as e:
        print(f"  ✗ Error importing create_linux_installer: {e}")
        return False
    
    try:
        print("  Importing build_linux_complete...")
        import build_linux_complete
        print("  ✓ build_linux_complete imported successfully")
    except Exception as e:
        print(f"  ✗ Error importing build_linux_complete: {e}")
        return False
    
    try:
        print("  Importing build_cross_platform...")
        import build_cross_platform
        print("  ✓ build_cross_platform imported successfully")
    except Exception as e:
        print(f"  ✗ Error importing build_cross_platform: {e}")
        return False
    
    return True

def test_linux_installer_class():
    """Test basic Linux installer class functionality."""
    print("\nTesting Linux installer class...")
    
    try:
        from installer_wizard_linux import LinuxLookAwayInstaller
        
        # Test class can be instantiated (but don't run GUI)
        print("  Testing class instantiation...")
        
        # Mock tkinter to avoid GUI startup
        import tkinter as tk
        original_mainloop = tk.Tk.mainloop
        tk.Tk.mainloop = lambda self: None  # Disable GUI mainloop
        
        try:
            installer = LinuxLookAwayInstaller()
            print("  ✓ LinuxLookAwayInstaller class instantiated successfully")
            
            # Test some basic methods
            license_text = installer.get_license_text()
            if license_text and "MIT License" in license_text:
                print("  ✓ get_license_text() works correctly")
            else:
                print("  ✗ get_license_text() returned unexpected content")
                return False
            
            embedded_data = installer.get_embedded_app_data()
            if isinstance(embedded_data, dict):
                print("  ✓ get_embedded_app_data() returns correct type")
            else:
                print("  ✗ get_embedded_app_data() returned wrong type")
                return False
            
            # Test platform detection method in build script
            from build_cross_platform import detect_platform
            platform = detect_platform()
            print(f"  ✓ Platform detection works: {platform}")
            
        finally:
            # Restore original mainloop
            tk.Tk.mainloop = original_mainloop
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error testing Linux installer class: {e}")
        return False

def test_file_structure():
    """Test that all required Linux files exist."""
    print("\nTesting Linux file structure...")
    
    required_files = [
        "installer_wizard_linux.py",
        "build_linux_app.py", 
        "create_linux_installer.py",
        "build_linux_complete.py",
        "build_cross_platform.py"
    ]
    
    missing_files = []
    for filename in required_files:
        file_path = installer_dir / filename
        if file_path.exists():
            print(f"  ✓ {filename} exists")
        else:
            print(f"  ✗ {filename} missing")
            missing_files.append(filename)
    
    if missing_files:
        print(f"  Missing files: {missing_files}")
        return False
    
    return True

def main():
    """Main test function."""
    print("=" * 60)
    print("LookAway Linux Build System Test")
    print("=" * 60)
    print(f"Running on: {sys.platform}")
    print(f"Python version: {sys.version}")
    
    if sys.platform.startswith('win'):
        print("Note: Running Linux build tests on Windows - GUI components disabled")
    
    success = True
    
    # Test file structure
    if not test_file_structure():
        success = False
    
    # Test imports
    if not test_linux_imports():
        success = False
    
    # Test installer class  
    if not test_linux_installer_class():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All Linux build system tests passed!")
        print("\nThe Linux build system should work correctly on actual Linux systems.")
        print("Required Linux dependencies:")
        print("  • python3-tk (or tkinter)")
        print("  • libnotify-bin (for desktop notifications)")
        print("  • X11 or Wayland (for GUI)")
        
        print("\nTo build on Linux:")
        print("  python build_linux_complete.py")
        print("  python build_cross_platform.py")
    else:
        print("❌ Some Linux build system tests failed!")
        print("Check the errors above and fix the issues.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)