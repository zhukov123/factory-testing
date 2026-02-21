# Factory Testing Repository

This repository is designed for testing agent workflows and automation patterns.

## Directory Structure

```
├── agents/
│   ├── workflows/
│   ├── tasks/
│   └── plugins/
├── configs/
├── scripts/
├── tests/
└── README.md
```

## Purpose

- Test agent task creation and execution
- Validate workflow automation patterns
- Benchmark agent performance across different models
- Experiment with agent orchestration

## Getting Started

1. Clone this repository
2. Set up your OpenClaw configuration
3. Run test workflows with `python scripts/run_workflow.py`

## Example Workflow

Basic agent workflow pattern demonstrating:
- Task decomposition
- Model selection
- Result aggregation
- Error handling

```python
from agents import WorkflowRunner

workflow = WorkflowRunner()
workflow.add_task("Research", model="gpt-5.2")
workflow.add_task("Analyze", model="claude-opus-4.6")
workflow.add_task("Summarize", model="kimi-k2.5")

result = workflow.execute()
```

## Benchmarking

Compare agent performance across models:
- Task completion time
- Token usage
- Result quality
- Cost per task

## Contributing

Add new workflow patterns and agent configurations to test different automation scenarios.
