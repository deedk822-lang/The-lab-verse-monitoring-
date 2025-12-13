#!/bin/bash

# --- 1. STRICT CREDENTIAL VALIDATION ---
if [[ "$PERSONAL_ACCESS_TOKEN" == *"placeholder"* ]] || [ -z "$PERSONAL_ACCESS_TOKEN" ]; then
    echo "❌ CRITICAL ERROR: Invalid PERSONAL_ACCESS_TOKEN."
    exit 1
fi

if ! command -v aliyun &> /dev/null; then
    echo "❌ CRITICAL ERROR: 'aliyun' CLI is missing."
    exit 1
fi

echo "🛡️ STARTING REAL-TIME SECURITY PATROL..."

# --- 2. LIVE DATA ACQUISITION ---
# Query Alibaba Cloud Security Center (Singapore Region)
echo "   > Querying Alibaba SAS (ap-southeast-1)..."

SCAN_JSON=$(aliyun sas DescribeVulnerabilities \
  --RegionId ap-southeast-1 \
  --Type "cve" \
  --Status "y" \
  --Output "json" \
  2>/dev/null)

# --- 3. INTELLIGENT REMEDIATION ---
export RAW_SCAN_DATA="$SCAN_JSON"
export PYTHONPATH=$PYTHONPATH:$(pwd)

python3 -c "
import os
import sys
import json

try:
    # Load Real Data
    raw = os.getenv('RAW_SCAN_DATA', '{}')
    data = json.loads(raw)
    total_count = data.get('TotalCount', 0)
    
    if total_count == 0:
        print('✅ STATUS: SECURE. Alibaba SAS reports 0 active vulnerabilities.')
        sys.exit(0)
        
    print(f'🚨 THREAT LEVEL RED: Found {total_count} active vulnerabilities.')
    print('🚑 INITIATING QWEN REMEDIATION PROTOCOL...')
    
    # Import Qwen Security Engineer
    from vaal_ai_empire.src.core.alibaba_sysadmin_core import MasterController
    admin = MasterController()
    
    # Qwen fixes the code based on the CVE report
    report = admin.patch_security_vulnerability(json.dumps(data, indent=2))
    print(report)

except Exception as e:
    print(f'❌ ERROR: {e}')
    sys.exit(1)
"