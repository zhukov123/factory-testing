"""Tests for HTML output format standards."""

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


class TestHTMLStructure:
    """Tests for HTML structure requirements."""

    def test_html_contains_head(self, sample_markdown, temp_dir):
        """Test that generated HTML contains <head> tag."""
        output_file = temp_dir / "output.html"
        result = convert_markdown(sample_markdown, output_file, show_stats=True)
        
        html = result['html']
        assert "<head>" in html, "HTML should contain <head> tag"
        assert "</head>" in html, "HTML should contain closing </head> tag"

    def test_html_contains_body(self, sample_markdown, temp_dir):
        """Test that generated HTML contains <body> tag."""
        output_file = temp_dir / "output.html"
        result = convert_markdown(sample_markdown, output_file, show_stats=True)
        
        html = result['html']
        assert "<body>" in html, "HTML should contain <body> tag"
        assert "</body>" in html, "HTML should contain closing </body> tag"

    def test_html_has_doctype(self, sample_markdown, temp_dir):
        """Test that generated HTML has DOCTYPE declaration."""
        output_file = temp_dir / "output.html"
        result = convert_markdown(sample_markdown, output_file, show_stats=True)
        
        html = result['html']
        assert "<!DOCTYPE html>" in html, "HTML should have DOCTYPE declaration"


class TestCSSInjection:
    """Tests for CSS injection functionality."""

    def test_css_injection_with_file(self, sample_markdown, temp_dir):
        """Test that CSS file is properly injected into HTML."""
        css_file = temp_dir / "style.css"
        css_file.write_text("body { font-family: sans-serif; }")
        
        output_file = temp_dir / "output.html"
        result = convert_markdown(sample_markdown, output_file, css_path=css_file, show_stats=True)
        
        html = result['html']
        assert 'link rel="stylesheet"' in html, "CSS link tag should be present"
        assert "style.css" in html, "CSS file path should be in href attribute"

    def test_css_injection_with_full_path(self, sample_markdown, temp_dir):
        """Test CSS injection with absolute path."""
        css_file = temp_dir / "custom.css"
        css_file.write_text("h1 { color: blue; }")
        
        output_file = temp_dir / "output.html"
        result = convert_markdown(sample_markdown, output_file, css_path=css_file, show_stats=True)
        
        html = result['html']
        assert 'link rel="stylesheet"' in html
        assert "custom.css" in html

    def test_no_css_when_not_provided(self, sample_markdown, temp_dir):
        """Test that no CSS link is added when css_path is not provided."""
        output_file = temp_dir / "output.html"
        result = convert_markdown(sample_markdown, output_file, show_stats=True)
        
        html = result['html']
        assert 'link rel="stylesheet"' not in html, "No CSS link should be present when not requested"