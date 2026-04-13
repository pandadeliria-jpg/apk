#!/bin/bash
# Setup script to register APK Installer as default handler for .apk files on macOS

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_BUNDLE="$SCRIPT_DIR/APK Installer.app"

echo "=== APK File Association Setup ==="
echo

# Check if app bundle exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo "[!] APK Installer.app not found at: $APP_BUNDLE"
    exit 1
fi

echo "[*] Found APK Installer.app"

# Make sure the binary is executable
chmod +x "$APP_BUNDLE/Contents/MacOS/apkinstaller"

# Register the app with LaunchServices
echo "[*] Registering app with macOS..."
/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP_BUNDLE"

# Check if duti is installed (for setting default app)
if command -v duti &> /dev/null; then
    echo "[*] Setting APK Installer as default for .apk files..."
    duti -s com.androidcompat.apkinstaller com.android.package-archive all
else
    echo "[!] duti not installed. Installing via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install duti
        duti -s com.androidcompat.apkinstaller com.android.package-archive all
    else
        echo "[!] Homebrew not found. Please install duti manually:"
        echo "    brew install duti"
        echo
        echo "Then run: duti -s com.androidcompat.apkinstaller com.android.package-archive all"
    fi
fi

# Alternative: use Finder's default application setting
echo
echo "[*] Alternative setup method (if duti not available):"
echo "    1. Right-click any .apk file"
echo "    2. Select 'Get Info'"
echo "    3. Under 'Open with:' select 'APK Installer'"
echo "    4. Click 'Change All...' to apply to all .apk files"
echo

echo "[+] Setup complete!"
echo

# Test with a sample message
echo "You can now double-click .apk files to install them!"
