# Kaggle solutions — moved to a separate branch

The original 4,094-file `kaggle_solutions/` tree (≈ 53 MB) was moved out of
`main` on 2026-05-10 to keep clone times reasonable. The full content lives
in the `archive/kaggle-solutions-2026` branch.

## To get the archive

```bash
# Inspect without checkout:
git fetch origin archive/kaggle-solutions-2026
git ls-tree origin/archive/kaggle-solutions-2026 -- kaggle_solutions/

# Or check it out into a worktree:
git worktree add ../kaggle-archive archive/kaggle-solutions-2026

# Or just clone the branch directly:
git clone -b archive/kaggle-solutions-2026 \
    https://github.com/markl-a/Data-Analysis-with-Agents kaggle-archive
```

## Why this happened

The `app.py` Streamlit dashboard + the demo path (`make demo` /
`streamlit run app.py`) don't depend on `kaggle_solutions/` at all — those
were tutorial-style worked examples that bloated the main branch's clone
size by ~5×. Recruiters / first-time contributors clone main; the kaggle
material is preserved verbatim on the archive branch for anyone who
specifically wants it.
