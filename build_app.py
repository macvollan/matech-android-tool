"""
PyInstaller Compilation Script for MacTech Android Tool
MacTech Solutions Lab
"""

import os
import sys
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build():
    print("=" * 60)
    print("  MacTech Android Tool - Standalone Executable Builder")
    print("  MacTech Solutions Lab")
    print("=" * 60)

    # 1. Clean previous build artifacts
    for folder in ["build", "dist"]:
        fpath = os.path.join(BASE_DIR, folder)
        if os.path.exists(fpath):
            shutil.rmtree(fpath, ignore_errors=True)

    # 2. Locate customtkinter package directory for data bundling
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)

    # 3. Construct PyInstaller command
    icon_path = os.path.join(BASE_DIR, "assets", "icon.ico")
    bin_path = os.path.join(BASE_DIR, "bin")
    assets_path = os.path.join(BASE_DIR, "assets")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=MacTech_Android_Tool",
        "--windowed", # No CMD window
        "--onedir", # Directory distribution
        f"--add-data={ctk_path};customtkinter",
        f"--add-data={bin_path};bin",
        f"--add-data={assets_path};assets",
    ]

    if os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")

    cmd.append(os.path.join(BASE_DIR, "main.py"))

    print(f"[BUILD] Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode == 0:
        print("\n✔ PyInstaller build succeeded!")
        dist_dir = os.path.join(BASE_DIR, "dist", "MacTech_Android_Tool")
        print(f"Artifacts located at: {dist_dir}")
        return True
    else:
        print("\n❌ PyInstaller build failed.")
        return False

if __name__ == "__main__":
    build()
