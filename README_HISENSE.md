# Hisense HLTE270E AutoGLM Setup Guide

## Device Information
- **Model**: Hisense HLTE270E
- **Variant**: S03_01_01_ZA06
- **Android Version**: Android OS
- **Supported**: ✅ Yes

## Setup Steps

### 1. Enable Developer Options
1. Go to **Settings** > **About Phone**
2. Tap **Build Number** 7-8 times
3. Developer Options will appear in Settings

### 2. Enable USB Debugging
1. Go to **Settings** > **Developer Options**
2. Enable **USB Debugging**
3. Connect device to computer via USB
4. Allow USB debugging when prompted

### 3. Run Setup Script
```bash
python3 setup_autoglm.py
```

## Usage
```python
from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig

config = ModelConfig(
    base_url="http://localhost:8000/v1",
    model_name="autoglm-phone-9b-multilingual"
)

agent = PhoneAgent(model_config=config)
result = agent.run("Open Chrome and search for AutoGLM")
```

## Troubleshooting

### Device Not Detected
1. Check USB cable (must support data transfer)
2. Re-enable USB debugging
3. Restart ADB: `adb kill-server && adb start-server`

### ADB Keyboard Not Working
1. Reinstall ADB Keyboard: `adb install Open-AutoGLM/adb_keyboard.apk`
2. Enable in Settings: `adb shell ime enable com.android.adbkeyboard/.AdbIME`
3. Set as default: `adb shell ime set com.android.adbkeyboard/.AdbIME`

## Wireless Setup
```bash
adb tcpip 5555
adb connect 192.168.1.XXX:5555
```
