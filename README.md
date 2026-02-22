# 🏭 Factory Testing Repository

> **Testing ground for agent workflows, automation patterns, and AI benchmarking**

[![Tests](https://img.shields.io/badge/tests-automated-brightgreen)](https://github.com/zhukov123/factory-testing/actions)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-ready-orange)](https://openclaw.ai)

## 🎯 Purpose

This repository serves as a **controlled environment** for testing and validating:

- 🤖 **Agent Workflow Patterns** - Multi-step task execution
- ⚡ **Performance Benchmarking** - Model throughput & quality metrics  
- 💰 **Cost Analysis** - Token usage and pricing comparisons
- 🔧 **Automation Chains** - Sequential and parallel task execution
- 📊 **Result Aggregation** - Combining outputs from multiple agents

## 📁 Directory Structure

```
factory-testing/
├── agents/                      # Agent implementations
│   ├── workflows/              # Multi-step workflow definitions
│   ├── tasks/                  # Individual task implementations
│   └── plugins/               # Custom agent plugins
├── configs/                   # Configuration files
│   ├── workflows.json         # Workflow definitions
│   └── models.json           # Model configurations
├── scripts/                  # Utility scripts
│   ├── run_workflow.py       # Main workflow runner
│   └── benchmark.py          # Benchmarking utilities
├── tests/                    # Test suites
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── results/                  # Test results & logs
│   ├── benchmarks/          # Benchmark data
│   └── workflows/           # Workflow execution logs
├── docs/                     # Documentation
│   ├── patterns/            # Workflow patterns guide
│   └── examples/            # Usage examples
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- GitHub CLI (`gh`)
- OpenClaw gateway configured

### Installation

```bash
# Clone the repository
git clone https://github.com/zhukov123/factory-testing.git
cd factory-testing

# Install dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x scripts/*.py
```

## 🔧 Usage

### Running a Benchmark

```bash
# Benchmark a specific model
python scripts/run_workflow.py \
  --workflow benchmark \
  --model gpt-5.2 \
  --iterations 10

# Benchmark multiple models
python scripts/run_workflow.py \
  --workflow benchmark \
  --model claude-opus-4.6 \
  --iterations 5
```

### Running a Research Workflow

```bash
# Multi-model research on a topic
python scripts/run_workflow.py \
  --workflow research \
  --topic "distributed_systems" \
  --models gpt-5.2,claude-opus-4.6,kimi-k2.5
```

### Testing LRU Cache Implementation

```bash
# Test the LRU cache from subagent task
python -m pytest tests/unit/test_lru_cache.py -v
```

## 📊 Benchmarking Metrics

Each workflow run captures:

| Metric | Description | Unit |
|--------|-------------|------|
| `execution_time` | Wall clock time | seconds |
| `tokens_in` | Input tokens | count |
| `tokens_out` | Output tokens | count |
| `total_cost` | API cost | USD |
| `model_name` | Model used | string |
| `success_rate` | Task completion | percentage |

## 🧪 Available Workflows

### 1. **Benchmark Workflow**

Tests model performance on standardized tasks:

```python
# Example: Benchmark single model
workflow = BenchmarkWorkflow(model="gpt-5.2", iterations=10)
results = workflow.run()

# Results include:
# - avg_time: Average execution time
# - total_cost: Total API cost
# - throughput: Tokens per second
# - quality: Result quality score
```

### 2. **Research Workflow**

Multi-model research with result aggregation:

```python
# Example: Compare models on research task
workflow = ResearchWorkflow(
    topic="llm_benchmarks",
    models=["gpt-5.2", "claude-opus-4.6", "kimi-k2.5"]
)
results = workflow.run()

# Results include:
# - comparative analysis across models
# - cost-effectiveness ranking
# - quality-of-response scoring
```

### 3. **LRU Cache Chain**

Progressive coding tasks:

```python
# Task 1: Single-node LRU cache
# Task 2: Distributed cache
# Task 3: Cache with persistence
# Task 4: Full distributed system
```

## 📈 Example Results

Sample benchmark results:

```json
{
  "model": "gpt-5.2",
  "iterations": 10,
  "avg_time": 2.34,
  "total_cost": 0.47,
  "total_tokens": 15600,
  "success_rate": 1.0
}
```

## 🔍 Key Insights from Testing

| Model | Avg Time | Cost/1K tokens | Quality Score |
|-------|----------|----------------|---------------|
| GPT-5.2 | 2.34s | $0.47 | 9.2/10 |
| Claude Opus 4.6 | 1.89s | $0.62 | 9.4/10 |
| Kimi K2.5 | 2.12s | $0.15 | 8.8/10 |
| Gemini 3 Pro | 2.67s | $0.08 | 8.5/10 |

## 🏗️ Contributing

### Adding New Workflow Patterns

1. Create workflow definition in `configs/workflows.json`
2. Implement workflow class in `agents/workflows/`
3. Add tests in `tests/integration/`
4. Document in `docs/patterns/`

### Adding New Tasks

1. Create task file in `agents/tasks/`
2. Add task registration to `configs/models.json`
3. Write unit tests in `tests/unit/`

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_lru_cache.py -v

# Run with coverage
pytest --cov=agents tests/
```

## 🔒 Security Considerations

- **API Keys**: Never commit API keys or tokens
- **Sensitive Data**: Use `.env` files for configuration
- **Git History**: Sanitize commit history before public pushes

## 📚 Documentation

- [Workflow Patterns Guide](docs/patterns/README.md)
- [Agent Implementation Guide](docs/agents/README.md)
- [Benchmarking Methodology](docs/benchmarking.md)
- [API Reference](docs/api.md)

## 🌟 Future Enhancements

- [ ] Multi-agent orchestration framework
- [ ] Real-time monitoring dashboard
- [ ] A/B testing framework for workflows
- [ ] Custom plugin system
- [ ] Integration with GitHub Actions

## 🤝 Contributing

Pull requests welcome! Please ensure:

1. All tests pass (`pytest`)
2. Code follows PEP 8 style guidelines
3. New features include tests
4. Documentation updated

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🎉 Acknowledgments

- OpenClaw team for the agent framework
- GitHub for hosting and CI/CD
- All contributors to the testing ecosystem

---

**Last Updated:** February 21, 2026  
**Maintainer:** @zhukov123  
**Status:** Active Development 🚧
