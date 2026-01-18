#!/bin/bash
# scripts/verify-rollback.sh
# Script to verify rollback status after ECS command execution

set -e

COMMAND_ID="$1"
REGION="${2:-cn-hangzhou}"

if [ -z "$COMMAND_ID" ]; then
    echo "Error: Command ID is required"
    exit 1
fi

echo "Verifying rollback command status: $COMMAND_ID"

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    INVOKE_STATUS=$(aliyun ecs DescribeInvocations --RegionId $REGION --InvokeId "$COMMAND_ID" --query 'Invocations.Invocation[0].InvokeStatus' --output text)

    if [[ "$INVOKE_STATUS" == "Finished" ]]; then
        echo "✅ Rollback script finished successfully."
        exit 0
    elif [[ "$INVOKE_STATUS" == "Failed" || "$INVOKE_STATUS" == "Stopped" ]]; then
        echo "❌ Rollback script failed with status: $INVOKE_STATUS"
        exit 1
    else
        echo "Rollback in progress... (attempt $((ATTEMPT+1))/$MAX_ATTEMPTS)"
        sleep 10
    fi

    ATTEMPT=$((ATTEMPT+1))
done

echo "Timeout waiting for rollback to complete"
exit 1
