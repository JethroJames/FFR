#!/bin/bash

export NCCL_P2P_DISABLE=1
export NCCL_IB_DISABLE=1
export DEBUG_MODE="true"
export DECORD_EOF_RETRY_MAX=20480
export FORCE_QWENVL_VIDEO_READER=decord

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Default values (override via command line or env vars)
MODEL_PATH="${MODEL_PATH:-${BASE_DIR}/output/grpo/checkpoint-200}"
FILE_NAME="${FILE_NAME:-default}"
OUTPUT_DIR="${OUTPUT_DIR:-${BASE_DIR}/eval/outputs}"
CUDA_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1,2,3}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model_path) MODEL_PATH="$2"; shift 2 ;;
        --file_name) FILE_NAME="$2"; shift 2 ;;
        --output_dir) OUTPUT_DIR="$2"; shift 2 ;;
        --datasets) DATASETS="$2"; shift 2 ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

export CUDA_VISIBLE_DEVICES=${CUDA_DEVICES}
export LOG_PATH="${BASE_DIR}/logs/debug_log_eval.txt"
mkdir -p "${BASE_DIR}/logs"

echo "Running evaluation..."
echo "  Model: ${MODEL_PATH}"
echo "  Output: ${OUTPUT_DIR}"

EVAL_CMD="python ${BASE_DIR}/ffr/eval/eval_bench.py \
    --model_path ${MODEL_PATH} \
    --file_name ${FILE_NAME} \
    --output_dir ${OUTPUT_DIR}"

if [ -n "${DATASETS}" ]; then
    EVAL_CMD="${EVAL_CMD} --datasets ${DATASETS}"
fi

eval ${EVAL_CMD}

echo "Evaluation completed. Output: ${OUTPUT_DIR}"
