"""Tests for publish workflow."""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.publish import PublishWorkflow


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def sample_markdown(temp_dir):
    """Create a sample markdown file."""
    md_file = temp_dir / "test.md"
    md_file.write_text("# Hello World\n\nThis is a **test**.")
    return md_file


@pytest.fixture
def sample_markdown_dir(temp_dir):
    """Create a directory with multiple markdown files."""
    (temp_dir / "file1.md").write_text("# File 1\n\nContent 1")
    (temp_dir / "file2.md").write_text("# File 2\n\nContent 2")
    (temp_dir / "readme.md").write_text("# Readme\n\nREADME content")
    return temp_dir


class TestPublishWorkflow:
    """Test cases for PublishWorkflow class."""
    
    def test_publish_single_file(self, sample_markdown, temp_dir):
        """Test publishing a single markdown file."""
        workflow = PublishWorkflow()
        output_file = temp_dir / "output.html"
        
        result = workflow.publish_file(sample_markdown, output_file)
        
        assert result['success'] is True
        assert output_file.exists()
        assert result['input'] == str(sample_markdown)
        assert result['output'] == str(output_file)
        assert 'elapsed_seconds' in result
        assert 'stats' in result
    
    def test_publish_file_with_stats(self, sample_markdown, temp_dir):
        """Test that stats are included in result."""
        workflow = PublishWorkflow()
        output_file = temp_dir / "output.html"
        
        result = workflow.publish_file(sample_markdown, output_file, include_toc=False)
        
        assert result['success'] is True
        assert 'stats' in result
        assert 'word_count' in result['stats']
        assert result['stats']['word_count'] > 0
    
    def test_publish_directory(self, sample_markdown_dir, temp_dir):
        """Test publishing all files in a directory."""
        workflow = PublishWorkflow()
        output_dir = temp_dir / "output"
        
        results = workflow.publish_directory(sample_markdown_dir, output_dir)
        
        assert len(results) == 3
        assert (output_dir / "file1.html").exists()
        assert (output_dir / "file2.html").exists()
        assert (output_dir / "readme.html").exists()
        assert all(r['success'] for r in results)
    
    def test_publish_directory_with_pattern(self, sample_markdown_dir, temp_dir):
        """Test publishing with custom glob pattern."""
        workflow = PublishWorkflow()
        output_dir = temp_dir / "output"
        
        results = workflow.publish_directory(
            sample_markdown_dir, output_dir, pattern="file*.md"
        )
        
        assert len(results) == 2
    
    def test_save_results(self, temp_dir):
        """Test saving workflow results to JSON."""
        workflow = PublishWorkflow()
        from datetime import datetime
        workflow.start_time = datetime.now()
        
        workflow.results = [
            {'input': 'a.md', 'output': 'a.html', 'success': True, 'elapsed_seconds': 0.1},
            {'input': 'b.md', 'output': 'b.html', 'success': True, 'elapsed_seconds': 0.2},
        ]
        
        log_file = temp_dir / "results.json"
        result = workflow.save_results(log_file)
        
        assert log_file.exists()
        data = json.loads(log_file.read_text())
        assert data['workflow'] == 'publish'
        assert data['total_files'] == 2
    
    def test_publish_with_failure(self, temp_dir):
        """Test handling of publish failures."""
        workflow = PublishWorkflow()
        
        missing_file = temp_dir / "missing.md"
        output_file = temp_dir / "output.html"
        
        result = workflow.publish_file(missing_file, output_file)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_publish_with_toc(self, sample_markdown, temp_dir):
        """Test publishing with table of contents."""
        workflow = PublishWorkflow()
        output_file = temp_dir / "output.html"
        
        result = workflow.publish_file(sample_markdown, output_file, include_toc=True)
        
        assert result['success'] is True
        assert 'stats' in result
    
    def test_publish_with_css(self, sample_markdown, temp_dir):
        """Test publishing with CSS file."""
        workflow = PublishWorkflow()
        
        css_file = temp_dir / "style.css"
        css_file.write_text("body { font-family: sans-serif; }")
        
        output_file = temp_dir / "output.html"
        result = workflow.publish_file(sample_markdown, output_file, css_path=css_file)
        
        assert result['success'] is True
        assert output_file.exists()


class TestPublishWorkflowCLI:
    """Test cases for the CLI interface."""
    
    def test_cli_help(self):
        """Test CLI help output."""
        import subprocess
        result = subprocess.run(
            ["python3", "scripts/publish.py", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/vishwa/.openclaw/workspace/factory-testing"
        )
        assert result.returncode == 0
        assert "Publish Markdown" in result.stdout
    
    def test_cli_single_file(self, sample_markdown, temp_dir):
        """Test CLI with single file."""
        import subprocess
        output_file = temp_dir / "output.html"
        
        result = subprocess.run(
            ["python3", "scripts/publish.py", 
             "--input", str(sample_markdown),
             "--output", str(output_file)],
            capture_output=True,
            text=True,
            cwd="/home/vishwa/.openclaw/workspace/factory-testing"
        )
        
        assert result.returncode == 0
        assert output_file.exists()
    
    def test_cli_missing_input(self, temp_dir):
        """Test CLI with missing input file."""
        import subprocess
        missing = temp_dir / "missing.md"
        output = temp_dir / "output.html"
        
        result = subprocess.run(
            ["python3", "scripts/publish.py",
             "--input", str(missing),
             "--output", str(output)],
            capture_output=True,
            text=True,
            cwd="/home/vishwa/.openclaw/workspace/factory-testing"
        )
        
        assert result.returncode != 0
        assert "Error" in result.stderr or "does not exist" in result.stderr
