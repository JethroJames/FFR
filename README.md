# FFR: Find, Fix, Reason

Context Repair for Video Reasoning

This repository contains the code and project page assets for **FFR (Find, Fix, Reason)**, a teacher-guided training framework for video reasoning. FFR uses a frozen teacher model to diagnose failed rollouts, provide a minimal evidence patch from the original video, and let the student reason again under the same question. The resulting repaired rollout is then integrated into GRPO with a patch tax to discourage over-reliance on teacher assistance.

## Highlights

- Observation-level intervention instead of full off-policy trajectory replacement
- Minimal evidence patches with explicit anti-leakage constraints
- GRPO-based training with teacher-guided repair
- Evaluation and ablation entry points for the main benchmarks in the paper
- A bundled GitHub Pages-style project site under [`docs/`](./docs/)

## Repository Layout

```text
FFR-code/
|-- configs/
|   |-- dataset_config.example.json
|   `-- deepspeed/
|-- docs/                       # GitHub Pages project site
|-- ffr/
|   |-- data/
|   |-- eval/
|   |-- teacher/
|   |-- train/
|   `-- trainer/
|-- scripts/
|   |-- run_ablation.sh
|   |-- run_eval.sh
|   |-- smoke_test.py
|   |-- train_grpo.sh
|   `-- train_sft.sh
|-- environment.yml
|-- CODE_COMPLETENESS_AUDIT.md
`-- README.md
```

## Release Status

The core research code is present, but this release should still be viewed as a **research artifact** rather than a fully turnkey product.

Already addressed in this workspace:

- package import issues in the GRPO and teacher paths
- public-facing project page under `docs/`
- basic release scaffolding (`environment.yml`, smoke test, dataset config example)

Still recommended before a public paper release:

- add your final author metadata
- add a license
- add the final arXiv URL once available
- publish exact model and data access instructions

See [`CODE_COMPLETENESS_AUDIT.md`](./CODE_COMPLETENESS_AUDIT.md) for a more detailed review.
See [`RELEASE_CHECKLIST.md`](./RELEASE_CHECKLIST.md) for the final publish checklist.

## Environment

Start from the provided Conda environment:

```bash
conda env create -f environment.yml
conda activate ffr
```

Notes:

- The environment file covers the main Python dependencies used by the codebase.
- `flash-attn` and some distributed-training dependencies are hardware/platform sensitive and may still need to be installed separately depending on your CUDA stack.
- Linux is the recommended runtime for training and evaluation.

## Smoke Test

Before launching a full run, use the smoke test to verify the package structure and release assets:

```bash
python scripts/smoke_test.py
```

This does not download models or run training. It only checks that the main Python entry points and project-page assets are wired up correctly.

## Training

### 1. Prepare environment variables

```bash
export PYTHON_ENV=/path/to/your/conda/envs/ffr/bin
export MODEL_PATH=/path/to/Qwen2.5-VL-7B-COT-SFT
export DATASET_PATH=/path/to/rl_data.json
export VIDEO_DATA_PATH=/path/to/Video-R1-data
export API_KEY=your_teacher_api_key
```

### 2. Launch GRPO + FFR

```bash
bash scripts/train_grpo.sh
```

### 3. Launch SFT

```bash
bash scripts/train_sft.sh
```

### 4. Run ablations

```bash
bash scripts/run_ablation.sh --patch_tax 0.3
```

## Evaluation

The evaluation script supports either:

- a dataset root via `EVAL_DATA_ROOT`, or
- an explicit JSON mapping file via `--dataset_config`

Example:

```bash
bash scripts/run_eval.sh \
  --model_path /path/to/checkpoint \
  --file_name release_eval \
  --output_dir ./eval_outputs \
  --datasets mmvu mvbench \
  --dataset_config configs/dataset_config.example.json
```

The expected structure of the dataset mapping file is provided in [`configs/dataset_config.example.json`](./configs/dataset_config.example.json).

## Teacher API

The teacher model runs as a separate FastAPI service during FFR training.

Relevant environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `API_KEY` | required | API key for the teacher backend |
| `API_BASE` | `https://api.siliconflow.cn/v1` | API base URL |
| `MODEL_NAME` | `zai-org/GLM-4.5V` | Teacher model name |
| `TIMEOUT_SECONDS` | `45` | Request timeout |

## Project Page

The academic project page lives in [`docs/`](./docs/) and is ready for GitHub Pages deployment.

Suggested public URLs:

- Repository: `https://github.com/JethroJames/FFR`
- Project page: `https://jethrojames.github.io/FFR/`

If you use GitHub Pages, configure the repository to publish from the `docs/` directory on the `main` branch.

## Paper Assets

Bundled local assets:

- Main paper: [`docs/assets/papers/ffr-paper.pdf`](./docs/assets/papers/ffr-paper.pdf)
- Supplement: [`docs/assets/papers/ffr-supplement.pdf`](./docs/assets/papers/ffr-supplement.pdf)

## Citation

```bibtex
@inproceedings{ffr2026,
  title={Find, Fix, Reason: Context Repair for Video Reasoning},
  booktitle={ICML},
  year={2026}
}
```
