#!/usr/bin/env python3
"""
Quick test script for Humbly Plural app
Run this to verify the app launches correctly
"""

import subprocess
import sys
import os

def test_app():
    """Test if the Humbly Plural app runs correctly"""
    exe_path = os.path.join("dist", "HumblyPlural.exe")

    if not os.path.exists(exe_path):
        print("❌ Error: HumblyPlural.exe not found in dist/ directory")
        print("Please run: pyinstaller --windowed --name HumblyPlural humbly_plural.py")
        return False

    try:
        print("🚀 Launching Humbly Plural app...")
        print("Note: The app window should open. Close it manually to continue.")

        # Launch the app (it will run in background)
        process = subprocess.Popen([exe_path])

        # Wait a moment for it to start
        import time
        time.sleep(3)

        # Check if process is still running (good sign!)
        if process.poll() is None:
            print("✅ App launched successfully!")
            print("💡 The app is running. Please test its features:")
            print("   - Add members")
            print("   - Create switches")
            print("   - Write notes")
            print("   - Check statistics")
            return True
        else:
            print("❌ App failed to start or crashed immediately")
            return False

    except Exception as e:
        print(f"❌ Error running app: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Humbly Plural App")
    print("=" * 40)

    success = test_app()

    if success:
        print("\n🎉 Test passed! Your app is ready for distribution.")
        print("📦 Upload HumblyPlural.exe to share with your community!")
    else:
        print("\n❌ Test failed. Please check the build process.")

    input("\nPress Enter to exit...")