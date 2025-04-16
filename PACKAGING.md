# Packaging FreePBX Popup Client for macOS

This document describes how to package the FreePBX Popup Client for macOS.

## Requirements

- macOS 10.14 or later
- Python 3.7 or later
- PyInstaller
- Additional dependencies listed in `requirements.txt`

## Building the Application

### Automatic Build

The easiest way to build the application is to use the provided build script:

```bash
./build.sh
```

This will:
1. Install all required dependencies
2. Create the necessary icon files
3. Build the application using PyInstaller
4. Package the application into a DMG file

### Manual Build

If you prefer to build the application manually, follow these steps:

1. Install the required dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

2. Create the .icns file from the icon.png (macOS only):
   ```bash
   # Create iconset directory
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
   ```

3. Build the application using PyInstaller:
   ```bash
   pyinstaller --clean freepbx_popup.spec
   ```

4. Create a DMG file (macOS only):
   ```bash
   hdiutil create -volname "FreePBX Popup" -srcfolder "dist/FreePBX Popup.app" -ov -format UDZO dist/FreePBX_Popup_Installer.dmg
   ```

## Output

After the build process completes, you will find:

- The application bundle at `dist/FreePBX Popup.app`
- The installer DMG at `dist/FreePBX_Popup_Installer.dmg` (macOS only)

## Icon Requirements

If you need to replace the icons, please provide:

- `resources/icon.png`: Main application icon (1024x1024 pixels recommended)
- `resources/menu_bar_icon.png`: Menu bar icon (22x22 pixels recommended, white color for dark mode compatibility)

## Troubleshooting

### Missing Dependencies

If you encounter errors about missing dependencies, try installing them manually:

```bash
pip3 install <package_name>
```

### Code Signing

For distribution outside of development, you may want to sign the application:

```bash
codesign --force --deep --sign "Developer ID Application: Your Name (XXXXXXXXXX)" "dist/FreePBX Popup.app"
```

### Notarization

For distribution through the internet, you may need to notarize the application:

```bash
xcrun altool --notarize-app --primary-bundle-id "com.parcopang.freepbxpopup" --username "your.apple.id@example.com" --password "app-specific-password" --file "dist/FreePBX_Popup_Installer.dmg"
```
