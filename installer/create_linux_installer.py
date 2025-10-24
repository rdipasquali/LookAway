#!/usr/bin/env python3
"""
Linux Installer Creation Script
Creates a Linux installer with embedded files similar to the Windows version.
"""

import os
import gzip
import base64
from pathlib import Path

def get_linux_app_files():
    """Get application files for Linux installer."""
    project_root = Path(__file__).parent.parent
    files_to_embed = {}
    
    # Main executable
    lookaway_exe = project_root / "dist" / "lookaway"
    if lookaway_exe.exists():
        print(f"Found lookaway executable ({lookaway_exe.stat().st_size / 1024 / 1024:.2f} MB)")
        with open(lookaway_exe, 'rb') as f:
            exe_data = f.read()
            # Compress the exe data
            compressed = gzip.compress(exe_data)
            encoded = base64.b64encode(compressed).decode('ascii')
            files_to_embed['lookaway'] = encoded
            print(f"   Compressed to {len(compressed) / 1024 / 1024:.2f} MB")
            print(f"   Base64 encoded to {len(encoded) / 1024 / 1024:.2f} MB")
    else:
        print("ERROR: lookaway executable not found! Run build_linux_app.py first.")
        return None
    
    # Configuration files
    config_dir = project_root / "config"
    if config_dir.exists():
        for config_file in config_dir.glob("*.json"):
            with open(config_file, 'r', encoding='utf-8') as f:
                files_to_embed[f'config/{config_file.name}'] = f.read()
            print(f"Added config: {config_file.name}")
    
    # License file
    license_file = project_root / "LICENSE"
    if license_file.exists():
        with open(license_file, 'r', encoding='utf-8') as f:
            files_to_embed['LICENSE'] = f.read()
        print(f"Added LICENSE")
    
    # README file
    readme_file = project_root / "README.md"
    if readme_file.exists():
        with open(readme_file, 'r', encoding='utf-8') as f:
            files_to_embed['README.md'] = f.read()
        print(f"Added README.md")
    
    # Linux startup scripts
    scripts_dir = project_root / "scripts"
    if scripts_dir.exists():
        for script_file in scripts_dir.glob("*linux*"):
            with open(script_file, 'r', encoding='utf-8') as f:
                files_to_embed[f'scripts/{script_file.name}'] = f.read()
            print(f"Added script: {script_file.name}")
    
    return files_to_embed

def create_linux_installer_with_files(output_file="linux_installer_with_files.py"):
    """Create Linux installer file with embedded files."""
    
    # Get application files
    files_data = get_linux_app_files()
    if files_data is None:
        return False
    
    # Read the base installer template
    installer_template = Path(__file__).parent / "installer_wizard_linux.py"
    
    if not installer_template.exists():
        print("ERROR: installer_wizard_linux.py template not found!")
        return False
    
    with open(installer_template, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Create the embedded files function
    embedded_files_code = "    def get_embedded_app_data(self):\n"
    embedded_files_code += "        \"\"\"Get embedded application data.\"\"\"\n"
    embedded_files_code += "        return {\n"
    
    for filename, data in files_data.items():
        # Escape the data properly for Python string
        escaped_data = repr(data)
        embedded_files_code += f"            {repr(filename)}: {escaped_data},\n"
    
    embedded_files_code += "        }\n"
    
    # Also update the get_license_text method with actual license
    if 'LICENSE' in files_data:
        license_method = "    def get_license_text(self):\n"
        license_method += "        \"\"\"Get license text from embedded data.\"\"\"\n"
        license_method += f"        return {repr(files_data['LICENSE'])}\n"
        
        # Replace the placeholder license method
        license_start = template_content.find('    def get_license_text(self):')
        if license_start != -1:
            # Find the end of the method
            lines = template_content[license_start:].split('\n')
            method_end = license_start
            indent_level = None
            
            for i, line in enumerate(lines):
                if i == 0:  # First line is the method definition
                    continue
                
                if line.strip() == '':  # Empty line
                    continue
                
                current_indent = len(line) - len(line.lstrip())
                
                if indent_level is None and line.strip():
                    indent_level = current_indent
                
                if line.strip() and current_indent <= 4:  # Back to class level or less
                    method_end = license_start + len('\n'.join(lines[:i]))
                    break
            else:
                # Reached end of file
                method_end = len(template_content)
            
            # Replace the method
            template_content = (template_content[:license_start] + 
                            license_method + '\n' +
                            template_content[method_end:])
    
    # Find and replace the placeholder function
    placeholder_start = template_content.find('    def get_embedded_app_data(self):')
    
    if placeholder_start == -1:
        print("ERROR: Could not find placeholder function in template!")
        return False
    
    # Find the end of the placeholder function
    lines = template_content[placeholder_start:].split('\n')
    function_end = len(lines)
    
    for i, line in enumerate(lines[1:], 1):  # Skip the function definition line
        if line.strip() and not line.startswith('        ') and not line.startswith('\t\t'):
            # Found a line that's not indented as part of the function
            function_end = i
            break
        elif line.strip().startswith('def ') and not line.startswith('        '):
            function_end = i
            break
    
    placeholder_end = placeholder_start + len('\n'.join(lines[:function_end]))
    
    # Replace the placeholder function
    new_content = (template_content[:placeholder_start] + 
                  embedded_files_code + 
                  template_content[placeholder_end:])
    
    # Write the new installer
    output_path = Path(__file__).parent / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Created Linux installer with embedded files: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
    
    return output_path

def main():
    """Main function."""
    print("=" * 60)
    print("Creating Linux Installer with Embedded Files")
    print("=" * 60)
    
    success = create_linux_installer_with_files()
    
    if success:
        print("\nSUCCESS: Linux installer with embedded files created successfully!")
        print("\nNext steps:")
        print("1. Build the installer: python -m PyInstaller --onefile linux_installer_with_files.py")
        print("2. Test the resulting executable on a Linux system")
        print("3. Distribute the installer executable")
    else:
        print("\nERROR: Failed to create Linux installer with embedded files!")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)