#!/usr/bin/env python3
"""
Workflow Runner for Factory Testing

Example usage:
    python scripts/run_workflow.py --workflow benchmark --model gpt-5.2 --iterations 10
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

class WorkflowRunner:
    def __init__(self, config_path="configs/workflows.json"):
        self.config = self.load_config(config_path)
        self.results = []
        
    def load_config(self, path):
        """Load workflow configurations"""
        config_file = Path(path)
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return {}
    
    def add_task(self, task_name, model="auto", timeout=1800):
        """Add a task to the workflow"""
        task = {
            "name": task_name,
            "model": model,
            "timeout": timeout,
            "created_at": datetime.now().isoformat()
        }
        self.results.append(task)
        return task
    
    def run_benchmark(self, model, iterations=5):
        """Run benchmark workflow"""
        print(f"Running benchmark workflow with {model} ({iterations} iterations)")
        
        times = []
        tokens = []
        
        for i in range(iterations):
            start_time = time.time()
            
            # Simulate a task
            task = self.add_task(f"benchmark_iteration_{i}", model=model)
            
            # Simulate work
            time.sleep(0.5)
            
            elapsed = time.time() - start_time
            times.append(elapsed)
            tokens.append(len(str(task)) * 10)  # Mock token count
            
            print(f"  Iteration {i+1}: {elapsed:.2f}s, {tokens[-1]} tokens")
        
        # Calculate stats
        stats = {
            "model": model,
            "iterations": iterations,
            "avg_time": sum(times) / len(times),
            "total_tokens": sum(tokens),
            "avg_tokens_per_run": sum(tokens) / len(tokens),
            "min_time": min(times),
            "max_time": max(times)
        }
        
        print(f"\nBenchmark complete!")
        print(f"Average time: {stats['avg_time']:.2f}s")
        print(f"Total tokens: {stats['total_tokens']:,}")
        
        return stats
    
    def run_research_workflow(self, topic, models=["gpt-5.2", "claude-opus-4.6", "kimi-k2.5"]):
        """Run multi-model research workflow"""
        print(f"Research workflow: {topic}")
        results = {}
        
        for model in models:
            print(f"\nRunning with {model}...")
            task = self.add_task(f"research_{topic}", model=model)
            
            start = time.time()
            # Simulate research
            time.sleep(1.0)
            elapsed = time.time() - start
            
            results[model] = {
                "time": elapsed,
                "task": task
            }
            
            print(f"  Completed in {elapsed:.2f}s")
        
        return results
    
    def save_results(self, output_path="results/latest_run.json"):
        """Save workflow results"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results,
                "summary": {
                    "total_tasks": len(self.results),
                    "models_used": list(set(r["model"] for r in self.results))
                }
            }, f, indent=2)
        
        print(f"\nResults saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Run agent workflow tests')
    parser.add_argument('--workflow', choices=['benchmark', 'research'], default='benchmark',
                       help='Type of workflow to run')
    parser.add_argument('--model', default='auto', 
                       help='Model to use (gpt-5.2, claude-opus-4.6, kimi-k2.5, etc.)')
    parser.add_argument('--iterations', type=int, default=5,
                       help='Number of iterations for benchmark')
    parser.add_argument('--topic', default='ai_benchmarks',
                       help='Research topic')
    
    args = parser.parse_args()
    
    runner = WorkflowRunner()
    
    if args.workflow == 'benchmark':
        stats = runner.run_benchmark(args.model, args.iterations)
        runner.save_results(f"results/benchmark_{args.model}_{int(time.time())}.json")
        
    elif args.workflow == 'research':
        results = runner.run_research_workflow(args.topic, [args.model])
        runner.save_results(f"results/research_{args.topic}.json")
    
    print("\n✅ Workflow execution complete!")


if __name__ == "__main__":
    main()
