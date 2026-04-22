#!/bin/bash

set -e

# ============================================================================
# Path Configuration (modify to match your environment)
# ============================================================================
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEACHER_API_DIR="${BASE_DIR}/ffr/teacher"
TRAIN_SCRIPT="${BASE_DIR}/ffr/train/grpo.py"
PYTHON_ENV="${PYTHON_ENV:-}"
OUTPUT_DIR="${OUTPUT_DIR:-${BASE_DIR}/output/grpo}"
MODEL_PATH="${MODEL_PATH:-}"
DATASET_PATH="${DATASET_PATH:-}"
VIDEO_DATA_PATH="${VIDEO_DATA_PATH:-}"
export PYTHONPATH="${BASE_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

PYTHON_BIN="${PYTHON_BIN:-python}"
TORCHRUN_BIN="${TORCHRUN_BIN:-torchrun}"
if [ -n "${PYTHON_ENV}" ]; then
    PYTHON_BIN="${PYTHON_ENV}/python"
    TORCHRUN_BIN="${PYTHON_ENV}/torchrun"
fi

MODEL_PATH="${MODEL_PATH:?Set MODEL_PATH to the base model checkpoint directory}"
DATASET_PATH="${DATASET_PATH:?Set DATASET_PATH to the RL training JSON/JSONL file}"
VIDEO_DATA_PATH="${VIDEO_DATA_PATH:?Set VIDEO_DATA_PATH to the video dataset root}"

# ============================================================================
# Training Configuration
# ============================================================================
export DEBUG_MODE="true"
export LOG_PATH="${BASE_DIR}/logs/debug_log.txt"
export FORCE_QWENVL_VIDEO_READER=decord

VIDEO_PATH_CONFIG="{\"Video-R1\":\"${VIDEO_DATA_PATH}\"}"

# FFR Configuration
USE_FFR="${USE_FFR:-true}"
TEACHER_API_URL="${TEACHER_API_URL:-http://localhost:8000}"
TEACHER_API_NFRAMES="${TEACHER_API_NFRAMES:-16}"
PATCH_TAX="${PATCH_TAX:-0.3}"

# Teacher API Configuration (requires API_KEY env var)
export API_BASE="${API_BASE:-https://api.siliconflow.cn/v1}"
export MODEL_NAME="${MODEL_NAME:-zai-org/GLM-4.5V}"
export TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-45}"

# ============================================================================
# Cleanup Function
# ============================================================================
mkdir -p "${BASE_DIR}/logs"

cleanup() {
    if [ -f "${TEACHER_API_DIR}/server.pid" ]; then
        SERVER_PID=$(cat "${TEACHER_API_DIR}/server.pid")
        kill -9 "${SERVER_PID}" 2>/dev/null || true
        rm -f "${TEACHER_API_DIR}/server.pid"
        echo "Teacher API Server stopped"
    fi
}
trap cleanup EXIT INT TERM

# ============================================================================
# Start Teacher API Server (if FFR enabled)
# ============================================================================
if [ "$USE_FFR" = "true" ]; then
    if [ -z "${API_KEY:-}" ]; then
        echo "ERROR: API_KEY environment variable is required when USE_FFR=true"
        exit 1
    fi

    echo "Starting Teacher API Server..."

    pkill -f "uvicorn ffr.teacher.server:app" 2>/dev/null || true

    cd "${BASE_DIR}"
    nohup "${PYTHON_BIN}" -m uvicorn ffr.teacher.server:app --host 0.0.0.0 --port 8000 --log-level info > "${BASE_DIR}/logs/teacher_api.log" 2>&1 &
    echo $! > "${TEACHER_API_DIR}/server.pid"

    for i in {1..10}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "Teacher API Server ready"
            break
        fi
        sleep 2
    done

fi

# ============================================================================
# Launch Training
# ============================================================================
echo "Starting GRPO Training..."
echo "  Model: ${MODEL_PATH}"
echo "  Dataset: ${DATASET_PATH}"
echo "  Output: ${OUTPUT_DIR}"
echo "  FFR: ${USE_FFR}"

"${TORCHRUN_BIN}" --nproc_per_node=8 \
    --nnodes=1 \
    --node_rank=0 \
    --master_addr=127.0.0.1 \
    --master_port=12365 \
    "${TRAIN_SCRIPT}" \
    --output_dir "${OUTPUT_DIR}" \
    --model_name_or_path "${MODEL_PATH}" \
    --dataset_name "${DATASET_PATH}" \
    --video_path "${VIDEO_PATH_CONFIG}" \
    --use_ffr "${USE_FFR}" \
    --teacher_api_url "${TEACHER_API_URL}" \
    --teacher_api_nframes "${TEACHER_API_NFRAMES}" \
    --patch_tax "${PATCH_TAX}" \
    --deepspeed "${BASE_DIR}/configs/deepspeed/zero3.json" \
    --max_prompt_length 16384 \
    --max_completion_length 1024 \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 1 \
    --learning_rate 5e-6 \
    --lr_scheduler_type "cosine" \
    --weight_decay 0.01 \
    --bf16 \
    --logging_steps 1 \
    --gradient_checkpointing true \
    --attn_implementation flash_attention_2 \
    --max_pixels 401408 \
    --num_train_epochs 2 \
    --run_name grpo-5e-6 \
    --save_strategy steps \
    --save_steps 100 \
    --beta 0.04 \
    --max_grad_norm 5 \
    --save_only_model true \
    --num_generations 8

echo "Training completed. Output: ${OUTPUT_DIR}"
