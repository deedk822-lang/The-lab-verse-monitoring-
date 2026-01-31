#!/bin/bash
echo "🔌 Setting up ADB for Hisense HLTE270E..."
wget -q https://dl.google.com/android/repository/platform-tools-latest-linux.zip
unzip -q platform-tools-latest-linux.zip
export PATH=$PWD/platform-tools:$PATH
echo "📋 ADB Version:"
adb version
echo "✅ ADB setup completed!"
echo "📱 Please connect your Hisense device and enable USB debugging."
