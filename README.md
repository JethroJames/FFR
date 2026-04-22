# Find, Fix, Reason

Code and project page for **Find, Fix, Reason: Context Repair for Video Reasoning**.

FFR trains video reasoners with a teacher-guided context repair step. When a rollout fails, a frozen teacher identifies the missing or wrong visual context, provides a small evidence patch from the original video, and the student retries the same question. The repaired rollout is then used in GRPO with a penalty on teacher assistance.

- Paper: <https://arxiv.org/abs/2604.16243>
- Project page: <https://jethrojames.github.io/FFR/>
- Appendix PDF: [`docs/assets/papers/ffr-appendix.pdf`](./docs/assets/papers/ffr-appendix.pdf)

This repository is a research release. Training still requires the relevant datasets, model checkpoints, video files, and teacher API access.

## Repository Layout

```text
configs/                    Example dataset and DeepSpeed configs
docs/                       Static project page for GitHub Pages
ffr/                        Training, teacher, data, and evaluation code
scripts/                    Launchers and sanity checks
environment.yml             Conda environment
CODE_COMPLETENESS_AUDIT.md  Notes on current code coverage and limitations
```

## Setup

Linux with CUDA is recommended for training and evaluation.

```bash
conda env create -f environment.yml
conda activate ffr
```

Some CUDA-dependent packages, such as `flash-attn`, may need to be installed separately for your local driver and PyTorch stack.

Run the lightweight checks first:

```bash
python scripts/smoke_test.py
python scripts/check_project_page.py
```

These checks only verify imports, script wiring, and website assets. They do not download models or run training.

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

Set the main paths and teacher API key:

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

The shell launchers use `python` and `torchrun` from the active environment. To force a specific environment, set:

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

## Project Page

The project page is a static site under [`docs/`](./docs/).

Local preview:

```bash
python -m http.server 8000 --directory docs
```

Then open:

```text
http://127.0.0.1:8000/
```

Deployment is handled by [`.github/workflows/pages.yml`](./.github/workflows/pages.yml). After GitHub Pages is enabled for the repository, pushes to `main` that change `docs/**` will publish the site to:

```text
https://jethrojames.github.io/FFR/
```

If the first deployment does not start automatically, run the `deploy-pages` workflow manually from the repository's Actions tab.

## Notes

- Full training has not been packaged as a one-command reproduction; paths and cluster settings should be adjusted locally.
- Teacher-guided repair depends on external VLM API availability and quota.
- Checkpoint and dataset release details should be filled in when those artifacts are ready.

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
