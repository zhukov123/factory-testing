"""Tests for markdown_to_html CLI."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from markdown_to_html import convert_markdown


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


def test_basic_conversion(sample_markdown, temp_dir):
    """Test basic markdown to HTML conversion."""
    output_file = temp_dir / "output.html"
    result = convert_markdown(sample_markdown, output_file)
    
    assert output_file.exists()
    assert "<h1>Hello World</h1>" in result
    assert "<strong>test</strong>" in result
    assert "<!DOCTYPE html>" in result


def test_with_css(sample_markdown, temp_dir):
    """Test conversion with custom CSS."""
    css_file = temp_dir / "style.css"
    css_file.write_text("body { font-family: sans-serif; }")
    
    output_file = temp_dir / "output.html"
    result = convert_markdown(sample_markdown, output_file, css_file)
    
    assert 'link rel="stylesheet" href="' in result
    assert "style.css" in result


def test_without_output_file(sample_markdown):
    """Test conversion without specifying output (returns string)."""
    result = convert_markdown(sample_markdown)
    
    assert isinstance(result, str)
    assert "<h1>Hello World</h1>" in result


def test_input_file_not_found(temp_dir):
    """Test error handling for missing input file."""
    missing_file = temp_dir / "missing.md"
    
    with pytest.raises(FileNotFoundError):
        convert_markdown(missing_file)


def test_cli_help():
    """Test CLI help output."""
    result = subprocess.run(
        ["python3", "markdown_to_html.py", "--help"],
        capture_output=True,
        text=True,
        cwd="/home/vishwa/.openclaw/workspace/factory-testing"
    )
    assert result.returncode == 0
    assert "Convert Markdown to HTML" in result.stdout


def test_markdown_features(temp_dir):
    """Test various markdown features."""
    md_file = temp_dir / "features.md"
    md_file.write_text("""# Title

## Subtitle

Paragraph with *italic* and `code`.

- Item 1
- Item 2

[Link](http://example.com)
""")
    
    output_file = temp_dir / "output.html"
    result = convert_markdown(md_file, output_file)
    
    assert "<h1>Title</h1>" in result
    assert "<h2>Subtitle</h2>" in result
    assert "<em>italic</em>" in result
    assert "<code>code</code>" in result
    assert "<ul>" in result
    assert "<li>Item 1</li>" in result
    assert '<a href="http://example.com">Link</a>' in result