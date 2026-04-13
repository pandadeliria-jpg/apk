#!/bin/bash
# Setup script to make Terminal the default handler for .apk files
# This creates a .app bundle that just opens Terminal and runs apk install

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BIN_DIR="$SCRIPT_DIR/bin"
APK_CMD="$BIN_DIR/apk"

echo "════════════════════════════════════════════════════════════"
echo "  📱 APK Terminal Handler Setup"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if apk command exists
if [ ! -f "$APK_CMD" ]; then
    echo "❌ apk command not found at: $APK_CMD"
    exit 1
fi

# Make sure it's executable
chmod +x "$APK_CMD"

# Create alias for easy access
echo "🔧 Setting up command alias..."

# Add to shell config
SHELL_CONFIG=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
fi

if [ -n "$SHELL_CONFIG" ]; then
    # Check if already added
    if ! grep -q "alias apk=" "$SHELL_CONFIG" 2>/dev/null; then
        echo "" >> "$SHELL_CONFIG"
        echo "# APK Installer alias" >> "$SHELL_CONFIG"
        echo "alias apk='$APK_CMD'" >> "$SHELL_CONFIG"
        echo "✅ Added alias to $(basename "$SHELL_CONFIG")"
    else
        echo "ℹ️  Alias already exists in $(basename "$SHELL_CONFIG")"
    fi
fi

# Add to PATH via symlink
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

if [ ! -L "$LOCAL_BIN/apk" ]; then
    ln -s "$APK_CMD" "$LOCAL_BIN/apk"
    echo "✅ Created symlink in ~/.local/bin/"
fi

# Add to PATH if not already there
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo ""
    echo "⚠️  ~/.local/bin is not in your PATH"
    echo "   Add this to your shell config:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# Setup as default handler
echo ""
echo "🔧 Setting Terminal as default handler for .apk files..."

# Create a minimal app bundle that opens Terminal
APP_DIR="$SCRIPT_DIR/APK-Terminal.app"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create the launcher
cat > "$APP_DIR/Contents/MacOS/apk-terminal" << 'EOF'
#!/bin/bash
# Terminal launcher for APK files
APK_FILE="$1"

if [ -z "$APK_FILE" ] || [ ! -f "$APK_FILE" ]; then
    # Try Finder selection
    APK_FILE=$(osascript <<'OSA' 2>/dev/null
        tell application "Finder"
            try
                set theSelection to selection
                if (count theSelection) > 0 then
                    return POSIX path of (item 1 of theSelection as alias)
                end if
            on error
            end try
        end tell
        return ""
OSA
    )
fi

COMPAT_DIR="/Users/danuta/robloxgen/android_compat"
APK_CMD="$COMPAT_DIR/bin/apk"

osascript <<OSA
tell application "Terminal"
    activate
    if "$APK_FILE" != "" ]; then
        do script "\"$APK_CMD\" install \"$APK_FILE\""
    else
        do script "\"$APK_CMD\""
    fi
    set custom title of front window to "📱 APK Installer"
end tell
OSA
EOF

chmod +x "$APP_DIR/Contents/MacOS/apk-terminal"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>apk-terminal</string>
    <key>CFBundleIdentifier</key>
    <string>com.androidcompat.apk-terminal</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>APK Terminal</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeExtensions</key>
            <array>
                <string>apk</string>
            </array>
            <key>CFBundleTypeName</key>
            <string>Android Package</string>
            <key>CFBundleTypeRole</key>
            <string>Editor</string>
        </dict>
    </array>
</dict>
</plist>
EOF

# Register the app
echo "📋 Registering app with macOS..."
/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP_DIR" 2>/dev/null || true

# Set as default using duti if available
if command -v duti &> /dev/null; then
    duti -s com.androidcompat.apk-terminal com.android.package-archive all 2>/dev/null || true
    echo "✅ Set as default handler using duti"
else
    echo ""
    echo "⚠️  duti not installed. To set as default:"
    echo "   1. Right-click any .apk file"
    echo "   2. Get Info (⌘+I)"
    echo "   3. Open with: → Other..."
    echo "   4. Select: $APP_DIR"
    echo "   5. Change All..."
    echo ""
fi

echo "════════════════════════════════════════════════════════════"
echo "✅ Setup complete!"
echo ""
echo "Usage:"
echo "  Terminal: apk install <apk-file>"
echo "  Double-click: Just double-click any .apk file"
echo ""
echo "To use immediately, run:"
echo "  source ~/.zshrc  (or ~/.bashrc)"
echo "════════════════════════════════════════════════════════════"
