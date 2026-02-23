# T11: Repository Restructuring Plan

## Summary

This document outlines the plan to reorganize the factory-testing repository by consolidating all project code into the `projects/` subfolder, with each project in its own folder. The root should contain only: `projects/`, `.git/`, `.gitignore`, `README.md`, `requirements.txt`, and config files.

---

## 1. Current State

### Directory Structure (Before)

```
factory-testing/
├── app/
│   └── rate_limiter.py          # Duplicate - exists in projects/rate-limiter-python
├── docs/                        # Documentation (keep)
├── projects/                    # Partially organized
│   ├── bracket-validator/       # Already organized
│   ├── rate-limiter-csharp/     # Already organized
│   ├── rate-limiter-python/     # Already organized
│   └── url-shortener/           # Already organized
├── src/                         # scattered files - TO BE REMOVED
│   ├── __init__.py
│   ├── bracket_validator.py     # Duplicate of projects/bracket-validator
│   ├── lru_cache.py             # Standalone - needs project
│   ├── url_shortener.py         # Duplicate of projects/url-shortener
│   └── __pycache__/
├── tests/                       # Root level tests - TO BE REORGANIZED
│   ├── test_bracket_validator.py   # Move to projects/bracket-validator/tests/
│   ├── test_lru_cache.py           # Move to new projects/lru-cache/tests/
│   ├── test_url_shortener.py       # Move to projects/url-shortener/tests/
│   ├── unit/
│   │   └── test_rate_limiter.py    # Move to projects/rate-limiter-python/tests/
│   └── __pycache__/
├── scripts/                     # Utility scripts
│   └── run_workflow.py          # Keep at root
├── subfolder/                   # Duplicate C# project - consolidate or remove
│   ├── RateLimiter/             # Duplicate of projects/rate-limiter-csharp
│   ├── RateLimiter.Tests/       # Tests with build artifacts
├── venv/                        # Python venv - remove from repo
├── .venv/                       # Python venv - remove from repo
├── .pytest_cache/               # Test cache - remove from repo
├── tasks.db                     # Taskboard database
├── .git/
├── .gitignore
├── README.md
└── requirements.txt
```

### Files to Move

| Current Location | Destination | Notes |
|-----------------|-------------|-------|
| `app/rate_limiter.py` | `projects/rate-limiter-python/src/rate_limiter.py` | Verify files are identical |
| `src/bracket_validator.py` | REMOVE | Duplicate of projects/bracket-validator |
| `src/lru_cache.py` | `projects/lru-cache/src/lru_cache.py` | Create new project |
| `src/url_shortener.py` | REMOVE | Duplicate of projects/url-shortener |
| `tests/test_bracket_validator.py` | `projects/bracket-validator/tests/` | Verify vs existing |
| `tests/test_lru_cache.py` | `projects/lru-cache/tests/` | Create new project |
| `tests/test_url_shortener.py` | `projects/url-shortener/tests/` | Verify vs existing |
| `tests/unit/test_rate_limiter.py` | `projects/rate-limiter-python/tests/` | Verify vs existing |
| `subfolder/RateLimiter/` | `projects/rate-limiter-csharp/src/` | Consolidate |
| `subfolder/RateLimiter.Tests/` | `projects/rate-limiter-csharp/tests/` | Consolidate |

### Directories to Remove After Migration

- `app/` (empty)
- `src/` (empty)
- `tests/` (empty)
- `subfolder/` (consolidated)
- `venv/` (already in .gitignore)
- `.venv/` (already in .gitignore)
- `.pytest_cache/` (already in .gitignore)
- `tasks.db` (needs to be added to .gitignore)

---

## 2. New Directory Structure (After)

```
factory-testing/
├── projects/
│   ├── bracket-validator/
│   │   ├── src/bracket_validator.py
│   │   ├── tests/test_bracket_validator.py
│   │   └── requirements.txt
│   ├── rate-limiter-csharp/
│   │   ├── src/RateLimiter/ (consolidated)
│   │   └── tests/RateLimiter.Tests/
│   ├── rate-limiter-python/
│   │   ├── src/rate_limiter.py
│   │   └── tests/test_rate_limiter.py
│   ├── lru-cache/                    # NEW
│   │   ├── src/lru_cache.py
│   │   └── tests/test_lru_cache.py
│   └── url-shortener/
│       ├── src/url_shortener.py
│       └── tests/test_url_shortener.py
├── scripts/
│   └── run_workflow.py
├── docs/
├── .git/
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 3. Migration Steps

### Step 1: Update .gitignore
Add `tasks.db` to .gitignore if not present.

### Step 2: Create lru-cache Project Structure
```bash
mkdir -p projects/lru-cache/src
mkdir -p projects/lru-cache/tests
```

### Step 3: Move lru_cache.py and Tests
```bash
mv src/lru_cache.py projects/lru-cache/src/
mv tests/test_lru_cache.py projects/lru-cache/tests/
```

### Step 4: Create __init__.py and conftest.py
- Create `projects/lru-cache/src/__init__.py`
- Create `projects/lru-cache/tests/conftest.py`

### Step 5: Create requirements.txt for lru-cache
Create minimal `projects/lru-cache/requirements.txt`

### Step 6: Handle Duplicates
- Compare and merge `tests/test_bracket_validator.py` with existing
- Compare and merge `tests/test_url_shortener.py` with existing  
- Compare and merge `tests/unit/test_rate_limiter.py` with existing

### Step 7: Handle app/rate_limiter.py
- Compare with `projects/rate-limiter-python/src/rate_limiter.py`
- Keep the more complete version
- Remove the other

### Step 8: Handle subfolder/ Consolidation
- Move `subfolder/RateLimiter/` contents to `projects/rate-limiter-csharp/src/RateLimiter/`
- Move `subfolder/RateLimiter.Tests/` to `projects/rate-limiter-csharp/tests/`
- Remove build artifacts (bin/, obj/) - these should be in .gitignore

### Step 9: Remove Empty Directories
```bash
rmdir app src tests subfolder
```

### Step 10: Update Root requirements.txt
Aggregate all project requirements or keep project-specific ones.

---

## 4. Import Updates Required

### Root-level test imports (BEFORE):
```python
# tests/test_bracket_validator.py
from src.bracket_validator import validate_brackets

# tests/test_lru_cache.py
from src.lru_cache import LRUCache

# tests/test_url_shortener.py
from src.url_shortener import ...

# tests/unit/test_rate_limiter.py
# (check imports)
```

### Project-level test imports (AFTER):
```python
# projects/bracket-validator/tests/test_bracket_validator.py
from src.bracket_validator import validate_brackets
# No change needed if structure is src/ at project root

# projects/lru-cache/tests/test_lru_cache.py
from src.lru_cache import LRUCache
# No change needed

# projects/url-shortener/tests/test_url_shortener.py
from src.url_shortener import ...
# No change needed

# projects/rate-limiter-python/tests/test_rate_limiter.py
# (check imports)
```

### Key Change:
- Tests in `projects/*/tests/` import from `src/` relative to project root
- PYTHONPATH should include the project root, or use pytest's `--rootdir`

---

## 5. Test Updates Required

1. **Verify test imports work** after moving to per-project structure
2. **Update conftest.py** if needed for shared fixtures
3. **Run tests** in each project:
   ```bash
   cd projects/bracket-va}

### Step 3: Run tests per project
```bash
cd projects/bracket-validator && pytest
cd projects/rate-limiter-python && pytest
cd projects/url-shortener && pytest
cd projects/lru-cache && pytest
```

### Step 4: Verify all tests pass after migration
- No import errors
- No missing dependencies

---

## 6. Implementation Checklist (for Senior Engineer)

- [ ] 1. Update .gitignore to add `tasks.db`
- [ ] 2. Create projects/lru-cache/src/ and projects/lru-cache/tests/ directories
- [ ] 3. Move src/lru_cache.py to projects/lru-cache/src/
- [ ] 4. Move tests/test_lru_cache.py to projects/lru-cache/tests/
- [ ] 5. Create projects/lru-cache/src/__init__.py
- [ ] 6. Create projects/lru-cache/tests/conftest.py (copy from other project)
- [ ] 7. Create projects/lru-cache/requirements.txt
- [ ] 8. Compare and merge tests/test_bracket_validator.py (remove duplicate)
- [ ] 9. Compare and merge tests/test_url_shortener.py (remove duplicate)
- [ ] 10. Compare and merge tests/unit/test_rate_limiter.py (remove duplicate)
- [ ] 11. Compare app/rate_limiter.py with projects/rate-limiter-python version
- [ ] 12. Consolidate subfolder/ into projects/rate-limiter-csharp/
- [ ] 13. Remove empty directories: app/, src/, tests/, subfolder/
- [ ] 14. Verify all tests pass in each project
- [ ] 15. Update root-level README.md if needed

---

## 7. Risks & Considerations

1. **Import Path Changes**: Tests rely on `from src.xxx import ...`. After migration, this should still work if PYTHONPATH is set correctly or pytest is run from project root.

2. **Duplicate Files**: Several files exist both in root and in projects/. Need to verify which version is canonical.

3. **C# Project**: subfolder/ has a duplicate C# project. Need to decide if this is intentional (work in progress) or should be consolidated.

4. **Build Artifacts**: subfolder/ contains bin/ and obj/ folders from .NET builds - these should be ignored.

5. **tasks.db**: Should be added to .gitignore to prevent accidental commits.

---

## 8. Acceptance Criteria

- [ ] Root contains only: projects/, .git/, .gitignore, README.md, requirements.txt, scripts/, docs/
- [ ] Each project has its own folder under projects/
- [ ] All Python source files are under projects/*/src/
- [ ] All tests are under projects/*/tests/
- [ ] No duplicate files between root src/ and projects/
- [ ] No stray venv/, .venv/, .pytest_cache/ in git
- [ ] All tests pass after migration
