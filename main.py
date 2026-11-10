"""
MaTech Android Tool - Main Entry Point
MacTech Solutions Lab
Automated Android Diagnostic, Authenticity Forensic Suite & ADB Controller
"""

import sys
import os

# Ensure package roots are correctly placed in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.adb_manager import ADBManager
from src.ui.main_window import MainWindow

def main():
    try:
        adb_mgr = ADBManager()
        app = MainWindow(adb_manager=adb_mgr)
        app.mainloop()
    except Exception as e:
        print(f"Error launching MaTech Android Tool: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
