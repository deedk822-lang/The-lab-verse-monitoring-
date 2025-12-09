#!/bin/bash

# 1. SECURITY CHECKS (Input Validation)
# We ensure the tool has the necessary keys before attempting to run.
if [ -z "$PERSONAL_ACCESS_TOKEN" ]; then
    echo "❌ CRITICAL: PERSONAL_ACCESS_TOKEN is missing from environment."
    echo "   Action: Export your GitHub token to allow code patching."
    exit 1
fi

if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "❌ CRITICAL: DASHSCOPE_API_KEY is missing."
    echo "   Action: Export your Qwen API key."
    exit 1
fi

if ! command -v aliyun &> /dev/null; then
    echo "❌ CRITICAL: 'aliyun' CLI not installed or not in PATH."
    exit 1
fi

# 2. REAL DATA ACQUISITION
# We query Alibaba Cloud for active vulnerabilities in the Singapore region.
echo "🔍 Querying Alibaba Cloud Security Center (ap-southeast-1)..."

# Fetching critical vulnerabilities (Linux software CVEs)
# We store this in a variable safely.
SCAN_JSON=$(aliyun sas DescribeVulnerabilities \
  --RegionId ap-southeast-1 \
  --Type "cve" \
  --Status "y" \
  --Output "json" \
  2>/dev/null)

# 3. LOGIC GATING (The Decision Layer)
# We parse the JSON to see if there are actually any risks.
# We use Python for safe JSON parsing instead of fragile grep/sed.

export RAW_SCAN_DATA="$SCAN_JSON"
export PYTHONPATH=$PYTHONPATH:$(pwd)

python3 -c "
import os
import sys
import json

# Safely load data from environment
raw_data = os.getenv('RAW_SCAN_DATA', '{}')

try:
    data = json.loads(raw_data)
    total_count = data.get('TotalCount', 0)

    if total_count == 0:
        print('✅ STATUS: SECURE. Alibaba SAS reports 0 active vulnerabilities.')
        sys.exit(0) # Exit cleanly, nothing to do

    print(f'⚠️ STATUS: VULNERABLE. Found {total_count} issues.')
    print('🚑 INITIATING QWEN REMEDIATION PROTOCOL...')

    # IMPORT THE CORE (Only if we have work to do)
    from vaal_ai_empire.src.core.alibaba_sysadmin_core import MasterController

    admin = MasterController()

    # We pass the raw JSON to Qwen so it can read the CVE details
    fix_report = admin.patch_security_vulnerability(json.dumps(data, indent=2))

    print('📝 REMEDIATION REPORT:')
    print(fix_report)

except json.JSONDecodeError:
    print('❌ ERROR: Invalid JSON response from Alibaba CLI. Check permissions.')
    sys.exit(1)
except ImportError:
    print('❌ ERROR: Could not load MasterController. Check src/core path.')
    sys.exit(1)
except Exception as e:
    print(f'❌ UNEXPECTED ERROR: {e}')
    sys.exit(1)
"
