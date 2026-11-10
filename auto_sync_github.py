"""
MacTech Solutions Lab - Automated GitHub Sync & Release Provisioner
Repository: https://github.com/macvollan/mactech-android-tool
"""

import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GIT_BIN = r"C:\Program Files\Git\cmd\git.exe"
if not os.path.exists(GIT_BIN):
    GIT_BIN = "git"

GH_BIN = r"C:\Program Files\GitHub CLI\gh.exe"
if not os.path.exists(GH_BIN):
    GH_BIN = "gh"

REPO_NAME = "macvollan/mactech-android-tool"

def sync(commit_msg: str = None):
    print("=" * 60)
    print("  MacTech Solutions Lab - Auto-Sync to GitHub")
    print(f"  Repository: {REPO_NAME}")
    print("=" * 60)

    if not commit_msg:
        commit_msg = "Release: MacTech Android Tool v2.2 - Forensic Authenticity & ADB Diagnostic Suite"

    # 1. Initialize git if not present
    if not os.path.exists(os.path.join(BASE_DIR, ".git")):
        print("[INIT] Initializing git repository...")
        subprocess.run([GIT_BIN, "init"], cwd=BASE_DIR)

    # 2. Stage changes
    print("[1/4] Staging file changes...")
    subprocess.run([GIT_BIN, "add", "-A"], cwd=BASE_DIR)

    # 3. Check status & commit
    st = subprocess.run([GIT_BIN, "status", "--porcelain"], cwd=BASE_DIR, capture_output=True, text=True).stdout
    if st.strip():
        print("[2/4] Committing changes...")
        subprocess.run([GIT_BIN, "commit", "-m", commit_msg], cwd=BASE_DIR)
    else:
        print("[2/4] Working directory clean, no new commits needed.")

    # 4. Set branch main
    subprocess.run([GIT_BIN, "branch", "-M", "main"], cwd=BASE_DIR)

    # 5. Check if remote exists, or create repo via gh
    remotes = subprocess.run([GIT_BIN, "remote"], cwd=BASE_DIR, capture_output=True, text=True).stdout
    if "origin" not in remotes:
        print("[3/4] Creating remote repository on GitHub via gh CLI...")
        res = subprocess.run([GH_BIN, "repo", "create", REPO_NAME, "--public", "--description", "MacTech Android Tool v2.2 - Enterprise Diagnostic, Fake Phone & Clone Detector, Forensic ADB & MTP Suite", "--confirm"], cwd=BASE_DIR, capture_output=True, text=True)
        print(res.stdout or res.stderr)
        subprocess.run([GIT_BIN, "remote", "add", "origin", f"https://github.com/{REPO_NAME}.git"], cwd=BASE_DIR)

    # 6. Push to main
    print(f"[4/4] Pushing to {REPO_NAME} (main)...")
    push_res = subprocess.run([GIT_BIN, "push", "-u", "origin", "main"], cwd=BASE_DIR, capture_output=True, text=True)
    if push_res.returncode == 0:
        print("\n✔ Successfully synced to GitHub!")
        print(f"URL: https://github.com/{REPO_NAME}")
        return True
    else:
        print(f"[ERR] Push failed: {push_res.stderr}")
        return False

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    sync(msg)
