"""
Helper script to package Open-Wheel Motorsport Management Tycoon locally.

Usage:
    python scripts/build_installer.py
"""

import os
import sys
import shutil
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPEC_PATH = os.path.join(PROJECT_ROOT, "packaging", "MotorsportTycoon.spec")
ISS_PATH = os.path.join(PROJECT_ROOT, "packaging", "installer.iss")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist", "MotorsportTycoon")
INSTALLER_DIR = os.path.join(PROJECT_ROOT, "dist_installer")

def main():
    print("=" * 60)
    print("  Motorsport Tycoon - Local Build & Packaging Script")
    print("=" * 60)

    # 1. Run PyInstaller
    print("\n[1/3] Compiling application bundle with PyInstaller...")
    cmd_pyinstaller = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        SPEC_PATH
    ]
    res = subprocess.run(cmd_pyinstaller, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print("\n[ERROR] PyInstaller failed to compile the application.")
        sys.exit(res.returncode)
    print(f"[OK] Application bundle generated at: {DIST_DIR}")

    # 2. Check for Inno Setup Compiler (ISCC)
    print("\n[2/3] Checking for Inno Setup (ISCC.exe)...")
    iscc_path = shutil.which("iscc")
    if not iscc_path:
        # Check standard default installation location
        candidate = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
        if os.path.exists(candidate):
            iscc_path = candidate

    if iscc_path:
        print(f"Found Inno Setup at: {iscc_path}")
        print("\n[3/3] Compiling Windows Setup Installer (.exe)...")
        res = subprocess.run([iscc_path, ISS_PATH], cwd=PROJECT_ROOT)
        if res.returncode != 0:
            print("\n[ERROR] Inno Setup compilation failed.")
            sys.exit(res.returncode)
        print(f"[OK] Setup Installer generated in: {INSTALLER_DIR}")
    else:
        print("[NOTICE] Inno Setup (iscc) was not found on your local system PATH.")
        print("To build the installer .exe locally, install Inno Setup 6 (https://jrsoftware.org/isinfo.php).")
        print("Note: GitHub Actions will automatically compile the installer on push/release!")
        print(f"Your portable application folder is ready at: {DIST_DIR}")

    print("\n" + "=" * 60)
    print("Build step complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
