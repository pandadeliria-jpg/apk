# Terminal-Based APK Installer Setup

No GUI! Just pure terminal with colors and effects.

## Quick Setup (Run These Commands)

```bash
# 1. Run the setup script
cd /Users/danuta/robloxgen/android_compat
chmod +x setup-terminal-handler.sh
./setup-terminal-handler.sh

# 2. Reload your shell config
source ~/.zshrc  # or ~/.bashrc
```

## Usage

### From Terminal:
```bash
# Install an APK
apk install ~/Downloads/roblox.apk

# Or use the full path
/Users/danuta/robloxgen/android_compat/bin/apk install ~/Downloads/roblox.apk
```

### By Double-Clicking:
Just double-click any `.apk` file - it will open in Terminal automatically!

## Features

- **🎨 Colors** - Cyan headers, green success, red errors, yellow warnings
- **📊 Progress Bar** - Visual `[████████░░░░] 60%` style progress
- **✨ Animations** - Spinner while loading
- **📦 ASCII Boxes** - Fancy borders around messages
- **🎮 Launch Option** - Type 'run' after install to launch the app

## Example Output

```
════════════════════════════════════════════════════════════
  📱 APK INSTALLER
════════════════════════════════════════════════════════════

File: roblox.apk
/Users/danuta/Downloads/roblox.apk

🔍 Verifying APK...
  ✓ Valid APK with DEX files
  → 2456 files in archive

→ Preparing installation...

🚀 Installing APK...

→ Extracting APK...
→ Installing roblox.apk...
  ✓ Installed: com.roblox.client
  ✓ Version: 2.650.742

  ✓ INSTALLATION SUCCESSFUL!

┌──────────────────────────────────────────────────────┐
│                    Next Steps                        │
├──────────────────────────────────────────────────────┤
│ Run the app with:                                    │
│                                                      │
│   python3 run_apk.py --run <package>                 │
│                                                      │
│ Or list installed apps:                              │
│   python3 run_apk.py --list-apps                     │
└──────────────────────────────────────────────────────┘

Press Enter to exit, or type 'run' to launch:
```

## Manual Setup (If Automatic Fails)

### Step 1: Create Alias
Add to your `~/.zshrc` or `~/.bashrc`:
```bash
alias apk='/Users/danuta/robloxgen/android_compat/bin/apk'
```

### Step 2: Add to PATH
```bash
mkdir -p ~/.local/bin
ln -s /Users/danuta/robloxgen/android_compat/bin/apk ~/.local/bin/apk
```

Make sure `~/.local/bin` is in your PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Step 3: Set as Default Handler
Right-click any `.apk` file → Get Info (⌘+I) → Open with → Other → Select:
```
/Users/danuta/robloxgen/android_compat/APK-Terminal.app
```

Click "Change All..." to apply to all APK files.

## Homebrew-Style Install (Optional)

To make it available system-wide like a Homebrew app:

```bash
# Create bin directory if needed
mkdir -p /usr/local/bin

# Symlink the command
sudo ln -s /Users/danuta/robloxgen/android_compat/bin/apk /usr/local/bin/apk

# Now you can use it from anywhere!
apk install ~/Downloads/roblox.apk
```

## Troubleshooting

### "command not found: apk"
- Run: `source ~/.zshrc` (or restart Terminal)
- Or use full path: `/Users/danuta/robloxgen/android_compat/bin/apk`

### Double-click doesn't open Terminal
- Right-click APK → Get Info → Open with → APK-Terminal.app → Change All
- Or run: `./setup-terminal-handler.sh` again

### Colors not showing
- Make sure you're using a terminal that supports ANSI colors (iTerm2, Terminal.app)
- The command auto-detects terminal vs GUI mode

## Summary

| Method | How |
|--------|-----|
| Terminal | `apk install file.apk` |
| Double-click | Just double-click any .apk |
| With launch | Type 'run' after install completes |
