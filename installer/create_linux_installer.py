#!/usr/bin/env python3
"""
Linux Resource Embedder - Creates installer with actual application files.
This embeds the lookaway executable and other necessary files into the installer.
"""

import os
import sys
import base64
import gzip
from pathlib import Path

def get_app_files():
    """Get the application files to embed."""
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
    
    # README
    readme_file = project_root / "README.md"
    if readme_file.exists():
        with open(readme_file, 'r', encoding='utf-8') as f:
            files_to_embed['README.txt'] = f.read()
        print(f"Added README.md")
    
    # Scripts
    scripts_dir = project_root / "scripts"
    if scripts_dir.exists():
        for script_file in scripts_dir.glob("*.sh"):
            with open(script_file, 'r', encoding='utf-8') as f:
                files_to_embed[f'scripts/{script_file.name}'] = f.read()
            print(f"Added script: {script_file.name}")
    
    return files_to_embed

def create_installer_with_files(output_file="linux_installer_with_files.py"):
    """Create installer file with embedded files."""
    
    # Get application files
    files_data = get_app_files()
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
    embedded_files_code += "        \"\"\"Get embedded application data\"\"\"\n"
    embedded_files_code += "        import base64\n"
    embedded_files_code += "        import gzip\n"
    embedded_files_code += "        \n"
    embedded_files_code += "        files = {\n"
    
    for file_path, file_data in files_data.items():
        if file_path == 'lookaway':
            # Special handling for compressed binary data - keep as base64 string
            embedded_files_code += f"            '{file_path}': '''{file_data}''',\n"
        else:
            # Text files - escape properly
            escaped_data = file_data.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
            embedded_files_code += f"            '{file_path}': '''{escaped_data}''',\n"
    
    embedded_files_code += "        }\n"
    embedded_files_code += "        \n"
    embedded_files_code += "        # Decompress the exe if it's compressed\n"
    embedded_files_code += "        if 'lookaway' in files and isinstance(files['lookaway'], str):\n"
    embedded_files_code += "            # First base64 decode, then gzip decompress\n"
    embedded_files_code += "            compressed_data = base64.b64decode(files['lookaway'])\n"
    embedded_files_code += "            files['lookaway'] = gzip.decompress(compressed_data)\n"
    embedded_files_code += "        \n"
    embedded_files_code += "        return files"
    
    # Find and replace the placeholder function
    placeholder_start = template_content.find('    def get_embedded_app_data(self):')
    if placeholder_start == -1:
        print("ERROR: Could not find placeholder function in template!")
        return False
    
    # Find the end of the function (look for the next function or class definition)
    lines = template_content[placeholder_start:].split('\n')
    function_end = 1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
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
    
    print(f"Created installer with embedded files: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
    
    return True

def main():
    """Main execution."""
    print("=" * 60)
    print("Creating Linux Installer with Embedded Files")
    print("=" * 60)
    
    success = create_installer_with_files()
    
    if success:
        print("\nSUCCESS: Linux installer with embedded files created successfully!")
        print("\nNext steps:")
        print("1. Build the installer: python -m PyInstaller --onefile linux_installer_with_files.py")
        print("2. Test the resulting executable")
    else:
        print("\nERROR: Failed to create installer with embedded files!")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)