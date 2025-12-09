#!/bin/bash

# --- CONFIGURATION ---
# Define the logs so Qwen can read them if things break
LOG_DIR="logs"
mkdir -p $LOG_DIR
TODAY=$(date +%Y-%m-%d)

echo "🌞 STARTING DAILY EMPIRE OPERATIONS [$TODAY]..."

# Set Python path to include the project root
export PYTHONPATH=$PWD

# --- FUNCTION: RUN WITH PROTECTION ---
# This wrapper performs the "Trigger" logic you described.
run_protected_job() {
    JOB_NAME=$1
    SCRIPT_PATH=$2
    LOG_FILE="$LOG_DIR/${JOB_NAME}_${TODAY}.log"

    echo "   ▶ Running $JOB_NAME..."

    # 1. EXECUTE THE AGENT (Capture Output)
    python3 $SCRIPT_PATH > $LOG_FILE 2>&1
    EXIT_CODE=$?

    # 2. CHECK FOR CRASH (The Trigger)
    if [ $EXIT_CODE -ne 0 ]; then
        echo "   ⚠️ $JOB_NAME CRASHED (Exit Code: $EXIT_CODE)."
        echo "   🚑 ACTIVATING QWEN SYSADMIN..."

        # 3. WAKE THE BRAIN (Qwen reads the log and fixes the code)
        # We pass the error log file path to the SysAdmin Core
        python3 vaal-ai-empire/src/core/alibaba_sysadmin_core.py "$LOG_FILE"

        echo "   ✅ RECOVERY SEQUENCE FINISHED."
    else
        echo "   ✅ $JOB_NAME Completed Successfully."
    fi
}

# --- DAILY SCHEDULE ---

# 1. JSE SPECIALIST (Check the Markets)
run_protected_job "JSE_Analysis" "vaal-ai-empire/src/agents/jse_specialist.py"

# 2. TAX AGENT (Check the Compliance/Revenue)
run_protected_job "Tax_Compliance" "vaal-ai-empire/src/agents/tax_collector.py"

# 3. SYSTEM AUDIT (Check the Dependencies)
# Qwen checks if libraries are outdated
run_protected_job "System_Audit" "vaal-ai-empire/scripts/maintenance/audit_system.py"

echo "🌙 OPERATIONS COMPLETE."
