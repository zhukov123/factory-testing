"""Tests for CLI argument handling in markdown_to_html CLI."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from markdown_to_html import convert_markdown, main


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


class TestArgparseIntegration:
    """Tests for argparse integration in the CLI."""

    def test_basic_conversion(self, sample_markdown, temp_dir):
        """Test basic markdown to HTML conversion."""
        output_file = temp_dir / "output.html"
        # Use show_stats=True to get dict return with new API
        result = convert_markdown(sample_markdown, output_file, show_stats=True)
        
        assert output_file.exists()
        assert "<h1>Hello World</h1>" in result['html']
        assert "<strong>test</strong>" in result['html']
        assert "<!DOCTYPE html>" in result['html']

    def test_with_css(self, sample_markdown, temp_dir):
        """Test conversion with custom CSS."""
        css_file = temp_dir / "style.css"
        css_file.write_text("body { font-family: sans-serif; }")
        
        output_file = temp_dir / "output.html"
        result = convert_markdown(sample_markdown, output_file, css_file, show_stats=True)
        
        assert 'link rel="stylesheet" href="' in result['html']
        assert "style.css" in result['html']

    def test_without_output_file(self, sample_markdown):
        """Test conversion without specifying output (returns dict when using new features)."""
        # Use show_stats=True to get dict return with new API
        result = convert_markdown(sample_markdown, show_stats=True)
        
        assert isinstance(result, dict)
        assert "html" in result
        assert "stats" in result
        assert "<h1>Hello World</h1>" in result['html']

    def test_input_file_not_found(self, temp_dir):
        """Test error handling for missing input file."""
        missing_file = temp_dir / "missing.md"
        
        with pytest.raises(FileNotFoundError):
            convert_markdown(missing_file)


class TestHelpTextUpdated:
    """Tests for updated help text in the CLI."""

    def test_cli_help(self):
        """Test CLI help output contains expected content."""
        result = subprocess.run(
            ["python3", "markdown_to_html.py", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/vishwa/.openclaw/workspace/factory-testing"
        )
        assert result.returncode == 0
        # Check for updated help text
        assert "Convert Markdown to HTML" in result.stdout
        # Check for new arguments in help
        assert "--include-toc" in result.stdout
        assert "--show-stats" in result.stdout
        assert "--version" in result.stdout

    def test_help_shows_examples(self):
        """Test that help includes examples."""
        result = subprocess.run(
            ["python3", "markdown_to_html.py", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/vishwa/.openclaw/workspace/factory-testing"
        )
        assert "Examples:" in result.stdout
        assert "input.md" in result.stdout

    def test_version_argument(self):
        """Test --version argument works."""
        result = subprocess.run(
            ["python3", "markdown_to_html.py", "--version"],
            capture_output=True,
            text=True,
            cwd="/home/vishwa/.openclaw/workspace/factory-testing"
        )
        assert result.returncode == 0
        assert "1.1.0" in result.stdout


class TestMarkdownFeatures:
    """Test various markdown features with CLI args."""

    def test_markdown_features(self, temp_dir):
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
        # Use show_stats=True to get dict return with new API
        result = convert_markdown(md_file, output_file, show_stats=True)
        
        assert "<h1>Title</h1>" in result['html']
        assert "<h2>Subtitle</h2>" in result['html']
        assert "<em>italic</em>" in result['html']
        assert "<code>code</code>" in result['html']
        assert "<ul>" in result['html']
        assert "<li>Item 1</li>" in result['html']
        assert '<a href="http://example.com">Link</a>' in result['html']


class TestStatisticsFeature:
    """Tests for the --show-stats feature using markdown utilities."""

    def test_stats_are_included(self, sample_markdown):
        """Test that statistics are included when requested."""
        result = convert_markdown(sample_markdown, show_stats=True)
        
        assert "stats" in result
        assert "word_count" in result['stats']
        assert "heading_count" in result['stats']
        assert "link_count" in result['stats']
        assert "code_block_count" in result['stats']

    def test_stats_values(self, temp_dir):
        """Test that stats have correct values."""
        md_file = temp_dir / "stats_test.md"
        md_file.write_text("""# Title

This is a paragraph with some [links](http://example.com).

```python
code = "test"
```
""")
        
        # Use show_stats=True to get dict return
        result = convert_markdown(md_file, show_stats=True)
        
        # Check stats values
        assert result['stats']['heading_count'] == 1
        assert result['stats']['link_count'] == 1
        assert result['stats']['code_block_count'] == 1
        # Words: Title, This, is, a, paragraph, with, some, links = 8
        assert result['stats']['word_count'] == 8


class TestTableOfContents:
    """Tests for the --include-toc feature using markdown utilities."""

    def test_toc_included_when_requested(self, temp_dir):
        """Test that TOC is included when --include-toc is used."""
        md_file = temp_dir / "toc_test.md"
        md_file.write_text("""# First Section

Some content here.

## Second Section

More content.
""")
        
        output_file = temp_dir / "output.html"
        result = convert_markdown(md_file, output_file, include_toc=True)
        
        assert "toc" in result
        assert result['toc'] is not None
        assert "Table of Contents" in result['toc']
        assert "First Section" in result['toc']
        assert "Second Section" in result['toc']

    def test_toc_not_included_by_default(self, temp_dir):
        """Test that TOC is not included by default when using stats."""
        md_file = temp_dir / "no_toc.md"
        md_file.write_text("# Heading\n\nContent.")
        
        # Use show_stats=True to get dict return, but don't include_toc
        result = convert_markdown(md_file, show_stats=True)
        
        # TOC should be None when not requested
        assert result['toc'] is None


class TestCliIntegration:
    """Integration tests for CLI with new arguments."""

    def test_cli_with_include_toc(self, temp_dir):
        """Test CLI with --include-toc flag."""
        md_file = temp_dir / "input.md"
        md_file.write_text("# Title\n\nContent.")
        
        result = subprocess.run(
            ["python3", "markdown_to_html.py", str(md_file), "--include-toc"],
            capture_output=True,
            text=True,
            cwd="/home/vishwa/.openclaw/workspace/factory-testing"
        )
        
        assert result.returncode == 0
        assert "Table of Contents" in result.stdout
        assert "#title" in result.stdout

    def test_cli_with_show_stats(self, temp_dir):
        """Test CLI with --show-stats flag."""
        md_file = temp_dir / "input.md"
        md_file.write_text("# Title\n\nSome content here.")
        
        output_file = temp_dir / "output.html"
        
        result = subprocess.run(
            ["python3", "markdown_to_html.py", str(md_file), "-o", str(output_file), "--show-stats"],
            capture_output=True,
            text=True,
            cwd="/home/vishwa/.openclaw/workspace/factory-testing"
        )
        
        assert result.returncode == 0
        assert "Document Statistics:" in result.stdout
        assert "Words:" in result.stdout
        assert "Headings:" in result.stdout


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
