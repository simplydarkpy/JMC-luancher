import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import sv_ttk
import minecraft_launcher_lib
import subprocess
import os
import json
import shutil
import uuid
import requests
import threading
import time

# ---------------- INFO ----------------

APP_NAME = "JMC Launcher"
APP_AUTHOR = "YOUSSOF"

# ---------------- PATHS ----------------

MC_DIR = os.path.join(os.getenv("APPDATA"), ".minecraft")
MODS_DIR = os.path.join(MC_DIR, "mods")
CONFIG_FILE = "jmc_config.json"

os.makedirs(MC_DIR, exist_ok=True)
os.makedirs(MODS_DIR, exist_ok=True)

# ---------------- FETCH ONLINE DATA ----------------

def get_latest_mc():
    data = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json").json()
    return data["latest"]["release"]

def get_latest_fabric():
    data = requests.get("https://meta.fabricmc.net/v2/versions/loader").json()
    return data[0]["version"]

# ---------------- USERNAME SAVE ----------------

def load_username():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f).get("username", "")
    return ""

def save_username(name):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"username": name}, f)

# ---------------- XP BAR ----------------

def xp_load():
    progress["value"] = 0
    for i in range(101):
        progress["value"] = i
        root.update()
        time.sleep(0.01)

# ---------------- FABRIC INSTALL ----------------

def install_fabric():
    threading.Thread(target=fabric_worker).start()

def fabric_worker():
    try:
        status_label.config(text="Installing Fabric...")
        xp_load()

        mc = get_latest_mc()
        loader = get_latest_fabric()

        minecraft_launcher_lib.fabric.install_fabric(
            minecraft_version=mc,
            loader_version=loader,
            minecraft_directory=MC_DIR
        )

        status_label.config(text=f"Fabric Installed ✅ ({mc})")

    except Exception as e:
        messagebox.showerror("Fabric Error", str(e))

# ---------------- LAUNCH GAME ----------------

def launch_game():
    threading.Thread(target=launch_worker).start()

def launch_worker():
    try:
        username = name_entry.get().strip()

        if not username:
            messagebox.showerror("Bruh", "Enter Username 😭")
            return

        save_username(username)

        status_label.config(text="Launching Minecraft...")
        xp_load()

        mc = get_latest_mc()
        loader = get_latest_fabric()

        version_id = f"fabric-loader-{loader}-{mc}"

        offline_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, username))

        options = {
            "username": username,
            "uuid": offline_uuid,
            "token": "0",
            "jvmArguments": ["-Xmx6G"]
        }

        cmd = minecraft_launcher_lib.command.get_minecraft_command(
            version_id,
            MC_DIR,
            options
        )

        subprocess.Popen(cmd)

        status_label.config(text="Minecraft Running 🎮")

    except Exception as e:
        messagebox.showerror("Launch Error", str(e))

# ---------------- MOD MANAGER ----------------

def refresh_mods():
    mod_list.delete(0, tk.END)

    for file in os.listdir(MODS_DIR):
        if file.endswith(".jar"):
            mod_list.insert(tk.END, file)

def drop_mod(event):
    files = root.tk.splitlist(event.data)

    for file in files:
        if file.endswith(".jar"):
            shutil.copy(file, MODS_DIR)

    refresh_mods()
    status_label.config(text="Mods Added ✅")

def delete_mod():
    selected = mod_list.curselection()

    if not selected:
        messagebox.showwarning("Select Mod", "Pick a mod first 💀")
        return

    mod_name = mod_list.get(selected[0])
    path = os.path.join(MODS_DIR, mod_name)

    try:
        os.remove(path)
        refresh_mods()
        status_label.config(text=f"{mod_name} Deleted 🗑️")
    except Exception as e:
        messagebox.showerror("Delete Error", str(e))

# ---------------- SPLASH SCREEN ----------------

splash = tk.Tk()
splash.overrideredirect(True)
splash.geometry("420x220+600+300")

tk.Label(
    splash,
    text="JMC Launcher",
    font=("Segoe UI", 22, "bold")
).pack(pady=20)

tk.Label(
    splash,
    text="By YOUSSOF",
    font=("Segoe UI", 11)
).pack()

sp = ttk.Progressbar(splash, length=300)
sp.pack(pady=20)

for i in range(100):
    sp["value"] = i
    splash.update()
    time.sleep(0.015)

splash.destroy()

# ---------------- MAIN WINDOW ----------------

root = TkinterDnD.Tk()
root.title(APP_NAME)
root.geometry("650x550")
root.resizable(False, False)

sv_ttk.set_theme("dark")

# ---------------- TABS ----------------

tabs = ttk.Notebook(root)
tabs.pack(fill="both", expand=True)

# ---------------- TAB: LAUNCHER ----------------

launch_tab = ttk.Frame(tabs)
tabs.add(launch_tab, text="Launcher")

ttk.Label(launch_tab, text="Offline Username").pack(pady=5)

name_entry = ttk.Entry(launch_tab, width=30)
name_entry.pack()

saved = load_username()
if saved:
    name_entry.insert(0, saved)

ttk.Button(launch_tab, text="Install / Update Fabric", command=install_fabric).pack(pady=10)
ttk.Button(launch_tab, text="Launch Minecraft", command=launch_game).pack()

progress = ttk.Progressbar(launch_tab, length=420)
progress.pack(pady=15)

status_label = ttk.Label(launch_tab, text="Ready ✅")
status_label.pack()

# ---------------- TAB: MODS ----------------

mods_tab = ttk.Frame(tabs)
tabs.add(mods_tab, text="Mods")

drop_box = ttk.Label(mods_tab, text="Drag Mods Here (.jar)", relief="ridge")
drop_box.pack(fill="x", padx=20, pady=10)

drop_box.drop_target_register(DND_FILES)
drop_box.dnd_bind("<<Drop>>", drop_mod)

mod_list = tk.Listbox(mods_tab, height=14)
mod_list.pack(fill="both", padx=20, pady=10)

btn_frame = ttk.Frame(mods_tab)
btn_frame.pack(pady=5)

ttk.Button(btn_frame, text="Delete Selected", command=delete_mod).pack(side="left", padx=10)
ttk.Button(btn_frame, text="Refresh", command=refresh_mods).pack(side="left", padx=10)

refresh_mods()

# ---------------- TAB: SETTINGS ----------------

settings_tab = ttk.Frame(tabs)
tabs.add(settings_tab, text="Settings")

def toggle_theme():
    current = sv_ttk.get_theme()
    sv_ttk.set_theme("light" if current == "dark" else "dark")

ttk.Button(settings_tab, text="Toggle Light / Dark Mode", command=toggle_theme).pack(pady=25)

ttk.Label(
    settings_tab,
    text="JMC Launcher\nBy YOUSSOF",
    font=("Segoe UI", 12)
).pack()

root.mainloop()
