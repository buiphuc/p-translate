import sys
import subprocess
import shutil
import os
from PyQt6.QtWidgets import QApplication
from ui import TranslationPopup
from settings_manager import load_config, apply_shortcut

def get_linux_selection_text() -> str:
    """
    Attempts to retrieve the currently selected/highlighted text on Linux.
    First simulates a Ctrl+C copy if xdotool is available to support complex widgets
    (like Google Sheets, VS Code, etc.), then reads the standard clipboard.
    Falls back to reading the primary selection (highlighted text) if no clipboard text is retrieved.
    """
    import time

    # Helper function to read standard clipboard
    def read_clipboard() -> str:
        # Prefer xclip on X11 if both exist (wl-paste can fail or block on X11)
        if shutil.which("xclip"):
            try:
                result = subprocess.run(
                    ["xclip", "-out", "-selection", "clipboard"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass

        if shutil.which("wl-paste"):
            try:
                result = subprocess.run(
                    ["wl-paste", "--no-newline"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass

        if shutil.which("xsel"):
            try:
                result = subprocess.run(
                    ["xsel", "--clipboard", "--output"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass
        return ""

    # Helper function to read primary selection (text highlighted with mouse)
    def read_primary() -> str:
        if shutil.which("xclip"):
            try:
                result = subprocess.run(
                    ["xclip", "-out", "-selection", "primary"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass

        if shutil.which("wl-paste"):
            try:
                result = subprocess.run(
                    ["wl-paste", "--primary", "--no-newline"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass

        if shutil.which("xsel"):
            try:
                result = subprocess.run(
                    ["xsel", "--primary", "--output"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=0.5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass
        return ""

    # 1. Get the current clipboard content before we copy
    old_clipboard = read_clipboard()

    # 2. Try to simulate Ctrl+C using xdotool on X11
    if shutil.which("xdotool"):
        try:
            # Short sleep to let the user release keys from the hotkey trigger (Ctrl+Q)
            time.sleep(0.15)
            # Release ctrl keys first to avoid modifiers clash
            subprocess.run(
                ["xdotool", "keyup", "ctrl", "Control_L", "Control_R"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
            # Send ctrl+c key stroke to copy current selection
            subprocess.run(
                ["xdotool", "key", "ctrl+c"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
            # Release ctrl keys again immediately to prevent stuck modifier keys in the OS
            subprocess.run(
                ["xdotool", "keyup", "ctrl", "Control_L", "Control_R"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
        except Exception:
            pass

    # 3. Poll the clipboard for changes (max 400ms)
    new_text = ""
    for _ in range(8):
        time.sleep(0.05)
        current_clip = read_clipboard()
        if current_clip and current_clip != old_clipboard:
            new_text = current_clip
            break

    # If the clipboard didn't change, check if there's any text in it (fallback)
    if not new_text:
        new_text = read_clipboard()

    # 4. Fallback to primary selection (text highlighted with mouse) if clipboard is empty
    if not new_text:
        new_text = read_primary()

    return new_text

def main():
    # 1. Parse arguments for setup option
    if len(sys.argv) > 1 and sys.argv[1] in ["--setup", "-s"]:
        config = load_config()
        shortcut = config.get("shortcut", "Ctrl+Q")
        success, message = apply_shortcut(shortcut)
        if success:
            print(f"SUCCESS: {message}")
            sys.exit(0)
        else:
            print(f"ERROR: {message}")
            sys.exit(1)

    # 2. Retrieve the highlighted text
    selected_text = get_linux_selection_text()
    
    # 3. Start the Qt Application
    app = QApplication(sys.argv)
    
    # Avoid exiting when last window closes immediately in case of window transitions
    app.setQuitOnLastWindowClosed(True)
    
    # 4. Instantiate and show the popup
    popup = TranslationPopup(selected_text)
    popup.show()
    
    # 5. Execute event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
