#!/bin/bash
# start-kimi.sh
export CUDA_VISIBLE_DEVICES=0,1,2,3

vllm serve $MODEL_NAME \
  --port 8000 \
  --tensor-parallel-size 4 \
  --max-model-len 32768 \
  --trust-remote-code \
  --gpu-memory-utilization 0.95 \
  --max-num-batched-tokens 8192
