#!/usr/bin/env python3
"""
Build script for FreePBX Popup Client.
Handles installation of dependencies and packaging of the application.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command and print output"""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    
    # Install requirements from requirements.txt
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Ensure PyInstaller is installed
    run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    print("Dependencies installed successfully.")

def create_icns_file():
    """Create .icns file from .png for macOS app icon"""
    if platform.system() != 'Darwin':
        print("Skipping .icns creation on non-macOS platform.")
        return
    
    print("Creating .icns file from icon.png...")
    
    # Check if icon.png exists
    icon_path = Path("resources/icon.png")
    if not icon_path.exists():
        print("Error: resources/icon.png not found.")
        return
    
    # Create temporary iconset directory
    iconset_path = Path("resources/icon.iconset")
    if iconset_path.exists():
        shutil.rmtree(iconset_path)
    iconset_path.mkdir(exist_ok=True)
    
    # Generate different icon sizes
    icon_sizes = [16, 32, 64, 128, 256, 512, 1024]
    for size in icon_sizes:
        run_command(["sips", "-z", str(size), str(size), str(icon_path), "--out", 
                    f"{iconset_path}/icon_{size}x{size}.png"], check=False)
        # Create 2x versions
        if size <= 512:
            run_command(["sips", "-z", str(size*2), str(size*2), str(icon_path), "--out", 
                        f"{iconset_path}/icon_{size}x{size}@2x.png"], check=False)
    
    # Convert iconset to icns
    run_command(["iconutil", "-c", "icns", str(iconset_path), "-o", "resources/icon.icns"], check=False)
    
    # Clean up
    shutil.rmtree(iconset_path)
    
    print("Icon created successfully.")

def build_app():
    """Build the application using PyInstaller"""
    print("Building application...")
    
    # Run PyInstaller with the spec file
    run_command(["pyinstaller", "--clean", "freepbx_popup.spec"])
    
    print("Application built successfully.")

def package_app():
    """Package the application for distribution"""
    print("Packaging application...")
    
    # Create a DMG file
    app_path = "dist/FreePBX Popup.app"
    dmg_path = "dist/FreePBX_Popup_Installer.dmg"
    
    if platform.system() == 'Darwin':
        # Create DMG
        run_command([
            "hdiutil", "create", "-volname", "FreePBX Popup", 
            "-srcfolder", app_path, "-ov", "-format", "UDZO", dmg_path
        ], check=False)
        
        print(f"DMG created at {dmg_path}")
    else:
        print("Skipping DMG creation on non-macOS platform.")
    
    print("Packaging completed.")

def main():
    """Main function"""
    print("Starting build process for FreePBX Popup Client...")
    
    # Install dependencies
    install_dependencies()
    
    # Create .icns file
    create_icns_file()
    
    # Build the application
    build_app()
    
    # Package the application
    package_app()
    
    print("Build process completed successfully.")
    print("You can find the application in the 'dist' directory.")

if __name__ == "__main__":
    main()
