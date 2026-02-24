# 🏭 Factory Testing Repository

> Testing ground for agent workflows, automation patterns, and AI benchmarking.

This repository centralizes a handful of helper projects (rate limiters, validators, shorteners, caches) that are used to demonstrate choreography between agents, CI checks, and documentation efforts.

## 📁 Directory layout

```
factory-testing/
├── projects/         # Self-contained workloads with src/, tests/, docs/
├── scripts/          # Utility scripts ( e.g., workflow runner )
├── docs/             # Repository-level documentation
├── README.md         # This file
├── requirements.txt  # Shared Python dependencies
└── .gitignore        # Files to ignore
```

## 🔧 Projects

Each folder under `projects/` follows the same convention (client code under `src/`, unit tests under `tests/`, and any project-specific docs under `docs/`).

- `projects/bracket-validator` — Balanced-bracket validator used across utility tests and demos.
- `projects/rate-limiter-python` — Fixed-window Python rate limiter with thread-safe buckets.
- `projects/rate-limiter-csharp` — .NET rate limiter library with configuration, events, DI helpers, and a placeholder `tests/` directory.
- `projects/url-shortener` — Hash-based URL shortener and in-memory store used in several agent workflows.
- `projects/lru-cache` — Newly consolidated LRU cache implementation with its own test suite.

## 🚀 Quick start

### Prerequisites

- Python 3.8+ (the repo targets modern CPython releases)
- `pip` available on your $PATH

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the workflow runner (demo script)

The `scripts/run_workflow.py` helper mimics agent-driven benchmarks and research runs.

```bash
python scripts/run_workflow.py --workflow benchmark --model gpt-5.2 --iterations 5
```

## 🧪 Running tests

Each project lives under `projects/<name>` with its own `tests/` directory. Run all Python tests with:

```bash
python -m pytest \
  projects/bracket-validator \
  projects/rate-limiter-python \
  projects/url-shortener \
  projects/lru-cache
```

Add `-v` for verbose output. C# tests (when present) are described in `projects/rate-limiter-csharp/tests/README.md`.

## 📚 Documentation

Add project-specific documentation under `projects/<name>/docs/` and cross-project docs under the top-level `docs/` directory. This repo also stores migration plans (see `docs/T11-plan.md`).

## 🤝 Contributing

1. Add your feature under `projects/<feature>/src/` with matching `tests/` and `docs/` folders.
2. Update `README.md` if you introduce new workflow scripts or commands.
3. Run the relevant pytest targets (see above) before opening a PR.
4. Keep the root directory tidy: only `projects/`, `scripts/`, `docs/`, and the core files should live at the top level.
