# Double-Click APK Installation Setup

This guide explains how to set up your Mac so that double-clicking an APK file automatically installs it using the Android→macOS Compatibility Layer.

## Option 1: Quick Setup (Recommended)

### Step 1: Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install duti
```bash
brew install duti
```

### Step 3: Run the setup script
```bash
cd /Users/danuta/robloxgen/android_compat
chmod +x setup_apk_association.sh
./setup_apk_association.sh
```

### Step 4: Double-click any .apk file!

---

## Option 2: Manual Setup (Finder)

If the automatic setup doesn't work, you can manually set the file association:

1. **Right-click** any `.apk` file
2. Select **"Get Info"** (or press ⌘+I)
3. Under **"Open with:"**, select **"Other..."**
4. Navigate to:
   ```
   /Users/danuta/robloxgen/android_compat/APK Installer.app
   ```
5. Check **"Always Open With"**
6. Click **"Add"**
7. Click **"Change All..."** button to apply to all .apk files

---

## Option 3: Install as Quick Action (Right-Click Menu)

### Step 1: Open the workflow in Automator
```bash
open "/Users/danuta/robloxgen/android_compat/Install APK.workflow"
```

### Step 2: Save as Quick Action
1. In Automator, go to **File → Save**
2. Choose **"Quick Action"** as the file format
3. Name it **"Install APK"**
4. Click **Save**

### Step 3: Use it
Now you can right-click any `.apk` file and select **"Quick Actions → Install APK"**

---

## Option 4: GUI Installer (Tkinter)

For a graphical installation experience:

```bash
cd /Users/danuta/robloxgen/android_compat
python3 apk_install_gui.py /path/to/your.apk
```

Or without specifying a file (browse dialog will appear):
```bash
python3 apk_install_gui.py
```

---

## What Happens When You Double-Click

1. **APK Installer** app opens
2. Shows a confirmation dialog
3. Opens Terminal window
4. Runs: `python3 run_apk.py <file>.apk --install`
5. Shows installation progress
6. App is now available in your installed apps library

---

## After Installation

### Run the installed app:
```bash
cd /Users/danuta/robloxgen/android_compat
python3 run_apk.py --run com.roblox.client
```

### List installed apps:
```bash
python3 run_apk.py --list-apps
```

### Uninstall:
```bash
python3 run_apk.py --uninstall com.roblox.client
```

---

## Troubleshooting

### "APK Installer.app can't be opened because it is from an unidentified developer"

1. Right-click the APK file (instead of double-clicking)
2. Hold **Option** key and click **"Open"**
3. Click **"Open"** in the security dialog

Or go to **System Preferences → Security & Privacy → General** and click **"Open Anyway"**

### APK doesn't install

Check the Terminal output for errors:
1. Make sure you're in the right directory:
   ```bash
   cd /Users/danuta/robloxgen/android_compat
   ```
2. Test manually:
   ```bash
   python3 run_apk.py your.apk --install
   ```

### "Python3 not found"

Make sure Python 3 is installed:
```bash
python3 --version
```

If not installed:
```bash
brew install python3
```

---

## Files Created

- `APK Installer.app` - macOS app bundle for opening APK files
- `apk_install_gui.py` - GUI installer with progress bar
- `setup_apk_association.sh` - Setup script for file associations
- `Install APK.workflow` - Automator Quick Action

---

## Storage Location

Installed apps are stored in:
```
~/.android_compat/apps/
├── installed/     # APK files and extracted contents
├── data/          # App data (SharedPreferences, databases)
└── cache/         # App cache
```

---

## Summary

| Method | How To Use |
|--------|------------|
| Double-click | Just double-click any .apk file |
| Right-click → Quick Actions | Right-click .apk → Quick Actions → Install APK |
| GUI Installer | `python3 apk_install_gui.py file.apk` |
| Command Line | `python3 run_apk.py file.apk --install` |
