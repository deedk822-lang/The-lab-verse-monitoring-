#!/bin/bash

# --- CONFIGURATION ---
LOG_DIR="logs"
mkdir -p $LOG_DIR
TODAY=$(date +%Y-%m-%d)

echo "🌞 STARTING EMPIRE OPERATIONS [$TODAY]..."

# --- FUNCTION: RUN WITH PROTECTION ---
# This wrapper executes the Python script and catches crashes.
run_protected_job() {
    JOB_NAME=$1
    SCRIPT_PATH=$2
    LOG_FILE="$LOG_DIR/${JOB_NAME}_${TODAY}.log"

    echo "   ▶ Running $JOB_NAME..."
    
    # 1. EXECUTE (Capture stdout and stderr)
    python3 $SCRIPT_PATH > "$LOG_FILE" 2>&1
    EXIT_CODE=$?

    # 2. CHECK FOR CRASH
    if [ $EXIT_CODE -ne 0 ]; then
        echo "   ⚠️ $JOB_NAME CRASHED (Exit Code: $EXIT_CODE)."
        echo "   🚑 ACTIVATING QWEN SYSADMIN (Auto-Repair)..."
        
        # 3. SELF-HEALING PROTOCOL
        # We pass the *path* to the log file so Qwen can read the traceback safely.
        export PYTHONPATH=$PYTHONPATH:$(pwd)
        python3 -c "
import sys
from vaal_ai_empire.src.core.alibaba_sysadmin_core import MasterController
admin = MasterController()
print(admin.heal_from_file('$LOG_FILE'))
"
        echo "   ✅ RECOVERY SEQUENCE FINISHED."
    else
        echo "   ✅ $JOB_NAME Completed Successfully."
    fi
}

# --- DAILY SCHEDULE ---

# 1. JSE SPECIALIST (Market Data)
run_protected_job "JSE_Analysis" "vaal-ai-empire/src/agents/jse_specialist.py"

# 2. TAX AGENT (Revenue & Compliance)
run_protected_job "Tax_Compliance" "vaal-ai-empire/src/agents/tax_collector.py"

# 3. SYSTEM AUDIT (Dependency Security)
run_protected_job "System_Audit" "vaal-ai-empire/scripts/maintenance/audit_system.py"

echo "🌙 OPERATIONS COMPLETE."