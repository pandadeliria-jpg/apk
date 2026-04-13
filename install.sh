#!/bin/bash
# Install APK Installer as a terminal command
# Usage: ./install.sh

set -e

INSTALL_DIR="/usr/local/bin"
COMPAT_DIR="/Users/danuta/robloxgen/android_compat"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}  📱 APK Installer - Terminal Edition${NC}"
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if we can write to /usr/local/bin
if [ ! -w "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠️  Need sudo to install to $INSTALL_DIR${NC}"
    SUDO="sudo"
else
    SUDO=""
fi

# Create the main command
echo -e "${CYAN}🔧 Installing 'apk' command...${NC}"

$SUDO tee "$INSTALL_DIR/apk" > /dev/null << EOF
#!/bin/bash
# APK Installer - Main command
# Usage: apk <command> [args]

COMPAT_DIR="$COMPAT_DIR"

show_help() {
    echo "APK Installer - Android→macOS Compatibility Layer"
    echo ""
    echo "Usage:"
    echo "  apk install <file.apk>     Install an APK file"
    echo "  apk list                   List installed apps"
    echo "  apk run <package>          Run an installed app"
    echo "  apk remove <package>       Uninstall an app"
    echo "  apk info <package>         Show app info"
    echo "  apk help                   Show this help"
    echo ""
    echo "Examples:"
    echo "  apk install ~/Downloads/roblox.apk"
    echo "  apk list"
    echo "  apk run com.roblox.client"
}

case "\$1" in
    install|i)
        if [ -z "\$2" ]; then
            echo "Usage: apk install <file.apk>"
            exit 1
        fi
        cd "\$COMPAT_DIR" && python3 run_apk.py "\$2" --install
        ;;
    list|ls)
        cd "\$COMPAT_DIR" && python3 run_apk.py --list-apps
        ;;
    run|r)
        if [ -z "\$2" ]; then
            echo "Usage: apk run <package_name>"
            exit 1
        fi
        cd "\$COMPAT_DIR" && python3 run_apk.py --run "\$2"
        ;;
    remove|rm|uninstall)
        if [ -z "\$2" ]; then
            echo "Usage: apk remove <package_name>"
            exit 1
        fi
        cd "\$COMPAT_DIR" && python3 run_apk.py --uninstall "\$2"
        ;;
    info)
        if [ -z "\$2" ]; then
            echo "Usage: apk info <package_name>"
            exit 1
        fi
        cd "\$COMPAT_DIR" && python3 -c "
import sys
sys.path.insert(0, '\$COMPAT_DIR/runtime')
from app_manager import get_app_manager
mgr = get_app_manager()
for app in mgr.list_apps():
    if '\$2' in app.package_name:
        print(f\"Name: {app.name}\")
        print(f\"Package: {app.package_name}\")
        print(f\"Version: {app.version_name} ({app.version_code})\")
        print(f\"Installed: {app.install_date}\")
        print(f\"Launches: {app.launch_count}\")
        print(f\"Location: {app.apk_path}\")
        break
"
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        # If first arg is a file, assume install
        if [ -f "\$1" ] && [[ "\$1" == *.apk ]]; then
            cd "\$COMPAT_DIR" && python3 run_apk.py "\$1" --install
        else
            show_help
        fi
        ;;
esac
EOF

$SUDO chmod +x "$INSTALL_DIR/apk"

echo ""
echo -e "${GREEN}${BOLD}✅ Installation complete!${NC}"
echo ""
echo "Command installed:"
echo "  ${BOLD}apk${NC} - Main command (install, list, run, remove)"
echo ""
echo "Usage:"
echo "  apk install ~/Downloads/roblox.apk"
echo "  apk list"
echo "  apk run com.roblox.client"
echo ""
echo -e "${YELLOW}Note: You may need to restart your terminal or run:${NC}"
echo "  hash -r"
echo ""
