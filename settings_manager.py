import os
import json
import subprocess
import shutil
import ast
import re

# Path to the config file in user's config directory
CONFIG_DIR = os.path.expanduser("~/.config/p-translate")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


def load_config() -> dict:
    """Loads configuration from config.json, creating a default one if it doesn't exist."""
    default_config = {
        "shortcut": "Ctrl+Q",
        "autostart": False
    }
    if not os.path.exists(CONFIG_PATH):
        save_config(default_config)
        return default_config
    
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            # Ensure all required keys exist
            for key, val in default_config.items():
                if key not in config:
                    config[key] = val
            return config
    except Exception:
        return default_config

def save_config(config: dict):
    """Saves the configuration dictionary to config.json."""
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def qt_to_gsettings_shortcut(qt_shortcut: str) -> str:
    """
    Converts a Qt-style shortcut (e.g., 'Ctrl+Alt+Q') 
    to GSettings-style shortcut format (e.g., '<Control><Alt>q').
    """
    parts = qt_shortcut.split('+')
    gsettings_parts = []
    
    for p in parts:
        p_lower = p.lower()
        if p_lower == "ctrl":
            gsettings_parts.append("<Control>")
        elif p_lower == "alt":
            gsettings_parts.append("<Alt>")
        elif p_lower == "shift":
            gsettings_parts.append("<Shift>")
        elif p_lower in ["meta", "win", "super"]:
            gsettings_parts.append("<Super>")
        else:
            # GSettings keys are lowercase (e.g., 'q', 'space', 'escape')
            gsettings_parts.append(p.lower())
            
    return "".join(gsettings_parts)

def apply_shortcut(qt_shortcut: str) -> tuple[bool, str]:
    """
    Registers the given Qt-style shortcut to run this application 
    via GSettings on Cinnamon or GNOME desktop environments.
    """
    if not qt_shortcut:
        return False, "Shortcut cannot be empty"
        
    gsettings_key = qt_to_gsettings_shortcut(qt_shortcut)
    
    main_path = os.path.abspath(__file__)
    # Path to run.sh wrapper, located in the same directory
    project_dir = os.path.dirname(main_path)
    command_str = f"/bin/bash {project_dir}/run.sh"
    
    # 1. Detect Desktop Environment by listing GSettings schemas
    try:
        schemas_res = subprocess.run(
            ["gsettings", "list-schemas"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        all_schemas = schemas_res.stdout
    except Exception as e:
        return False, f"Failed to list GSettings schemas: {str(e)}"
        
    is_cinnamon = "org.cinnamon.desktop.keybindings" in all_schemas
    
    if is_cinnamon:
        # --- Cinnamon Configuration ---
        schema = "org.cinnamon.desktop.keybindings"
        key = "custom-list"
        path_prefix = "/org/cinnamon/desktop/keybindings/custom-keybindings/"
        custom_schema = "org.cinnamon.desktop.keybindings.custom-keybinding"
        
        try:
            # Read custom-list of keybindings
            res = subprocess.run(["gsettings", "get", schema, key], stdout=subprocess.PIPE, text=True, timeout=2)
            list_str = res.stdout.strip()
            if not list_str or list_str.startswith("@as"):
                bindings_list = []
            else:
                try:
                    bindings_list = ast.literal_eval(list_str)
                except Exception:
                    bindings_list = []
            
            # Find if our P-Translate binding is already registered, and find max index
            max_idx = -1
            our_existing_id = None
            for item in bindings_list:
                item_path = f"{custom_schema}:{path_prefix}{item}/"
                res_name = subprocess.run(["gsettings", "get", item_path, "name"], stdout=subprocess.PIPE, text=True)
                if "P-Translate" in res_name.stdout:
                    our_existing_id = item
                    break
                match = re.search(r'custom(\d+)$', item)
                if match:
                    idx = int(match.group(1))
                    if idx > max_idx:
                        max_idx = idx
            
            if our_existing_id:
                binding_id = our_existing_id
            else:
                binding_id = f"custom{max_idx + 1}"
                
            # Add to custom-list if not present
            if binding_id not in bindings_list:
                bindings_list.append(binding_id)
                formatted_list = str(bindings_list).replace("'", '"')
                subprocess.run(["gsettings", "set", schema, key, formatted_list])
                
            # Set keybinding details
            target_path = f"{custom_schema}:{path_prefix}{binding_id}/"
            subprocess.run(["gsettings", "set", target_path, "name", "P-Translate"])
            subprocess.run(["gsettings", "set", target_path, "command", command_str])
            # Cinnamon binding must be formatted as a list of strings
            subprocess.run(["gsettings", "set", target_path, "binding", f"['{gsettings_key}']"])
            
            return True, f"Cinnamon Shortcut registered successfully to {qt_shortcut}!"
        except Exception as e:
            return False, f"Error configuring Cinnamon shortcut: {str(e)}"
            
    else:
        # --- GNOME Configuration ---
        schema = "org.gnome.settings-daemon.plugins.media-keys"
        key = "custom-keybindings"
        path_prefix = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
        custom_schema = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
        
        try:
            # Read custom-keybindings list
            res = subprocess.run(["gsettings", "get", schema, key], stdout=subprocess.PIPE, text=True, timeout=2)
            list_str = res.stdout.strip()
            if not list_str or list_str.startswith("@as"):
                bindings_list = []
            else:
                try:
                    bindings_list = ast.literal_eval(list_str)
                except Exception:
                    bindings_list = []
                    
            max_idx = -1
            our_existing_path = None
            for item in bindings_list:
                item_path = f"{custom_schema}:{item}"
                res_name = subprocess.run(["gsettings", "get", item_path, "name"], stdout=subprocess.PIPE, text=True)
                if "P-Translate" in res_name.stdout:
                    our_existing_path = item
                    break
                match = re.search(r'custom(\d+)/$', item)
                if match:
                    idx = int(match.group(1))
                    if idx > max_idx:
                        max_idx = idx
                        
            if our_existing_path:
                new_path = our_existing_path
            else:
                new_path = f"{path_prefix}custom{max_idx + 1}/"
                
            # Add to custom-keybindings list if not present
            if new_path not in bindings_list:
                bindings_list.append(new_path)
                formatted_list = str(bindings_list).replace("'", '"')
                subprocess.run(["gsettings", "set", schema, key, formatted_list])
                
            # Set keybinding details
            target_path = f"{custom_schema}:{new_path}"
            subprocess.run(["gsettings", "set", target_path, "name", "P-Translate"])
            subprocess.run(["gsettings", "set", target_path, "command", command_str])
            # GNOME binding is a direct string
            subprocess.run(["gsettings", "set", target_path, "binding", gsettings_key])
            
            return True, f"GNOME Shortcut registered successfully to {qt_shortcut}!"
        except Exception as e:
            return False, f"Error configuring GNOME shortcut: {str(e)}"

def apply_autostart(enable: bool) -> tuple[bool, str]:
    """
    Creates or removes a .desktop file in the user's autostart directory 
    to control automatic application launching on desktop login.
    """
    autostart_dir = os.path.expanduser("~/.config/autostart")
    desktop_file_path = os.path.join(autostart_dir, "p-translate.desktop")
    
    if enable:
        try:
            # Ensure the directory exists
            os.makedirs(autostart_dir, exist_ok=True)
            
            main_path = os.path.abspath(__file__)
            project_dir = os.path.dirname(main_path)
            run_sh_path = os.path.join(project_dir, "run.sh")
            
            content = f"""[Desktop Entry]
Type=Application
Name=P-Translate
Comment=Quick translation tool using hotkey
Exec=/bin/bash {run_sh_path}
X-GNOME-Autostart-enabled=true
Terminal=false
"""
            with open(desktop_file_path, "w") as f:
                f.write(content)
            return True, "Autostart enabled successfully"
        except Exception as e:
            return False, f"Failed to enable autostart: {str(e)}"
    else:
        try:
            if os.path.exists(desktop_file_path):
                os.remove(desktop_file_path)
            return True, "Autostart disabled successfully"
        except Exception as e:
            return False, f"Failed to disable autostart: {str(e)}"

def check_and_update_shortcut_registration() -> tuple[bool, str]:
    """
    Checks if the current global shortcut and autostart registration
    in GSettings/autostart folder match the current application path and settings.
    If they do not match, or are not registered yet, they will be updated automatically.
    """
    # 1. Load current configuration
    config = load_config()
    shortcut = config.get("shortcut", "Ctrl+Q")
    autostart = config.get("autostart", False)
    
    # 2. Define the expected command string
    main_path = os.path.abspath(__file__)
    project_dir = os.path.dirname(main_path)
    expected_command = f"/bin/bash {project_dir}/run.sh"
    
    # 3. Detect Desktop Environment
    try:
        schemas_res = subprocess.run(
            ["gsettings", "list-schemas"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        all_schemas = schemas_res.stdout
    except Exception as e:
        return False, f"Failed to list GSettings schemas: {str(e)}"
        
    is_cinnamon = "org.cinnamon.desktop.keybindings" in all_schemas
    is_gnome = "org.gnome.settings-daemon.plugins.media-keys" in all_schemas
    
    shortcut_needs_update = True
    gsettings_key = qt_to_gsettings_shortcut(shortcut)
    
    if is_cinnamon:
        # Check Cinnamon keybindings
        schema = "org.cinnamon.desktop.keybindings"
        key = "custom-list"
        path_prefix = "/org/cinnamon/desktop/keybindings/custom-keybindings/"
        custom_schema = "org.cinnamon.desktop.keybindings.custom-keybinding"
        
        try:
            res = subprocess.run(["gsettings", "get", schema, key], stdout=subprocess.PIPE, text=True, timeout=2)
            list_str = res.stdout.strip()
            if list_str and not list_str.startswith("@as"):
                bindings_list = ast.literal_eval(list_str)
            else:
                bindings_list = []
                
            for item in bindings_list:
                item_path = f"{custom_schema}:{path_prefix}{item}/"
                res_name = subprocess.run(["gsettings", "get", item_path, "name"], stdout=subprocess.PIPE, text=True)
                if "P-Translate" in res_name.stdout:
                    # Found existing registration. Check command and binding
                    res_cmd = subprocess.run(["gsettings", "get", item_path, "command"], stdout=subprocess.PIPE, text=True)
                    res_bind = subprocess.run(["gsettings", "get", item_path, "binding"], stdout=subprocess.PIPE, text=True)
                    
                    registered_cmd = res_cmd.stdout.strip().strip("'\"")
                    registered_bind_raw = res_bind.stdout.strip()
                    try:
                        registered_bind_list = ast.literal_eval(registered_bind_raw)
                        registered_bind = registered_bind_list[0] if registered_bind_list else ""
                    except Exception:
                        registered_bind = ""
                        
                    if registered_cmd == expected_command and registered_bind == gsettings_key:
                        shortcut_needs_update = False
                    break
        except Exception:
            pass
            
    elif is_gnome:
        # Check GNOME keybindings
        schema = "org.gnome.settings-daemon.plugins.media-keys"
        key = "custom-keybindings"
        path_prefix = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
        custom_schema = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
        
        try:
            res = subprocess.run(["gsettings", "get", schema, key], stdout=subprocess.PIPE, text=True, timeout=2)
            list_str = res.stdout.strip()
            if list_str and not list_str.startswith("@as"):
                bindings_list = ast.literal_eval(list_str)
            else:
                bindings_list = []
                
            for item in bindings_list:
                item_path = f"{custom_schema}:{item}"
                res_name = subprocess.run(["gsettings", "get", item_path, "name"], stdout=subprocess.PIPE, text=True)
                if "P-Translate" in res_name.stdout:
                    res_cmd = subprocess.run(["gsettings", "get", item_path, "command"], stdout=subprocess.PIPE, text=True)
                    res_bind = subprocess.run(["gsettings", "get", item_path, "binding"], stdout=subprocess.PIPE, text=True)
                    
                    registered_cmd = res_cmd.stdout.strip().strip("'\"")
                    registered_bind = res_bind.stdout.strip().strip("'\"")
                    
                    if registered_cmd == expected_command and registered_bind == gsettings_key:
                        shortcut_needs_update = False
                    break
        except Exception:
            pass
            
    # Check autostart file correctness
    autostart_needs_update = True
    autostart_dir = os.path.expanduser("~/.config/autostart")
    desktop_file_path = os.path.join(autostart_dir, "p-translate.desktop")
    
    if autostart:
        if os.path.exists(desktop_file_path):
            try:
                with open(desktop_file_path, "r") as f:
                    content = f.read()
                expected_exec = f"Exec=/bin/bash {os.path.join(project_dir, 'run.sh')}"
                if expected_exec in content:
                    autostart_needs_update = False
            except Exception:
                pass
    else:
        # If autostart is disabled and no file exists, we don't need to update
        if not os.path.exists(desktop_file_path):
            autostart_needs_update = False

    messages = []
    # 4. Perform updates if needed
    if shortcut_needs_update:
        success, msg = apply_shortcut(shortcut)
        if success:
            messages.append("Global shortcut updated successfully")
        else:
            messages.append(f"Failed to update shortcut: {msg}")
            
    if autostart_needs_update:
        success, msg = apply_autostart(autostart)
        if success:
            messages.append("Autostart configuration updated successfully")
        else:
            messages.append(f"Failed to update autostart: {msg}")
            
    if not messages:
        return True, "Shortcut and autostart are already up to date"
    else:
        return True, "; ".join(messages)

