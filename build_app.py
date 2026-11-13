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
    ver_path = os.path.join(BASE_DIR, "file_version_info.txt")

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
    if os.path.exists(ver_path):
        cmd.append(f"--version-file={ver_path}")

    cmd.append(os.path.join(BASE_DIR, "main.py"))

    print(f"[BUILD] Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode == 0:
        print("\n✔ PyInstaller build succeeded!")
        dist_dir = os.path.join(BASE_DIR, "dist", "MacTech_Android_Tool")
        exe_path = os.path.join(dist_dir, "MacTech_Android_Tool.exe")

        # 4. Sign executable with Authenticode Code Signing Certificate
        print("\n[SIGN] Signing executable with MacTech Solutions Lab certificate...")
        sign_script = f"""
        $cert = Get-ChildItem Cert:\\CurrentUser\\My | Where-Object {{ $_.Subject -like '*MacTech Solutions Lab*' }} | Select-Object -First 1
        if ($cert) {{
            Set-AuthenticodeSignature -FilePath '{exe_path}' -Certificate $cert -HashAlgorithm SHA256 | Out-Null
            Write-Host '✔ Executable digitally signed with Authenticode (MacTech Solutions Lab)!'
        }} else {{
            Write-Host '⚠ No matching certificate found in Cert:\\CurrentUser\\My'
        }}
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", sign_script], cwd=BASE_DIR)

        # 5. Copy helper files & cert to dist directory
        for f in ["MacTech_Solutions_Lab.cer", "Trust_Publisher_And_Run.bat", "Launch_Tool.bat"]:
            src = os.path.join(BASE_DIR, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(dist_dir, f))

        print(f"\nArtifacts located at: {dist_dir}")
        return True
    else:
        print("\n❌ PyInstaller build failed.")
        return False

if __name__ == "__main__":
    build()
