#!/usr/bin/env python3
import os
import subprocess
import json
import time

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {cmd}")
        return result.stdout
    else:
        print(f"❌ {cmd}")
        print(f"Error: {result.stderr}")
        return None

def main():
    print("🚀 Starting AutoGLM setup for Hisense HLTE270E...")

    with open('hisense_config.json', 'r') as f:
        config = json.load(f)

    print(f"Device: {config['device_model']} ({config['device_variant']})")

    devices = run_command("adb devices")
    if devices and "device" in devices:
        print("✅ Device connected via ADB")
    else:
        print("❌ No device found. Please connect your Hisense device and enable USB debugging.")
        return

    print("⌨️ Installing ADB Keyboard...")
    run_command("adb install Open-AutoGLM/adb_keyboard.apk")
    run_command("adb shell ime enable com.android.adbkeyboard/.AdbIME")
    run_command("adb shell ime set com.android.adbkeyboard/.AdbIME")

    print("✅ ADB Keyboard installed and enabled")

    print("🤖 Starting AutoGLM...")
    os.chdir("Open-AutoGLM")
    run_command("python3 main.py --base-url http://localhost:8000/v1 --model 'autoglm-phone-9b-multilingual'")

    print("🎉 AutoGLM setup completed!")

if __name__ == "__main__":
    main()
