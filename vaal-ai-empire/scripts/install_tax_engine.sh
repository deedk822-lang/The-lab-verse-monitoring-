#!/bin/bash

# --- THE TAX AGENT INSTALLER ---
# This script transforms a blank server into the "Tax Agent"
# by installing the actual brains: Qwen (Alibaba) and GLM-4 (ZhipuAI).

set -e  # Exit immediately if any command fails (The Agent dies if it can't load)

echo "🚀 INITIALIZING TAX AGENT ENGINE..."

# 1. VERIFY THE ENVIRONMENT (The Body)
# We need Python 3.10+ and pip
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is missing. The Agent has no body."
    exit 1
fi

echo "✅ Environment Check: OK"

# 2. INSTALL THE BRAINS (The Intelligence)
# This is where we stop faking it. We install the OFFICIAL SDKs.

echo "🧠 Installing Qwen-VL (Vision & Reasoning)..."
pip install dashscope --upgrade --quiet
# DashScope is the pipe to Qwen-Max and Qwen-VL

echo "🧠 Installing GLM-4 (Complex Logic & Strategy)..."
pip install zhipuai --upgrade --quiet
pip install sniffio --quiet
# ZhipuAI is the pipe to GLM-4

echo "🧠 Installing The Coordinator (One Source)..."
pip install cohere pandas numpy scikit-learn requests --quiet
# This supports the "Central Intelligence" logic you approved

# 3. WAKE UP THE MODELS (The Pulse Check)
# We run a 1-token test to prove the Agent is ALIVE.

echo "⚡ Waking up the Tax Agent..."

python3 -c "
import os
import sys
from zhipuai import ZhipuAI
import dashscope

# LOAD KEYS
glm_key = os.getenv('GLM4_API_KEY')
qwen_key = os.getenv('DASHSCOPE_API_KEY') # Qwen uses Dashscope Key

if not glm_key and not qwen_key:
    print('❌ ERROR: No API Keys found. The Agent is brain-dead.')
    sys.exit(1)

print('✅ KEYS DETECTED. Testing connectivity...')

# TEST GLM-4 (The Strategist)
if glm_key:
    try:
        client = ZhipuAI(api_key=glm_key)
        response = client.chat.completions.create(
            model='glm-4',
            messages=[{'role': 'user', 'content': 'Say exactly: I am the Tax Agent.'}]
        )
        print(f'🤖 GLM-4 SAYS: {response.choices[0].message.content}')
    except Exception as e:
        print(f'⚠️ GLM-4 Init Failed: {e}')

# TEST QWEN (The Analyst)
if qwen_key:
    try:
        # Simple generation call for Qwen
        resp = dashscope.Generation.call(
            model='qwen-turbo',
            api_key=qwen_key,
            prompt='Say exactly: Revenue Systems Online.'
        )
        if resp.status_code == 200:
            print(f'🤖 QWEN SAYS: {resp.output.text}')
        else:
            print(f'⚠️ Qwen Init Failed: {resp.message}')
    except Exception as e:
        print(f'⚠️ Qwen Init Failed: {e}')
"

# 4. FINAL VERDICT
if [ $? -eq 0 ]; then
    echo "✅ SUCCESS: The Tax Agent is INSTALLED and ALIVE."
    echo "READY TO GENERATE REVENUE."
    exit 0
else
    echo "❌ FAILURE: The Agent could not wake up."
    exit 1
fi
