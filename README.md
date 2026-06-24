# P-Translate

A fast, lightweight, and modern translation popup application for Linux, inspired by QTranslate on Windows. It grabs the currently highlighted text, translates it using the free Google Translate API, and displays the result in a beautiful, borderless dark-themed popup right at your cursor position. The popup auto-closes when it loses focus (when you click elsewhere) or when you press the `Escape` key.

## Features

- **Instant translation**: Highlights text and translates in under a second.
- **Auto-grab selection**: Works on both Wayland and X11 display servers.
- **Premium dark UI**: Designed using the Catppuccin Mocha theme with rounded corners, drop shadows, and soft animations.
- **Easy controls**: Quick copy to clipboard, change languages, or edit the source text directly.
- **Zero background daemon**: Activated purely on-demand via system shortcuts, consuming 0% CPU and 0MB RAM when idle.

---

## Installation

### Method 1: Installing via Debian Package (Recommended for Ubuntu/Debian/Mint)
This is the easiest installation method as it automatically handles all dependencies (such as Python 3, PyQt6, xdotool, and xclip).

1. Download the latest `p-translate.deb` package from the [Releases](https://github.com/buiphuc/p-translate/releases) page.
2. Install the package using `dpkg`:
   ```bash
   sudo dpkg -i p-translate.deb
   # If there are any missing dependencies, resolve them with:
   sudo apt install -f
   ```

### Method 2: Manual Installation (Other Distributions)
1. **Install Prerequisites**: Ensure you have the required clipboard and automation utilities:
   - **Fedora/RHEL**: `sudo dnf install wl-clipboard xclip xsel xdotool python3-pyqt6`
   - **Arch Linux**: `sudo pacman -S wl-clipboard xclip xsel xdotool python3-pyqt6`
2. **Clone or copy the application files** to a directory of your choice, e.g., `/home/username/p-translate`.
3. Make `run.sh` executable:
   ```bash
   chmod +x /home/username/p-translate/run.sh
   ```

---

## How to Set Up the Keyboard Shortcut

To translate text instantly like QTranslate on Windows, configure a custom keyboard shortcut in your Linux desktop environment (GNOME, Cinnamon, KDE, XFCE, etc.).

### For Debian Package users:
1. Open **Settings** -> **Keyboard** (or **Keyboard Shortcuts**).
2. Go to **Custom Shortcuts** -> click **Add Custom Shortcut** (or click the **+** button).
3. Fill in the fields:
   - **Name**: `P-Translate`
   - **Command**: `p-translate`
   - **Shortcut**: Press `Ctrl + Q` (or any shortcut of your choice).
4. Click **Add**.

### For Manual Installation users:
Set the **Command** in the shortcut configuration to run the wrapper script:
- `/bin/bash /home/username/p-translate/run.sh`

---

## Usage

1. **Select/highlight** any text on your screen (in your browser, PDF reader, text editor, terminal, etc.).
2. **Press `Ctrl + Q`** (or your custom shortcut).
3. The translation popup will appear instantly near your cursor showing the translated text in Vietnamese.
4. **Interact**:
   - Change languages via the dropdowns (source text will re-translate automatically).
   - Press **Copy Translation** or hit Enter to copy the translation to your clipboard.
   - Edit the source text in the top box and click **Translate** (or press the hotkey again) to translate new text.
5. **Close**: Simply click anywhere outside the popup window, click the `×` button, or press the `Escape` key.
