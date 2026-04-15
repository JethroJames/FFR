# Release Checklist

## Must Do Before Public Paper Release

- Fill in final author names and affiliations in the project page:
  - `docs/assets/data/site-data.js`
- Add the final arXiv link once the paper is live:
  - `docs/assets/data/site-data.js`
  - `README.md`
- Choose and add a repository license:
  - `LICENSE`
- Verify the GitHub Pages site is enabled:
  - repository settings -> Pages -> branch `main` / folder `docs`
- Verify the main training and evaluation paths on a Linux machine with the intended CUDA stack

## Recommended

- Replace placeholder environment paths in shell scripts with your actual internal examples if you want the docs to be more concrete
- Add exact dataset access instructions and expected directory structure for each benchmark
- Expand CI beyond the current syntax-and-assets sanity workflow if you want stronger public release guarantees
- Add one short "known limitations" section to the README

## Quick Sanity Checks

- `python -m compileall ffr`
- `python scripts/smoke_test.py`
- open `docs/index.html` locally and verify the page renders
- verify `git push` and GitHub Pages deployment
