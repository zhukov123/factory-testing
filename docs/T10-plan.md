# T10 Plan: Repository Clean-up

## Current State Analysis

The repository `/home/vishwa/.openclaw/workspace/factory-testing` contains multiple projects混在一起 (mixed together):

| Location | Project | Language | Issue |
|----------|---------|----------|-------|
| `src/url_shortener.py` | URL Shortener | Python | Mixed with other projects in `src/` |
| `src/bracket_validator.py` | Bracket Validator | Python | Mixed with other projects in `src/` |
| `app/rate_limiter.py` | Rate Limiter | Python | In `app/` folder (unclear purpose) |
| `subfolder/RateLimiter/` | RateLimiter (library) | C# (.NET) | Deeply nested, confusingly similar name to Python rate_limiter |
| `tests/` | All tests | Python | Flat structure, not organized by project |

### Problems Identified:
1. **Mixed project locations** - Multiple projects in `src/` and `app/`
2. **Duplicate/similar projects** - Both Python (`app/rate_limiter.py`) and C# (`subfolder/RateLimiter/`) rate limiters with confusing names
3. **Tests not organized** - All tests in flat `tests/` folder
4. **Unclear root structure** - `app/`, `src/`, `subfolder/` unclear separation

## Proposed Folder Structure

```
factory-testing/
├── projects/
│   ├── url-shortener/           # URL Shortener (Python)
│   │   ├── src/
│   │   │   └── url_shortener.py
│   │   ├── tests/
│   │   │   └── test_url_shortener.py
│   │   └── requirements.txt
│   │
│   ├── bracket-validator/       # Bracket Validator (Python)
│   │   ├── src/
│   │   │   └── bracket_validator.py
│   │   ├── tests/
│   │   │   └── test_bracket_validator.py
│   │   └── requirements.txt
│   │
│   ├── rate-limiter-python/     # Rate Limiter (Python)
│   │   ├── src/
│   │   │   └── rate_limiter.py
│   │   ├── tests/
│   │   │   └── test_rate_limiter.py
│   │   └── requirements.txt
│   │
│   └── rate-limiter-csharp/     # Rate Limiter (C# .NET)
│       ├── src/
│       │   └── RateLimiter/     # All C# source from subfolder/RateLimiter
│       ├── RateLimiter.csproj
│       └── README.md
│
├── docs/                        # Keep existing docs
├── scripts/                     # Keep existing scripts
└── README.md                    # Keep root readme
```

## Migration Plan

### Phase 1: Create Project Directories
1. Create `projects/` directory
2. Create each project subdirectory with standard structure (`src/`, `tests/`)
3. Copy source files into appropriate project folders

### Phase 2: Relocate and Organize
1. Move `src/url_shortener.py` → `projects/url-shortener/src/`
2. Move `src/bracket_validator.py` → `projects/bracket-validator/src/`
3. Move `app/rate_limiter.py` → `projects/rate-limiter-python/src/`
4. Move `subfolder/RateLimiter/` → `projects/rate-limiter-csharp/src/RateLimiter/`
5. Move corresponding test files into each project's `tests/` folder

### Phase 3: Update References
1. Update imports in test files to match new paths
2. Update any internal references between projects
3. Clean up empty `src/`, `app/`, `subfolder/` directories

### Phase 4: Cleanup
1. Remove empty directories
2. Verify all tests pass
3. Update README if needed

## Testing Approach

1. **Verify file locations**: Each project in correct folder
2. **Run existing tests**: Ensure nothing broke
   ```bash
   cd projects/url-shortener && pytest
   cd projects/bracket-validator && pytest  
   cd projects/rate-limiter-python && pytest
   ```
3. **C# project**: Verify builds
   ```bash
   cd projects/rate-limiter-csharp && dotnet build
   ```

## Next Steps (After Plan Approval)
1. Execute the migration (Phases 1-4)
2. Verify all tests pass
3. Update root README with new structure