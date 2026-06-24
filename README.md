# QTranslate for Linux

A fast, lightweight, and modern translation popup application for Linux, inspired by QTranslate on Windows. It grabs the currently highlighted text, translates it using the free Google Translate API, and displays the result in a beautiful, borderless dark-themed popup right at your cursor position. The popup auto-closes when it loses focus (when you click elsewhere) or when you press the `Escape` key.

## Features

- **Instant translation**: Highlights text and translates in under a second.
- **Auto-grab selection**: Works on both Wayland and X11 display servers.
- **Premium dark UI**: Designed using the Catppuccin Mocha theme with rounded corners, drop shadows, and soft animations.
- **Easy controls**: Quick copy to clipboard, change languages, or edit the source text directly.
- **Zero background daemon**: Activated purely on-demand via system shortcuts, consuming 0% CPU and 0MB RAM when idle.

---

## Prerequisites

First, ensure you have the required clipboard utilities installed for your display server:

### For Ubuntu/Debian/Mint:
```bash
# For Wayland (default on most modern distributions like Ubuntu 22.04+)
sudo apt install wl-clipboard

# For X11 (if you are running on Xorg)
sudo apt install xclip xsel
```

### For Fedora/RHEL:
```bash
sudo dnf install wl-clipboard xclip xsel
```

### For Arch Linux:
```bash
sudo pacman -S wl-clipboard xclip xsel
```

---

## Installation

1. **Clone or copy the application files** to a directory of your choice, e.g., `/home/username/qtranslate-linux`.
2. **Install the Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you run into a PEP 668 externally-managed-environment error, you can install PyQt6 via your package manager (`sudo apt install python3-pyqt6`) or create a Python virtual environment.*

---

## How to Set Up the `Ctrl + Q` Shortcut

To translate text instantly like QTranslate on Windows, configure a custom keyboard shortcut in your Linux desktop environment (GNOME, KDE, XFCE, etc.).

### For GNOME (Ubuntu, Fedora, Debian default):
1. Open **Settings** -> **Keyboard** (or **Keyboard Shortcuts**).
2. Scroll to the bottom and click on **View and Customise Shortcuts** -> **Custom Shortcuts** (or **Add Custom Shortcut**).
3. Click the **+** (Add) button.
4. Fill in the fields:
   - **Name**: `QTranslate Linux`
   - **Command**: `python3 /absolute/path/to/qtranslate-linux/main.py`
   - **Shortcut**: Press `Ctrl + Q` (Note: If `Ctrl + Q` is bound to something else, GNOME will ask to reassign it).
5. Click **Add**.

*Tip: If you used a virtual environment, set the Command to use the python interpreter inside that virtual environment, for example:*
`/home/username/qtranslate-linux/venv/bin/python /home/username/qtranslate-linux/main.py`

---

## Usage

1. **Select/highlight** any text on your screen (in your browser, PDF reader, text editor, terminal, etc.).
2. **Press `Ctrl + Q`** (or your custom shortcut).
3. The translation popup will appear instantly near your cursor showing the translated text in Vietnamese.
4. **Interact**:
   - Change languages via the dropdowns (source text will re-translate automatically).
   - Press **Copy** or hit Enter to copy the translation.
   - Edit the source text in the top box and click **Translate** (or press the hotkey again) to translate new text.
5. **Close**: Simply click anywhere outside the popup window, click the `×` button, or press the `Escape` key.
