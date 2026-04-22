#!/bin/bash

set -e

export NCCL_P2P_DISABLE=1
export NCCL_IB_DISABLE=1
export DEBUG_MODE="true"
export DECORD_EOF_RETRY_MAX=20480
export FORCE_QWENVL_VIDEO_READER=decord

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_ENV="${PYTHON_ENV:-}"
PYTHON_BIN="${PYTHON_BIN:-python}"
if [ -n "${PYTHON_ENV}" ]; then
    PYTHON_BIN="${PYTHON_ENV}/python"
fi

# Default values (override via command line or env vars)
MODEL_PATH="${MODEL_PATH:-${BASE_DIR}/output/grpo/checkpoint-200}"
FILE_NAME="${FILE_NAME:-default}"
OUTPUT_DIR="${OUTPUT_DIR:-${BASE_DIR}/eval/outputs}"
CUDA_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1,2,3}"
DATASET_CONFIG="${DATASET_CONFIG:-}"
DATASETS=()
EXTRA_ARGS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model_path) MODEL_PATH="$2"; shift 2 ;;
        --file_name) FILE_NAME="$2"; shift 2 ;;
        --output_dir) OUTPUT_DIR="$2"; shift 2 ;;
        --dataset_config) DATASET_CONFIG="$2"; shift 2 ;;
        --datasets)
            shift
            while [[ $# -gt 0 && "$1" != --* ]]; do
                DATASETS+=("$1")
                shift
            done
            ;;
        --nframes|--temperature|--top_p|--max_tokens|--max_model_len|--gpu_mem_util)
            EXTRA_ARGS+=("$1" "$2")
            shift 2
            ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

export CUDA_VISIBLE_DEVICES="${CUDA_DEVICES}"
export LOG_PATH="${BASE_DIR}/logs/debug_log_eval.txt"
mkdir -p "${BASE_DIR}/logs"

echo "Running evaluation..."
echo "  Model: ${MODEL_PATH}"
echo "  Output: ${OUTPUT_DIR}"

EVAL_CMD=(
    "${PYTHON_BIN}" "${BASE_DIR}/ffr/eval/eval_bench.py"
    --model_path "${MODEL_PATH}"
    --file_name "${FILE_NAME}"
    --output_dir "${OUTPUT_DIR}"
)

if [ ${#DATASETS[@]} -gt 0 ]; then
    EVAL_CMD+=(--datasets "${DATASETS[@]}")
fi

if [ -n "${DATASET_CONFIG}" ]; then
    EVAL_CMD+=(--dataset_config "${DATASET_CONFIG}")
fi

if [ ${#EXTRA_ARGS[@]} -gt 0 ]; then
    EVAL_CMD+=("${EXTRA_ARGS[@]}")
fi

"${EVAL_CMD[@]}"

echo "Evaluation completed. Output: ${OUTPUT_DIR}"
