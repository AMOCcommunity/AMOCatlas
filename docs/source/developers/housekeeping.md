# Project Maintenance Checklist

Quick reference for maintaining AMOCatlas development environment and processes.

---

## Dependencies

**Adding packages** (dependencies live in `pyproject.toml`):
- ✅ Runtime needs → add to `[project] dependencies`
- ✅ Test / docs / lint only → add to the matching extra under `[project.optional-dependencies]` (`test`, `docs`, `dev`)
- ✅ Update GitHub Actions if CI needs it

**Updating packages:**
- ✅ Test locally first
- ✅ Recreate virtual environment if major changes
- ✅ Verify CI still passes

---

## Environment Refresh

When things get messy:
```bash
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest  # Verify everything works
```

---

## Pre-merge Checklist

Before merging any PR:
- ✅ `pytest` passes locally
- ✅ `ruff check .` and `ruff format --check .` pass  
- ✅ Run demo notebooks: `demo.ipynb` (check for errors)
- ✅ Clear all notebook outputs before committing
  - **Exception**: `amoc_paperfigs.ipynb` should keep outputs (requires PyGMT/GMT not available in CI)
- ✅ GitHub Actions CI is green
- ✅ Consider "Squash and merge" for cleaner history

---

## Documentation

**When adding docs dependencies:**
- ✅ Add to the `docs` extra under `[project.optional-dependencies]` in `pyproject.toml`
- ✅ Test build: `cd docs && make clean html`
- ✅ Verify GitHub Actions docs build passes

---

*For detailed workflows, see the {doc}`developer_guide`.*

