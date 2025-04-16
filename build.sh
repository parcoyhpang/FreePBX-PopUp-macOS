#!/bin/bash
# Build script for FreePBX Popup Client

echo "Building FreePBX Popup Client..."

# Install required packages
pip3 install -r requirements.txt

# Create icon.icns if it doesn't exist
if [ ! -f "resources/icon.icns" ]; then
    echo "Creating icon.icns..."
    mkdir -p resources/icon.iconset
    
    # Generate different icon sizes
    sips -z 16 16 resources/icon.png --out resources/icon.iconset/icon_16x16.png
    sips -z 32 32 resources/icon.png --out resources/icon.iconset/icon_16x16@2x.png
    sips -z 32 32 resources/icon.png --out resources/icon.iconset/icon_32x32.png
    sips -z 64 64 resources/icon.png --out resources/icon.iconset/icon_32x32@2x.png
    sips -z 128 128 resources/icon.png --out resources/icon.iconset/icon_128x128.png
    sips -z 256 256 resources/icon.png --out resources/icon.iconset/icon_128x128@2x.png
    sips -z 256 256 resources/icon.png --out resources/icon.iconset/icon_256x256.png
    sips -z 512 512 resources/icon.png --out resources/icon.iconset/icon_256x256@2x.png
    sips -z 512 512 resources/icon.png --out resources/icon.iconset/icon_512x512.png
    sips -z 1024 1024 resources/icon.png --out resources/icon.iconset/icon_512x512@2x.png
    
    # Convert iconset to icns
    iconutil -c icns resources/icon.iconset -o resources/icon.icns
    
    # Clean up
    rm -rf resources/icon.iconset
fi

# Build the application
pyinstaller --clean freepbx_popup.spec

# Create DMG
if [ -d "dist/FreePBX Popup.app" ]; then
    echo "Creating DMG..."
    hdiutil create -volname "FreePBX Popup" -srcfolder "dist/FreePBX Popup.app" -ov -format UDZO dist/FreePBX_Popup_Installer.dmg
    echo "DMG created at dist/FreePBX_Popup_Installer.dmg"
fi

echo "Build completed!"
