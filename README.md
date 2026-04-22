# FFR: Find, Fix, Reason

Context Repair for Video Reasoning

This repository contains the code and project page assets for **FFR (Find, Fix, Reason)**, a teacher-guided training framework for video reasoning. FFR uses a frozen teacher model to diagnose failed rollouts, provide a minimal evidence patch from the original video, and let the student reason again under the same question. The resulting repaired rollout is then integrated into GRPO with a patch tax to discourage over-reliance on teacher assistance.

## Highlights

- Observation-level intervention instead of full off-policy trajectory replacement
- Minimal evidence patches with explicit anti-leakage constraints
- GRPO-based training with teacher-guided repair
- Evaluation and ablation entry points for the main benchmarks in the paper
- A bundled GitHub Pages-style project site under [`docs/`](./docs/)
- Public paper metadata wired to arXiv: [`2604.16243`](https://arxiv.org/abs/2604.16243)

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
|   |-- check_project_page.py
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
- final arXiv and GitHub URLs in the README and project page

Still recommended for stronger reproducibility:

- publish exact model checkpoint and dataset access instructions when those artifacts are ready
- run the full training/evaluation environment on the target Linux + CUDA stack

See [`CODE_COMPLETENESS_AUDIT.md`](./CODE_COMPLETENESS_AUDIT.md) for a more detailed review.
See [`RELEASE_CHECKLIST.md`](./RELEASE_CHECKLIST.md) for the final publish checklist.

## Paper and Links

- Paper: <https://arxiv.org/abs/2604.16243>
- PDF: <https://arxiv.org/pdf/2604.16243>
- DOI: <https://doi.org/10.48550/arXiv.2604.16243>
- Code: <https://github.com/JethroJames/FFR>
- Project page: <https://jethrojames.github.io/FFR/>

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
- The shell launchers use `python` and `torchrun` from your active shell by default. Set `PYTHON_ENV=/path/to/env/bin` if you want them to call a specific Conda environment explicitly.

## Smoke Test

Before launching a full run, use the smoke test to verify the package structure and release assets:

```bash
python scripts/smoke_test.py
python scripts/check_project_page.py
```

These checks do not download models or run training. They only verify that the main Python entry points and project-page assets are wired up correctly.

## Training

### 1. Prepare environment variables

```bash
export MODEL_PATH=/path/to/Qwen2.5-VL-7B-COT-SFT
export DATASET_PATH=/path/to/rl_data.json
export VIDEO_DATA_PATH=/path/to/Video-R1-data
export API_KEY=your_teacher_api_key

# Optional: force scripts to use a specific environment instead of PATH.
export PYTHON_ENV=/path/to/your/conda/envs/ffr/bin
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

Current URLs:

- Paper: `https://arxiv.org/abs/2604.16243`
- Repository: `https://github.com/JethroJames/FFR`
- Project page: `https://jethrojames.github.io/FFR/`

For local preview, you can either open `docs/index.html` directly or run:

```bash
cd docs
python -m http.server 8000
```

If you later enable GitHub Pages, configure the repository to publish from the `docs/` directory on the `main` branch.
This repository also includes a Pages deployment workflow under `.github/workflows/pages.yml`; if you prefer Actions-based Pages, set the repository Pages source to "GitHub Actions".

## Paper Assets

Canonical public assets:

- arXiv abstract: <https://arxiv.org/abs/2604.16243>
- arXiv PDF: <https://arxiv.org/pdf/2604.16243>

Bundled local backup assets:

- Main paper: [`docs/assets/papers/ffr-paper.pdf`](./docs/assets/papers/ffr-paper.pdf)
- Supplement: [`docs/assets/papers/ffr-supplement.pdf`](./docs/assets/papers/ffr-supplement.pdf)

## Known Limitations

- Full training requires a multi-GPU Linux environment and the CUDA-specific dependencies listed in `environment.yml`.
- Teacher-guided FFR training depends on an external VLM API key and quota.
- Dataset paths are intentionally provided as examples; update `configs/dataset_config.example.json` or set `EVAL_DATA_ROOT` for your local benchmark layout.

## Citation

```bibtex
@misc{huang2026findfixreason,
  title={Find, Fix, Reason: Context Repair for Video Reasoning},
  author={Huang, Haojian and Qin, Chuanyu and Li, Yinchuan and Chen, Yingcong},
  year={2026},
  eprint={2604.16243},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  doi={10.48550/arXiv.2604.16243},
  url={https://arxiv.org/abs/2604.16243}
}
```
