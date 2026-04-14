#!/bin/bash

set -e

# ============================================================================
# Configuration
# ============================================================================
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_ENV="${PYTHON_ENV:-/yourpath/miniconda3/envs/video-r1/bin}"

MODEL_PATH="${MODEL_PATH:-/yourpath/video_reasoning/model/Qwen2.5-VL-7B-COT-SFT}"
DATASET_PATH="${DATASET_PATH:-${BASE_DIR}/data/sft/qwen3-235B-sft-data/sft_train_data.json}"
VIDEO_DATA_PATH="${VIDEO_DATA_PATH:-/yourpath/video_reasoning/data/train/Video-R1-data}"
OUTPUT_DIR="${OUTPUT_DIR:-${BASE_DIR}/output/sft_235B}"

export DEBUG_MODE="true"
export LOG_PATH="${BASE_DIR}/logs/debug_log_sft.txt"
export FORCE_QWENVL_VIDEO_READER=decord

mkdir -p "${BASE_DIR}/logs"

# ============================================================================
# Launch Training
# ============================================================================
echo "Starting SFT Training..."
echo "  Model: ${MODEL_PATH}"
echo "  Dataset: ${DATASET_PATH}"
echo "  Output: ${OUTPUT_DIR}"

CUDA_VISIBLE_DEVICES=4,5,6,7 ${PYTHON_ENV}/torchrun --nproc_per_node=4 \
    --nnodes=1 \
    --node_rank=0 \
    --master_addr=127.0.0.1 \
    --master_port=12349 \
    "${BASE_DIR}/ffr/train/sft.py" \
    --output_dir "${OUTPUT_DIR}" \
    --model_name_or_path "${MODEL_PATH}" \
    --dataset_name "${DATASET_PATH}" \
    --video_path "{\"Video-R1\":\"${VIDEO_DATA_PATH}\"}" \
    --deepspeed "${BASE_DIR}/configs/deepspeed/zero2.json" \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 2 \
    --learning_rate 1e-5 \
    --logging_steps 1 \
    --bf16 \
    --report_to tensorboard \
    --gradient_checkpointing true \
    --attn_implementation flash_attention_2 \
    --num_train_epochs 5 \
    --run_name "sft-video" \
    --save_strategy epoch \
    --max_grad_norm 5 \
    --save_only_model true \
    --max_length 8192

echo "Training completed. Output: ${OUTPUT_DIR}"
