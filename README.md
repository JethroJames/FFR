# Find, Fix, Reason

FFR trains video reasoners with teacher-guided context repair: failed rollouts receive a small evidence patch from a frozen teacher, and the repaired rollout is used in GRPO with a penalty on teacher assistance.

## Repository Layout

```text
configs/                    Example dataset and DeepSpeed configs
docs/                       Project page assets
ffr/                        Training, teacher, data, and evaluation code
scripts/                    Launchers and sanity checks
environment.yml             Conda environment
```

## Setup

Linux with CUDA is recommended for training and evaluation.

```bash
conda env create -f environment.yml
conda activate ffr
```

Some CUDA-dependent packages, such as `flash-attn`, may need local installation for your driver and PyTorch stack. After setup, run:

```bash
python scripts/smoke_test.py
```

The smoke test checks imports, script wiring, and required public assets. It does not download models or run training.

## Data

Training data can be `.json` or `.jsonl`. Each sample should include the fields used by the launchers:

| Field | Description |
| --- | --- |
| `problem_id` | Stable sample id |
| `data_source` | Dataset key used to resolve the video root |
| `path` | Relative or absolute video path |
| `data_type` | Usually `video` |
| `problem_type` | Question type, such as `multiple choice` or `free-form` |
| `problem` | Question text |
| `options` | Multiple-choice options, when needed |
| `solution` | Ground-truth answer, usually in `<answer>...</answer>` format |
| `process` | Reference reasoning trace for SFT |

For evaluation datasets, start from [`configs/dataset_config.example.json`](./configs/dataset_config.example.json).

## Training

Set paths and teacher API access:

```bash
export MODEL_PATH=/path/to/base-or-sft-checkpoint
export DATASET_PATH=/path/to/train.json
export VIDEO_DATA_PATH=/path/to/video/root
export API_KEY=your_teacher_api_key
```

Optional teacher settings:

```bash
export API_BASE=https://api.siliconflow.cn/v1
export MODEL_NAME=zai-org/GLM-4.5V
export TIMEOUT_SECONDS=45
```

Launch GRPO with FFR:

```bash
bash scripts/train_grpo.sh
```

Launch SFT:

```bash
bash scripts/train_sft.sh
```

To force a specific environment, set:

```bash
export PYTHON_ENV=/path/to/conda/envs/ffr/bin
```

## Evaluation

Example:

```bash
bash scripts/run_eval.sh \
  --model_path /path/to/checkpoint \
  --file_name release_eval \
  --output_dir ./eval_outputs \
  --datasets mmvu mvbench \
  --dataset_config configs/dataset_config.example.json
```

You can also set `EVAL_DATA_ROOT` if your benchmark files follow the expected local layout.

## Notes

This release is not a one-command reproduction package; adjust paths, cluster settings, checkpoints, datasets, and teacher API access for your local setup.

## Citation

```bibtex
@article{huang2026find,
  title={Find, Fix, Reason: Context Repair for Video Reasoning},
  author={Huang, Haojian and Qin, Chuanyu and Li, Yinchuan and Chen, Yingcong},
  journal={arXiv preprint arXiv:2604.16243},
  year={2026}
}
```
