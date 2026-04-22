# Release Checklist

## Current Public Release State

- arXiv link is wired in `README.md` and `docs/index.html`: <https://arxiv.org/abs/2604.16243>
- GitHub repository link is wired in the project page: <https://github.com/JethroJames/FFR>
- Static project-page checks are available via `python scripts/check_project_page.py`
- GitHub Pages can deploy either from `docs/` on `main` or through `.github/workflows/pages.yml`

## Still Recommended

- Add exact dataset access instructions and expected directory structure for each benchmark
- Expand CI beyond the current syntax-and-assets sanity workflow if you want stronger public release guarantees
- Verify the main training and evaluation paths on a Linux machine with the intended CUDA stack
- Verify the GitHub Pages site is enabled:
  - repository settings -> Pages -> source `GitHub Actions`, or
  - repository settings -> Pages -> branch `main` / folder `docs`

## Quick Sanity Checks

- `python -m compileall ffr`
- `python scripts/smoke_test.py`
- `python scripts/check_project_page.py`
- open `docs/index.html` locally and verify the page renders
- verify `git push` and GitHub Pages deployment
