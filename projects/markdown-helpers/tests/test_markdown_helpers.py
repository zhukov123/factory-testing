"""Unit tests for markdown utility helpers."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from markdown_helpers import (
    extract_headings,
    count_words,
    strip_markdown,
    extract_links,
    extract_code_blocks,
    extract_code_inline,
    is_valid_markdown_filename,
    get_table_of_contents,
)


class TestExtractHeadings:
    """Tests for extract_headings function."""

    def test_single_h1(self):
        text = "# Hello World"
        result = extract_headings(text)
        assert result == [(1, "Hello World")]

    def test_multiple_headings(self):
        text = """# Title
## Section 1
### Subsection
## Section 2"""
        result = extract_headings(text)
        assert result == [
            (1, "Title"),
            (2, "Section 1"),
            (3, "Subsection"),
            (2, "Section 2"),
        ]

    def test_no_headings(self):
        text = "Just plain text without any headings"
        result = extract_headings(text)
        assert result == []

    def test_max_level_heading(self):
        text = "###### H6"
        result = extract_headings(text)
        assert result == [(6, "H6")]


class TestCountWords:
    """Tests for count_words function."""

    def test_simple_text(self):
        text = "Hello world"
        assert count_words(text) == 2

    def test_with_markdown_bold(self):
        text = "Hello **world**"
        assert count_words(text) == 2

    def test_with_code_blocks(self):
        text = "Hello world\n```python\nprint('test')\n```"
        # Code block content should be excluded
        assert count_words(text) == 2

    def test_with_links(self):
        text = "Check [this link](https://example.com)"
        # Link URL should be excluded, link text counted
        assert count_words(text) == 3  # Check, this, link


class TestStripMarkdown:
    """Tests for strip_markdown function."""

    def test_strip_headers(self):
        text = "# Title\n## Section"
        result = strip_markdown(text)
        assert "Title" in result
        assert "#" not in result

    def test_strip_bold_italic(self):
        text = "**bold** and *italic*"
        result = strip_markdown(text)
        assert result == "bold and italic"

    def test_strip_code(self):
        text = "Use `print()` function"
        result = strip_markdown(text)
        assert result == "Use print() function"


class TestExtractLinks:
    """Tests for extract_links function."""

    def test_single_link(self):
        text = "[Google](https://google.com)"
        result = extract_links(text)
        assert result == [("Google", "https://google.com")]

    def test_multiple_links(self):
        text = "[Google](https://google.com) and [GitHub](https://github.com)"
        result = extract_links(text)
        assert result == [
            ("Google", "https://google.com"),
            ("GitHub", "https://github.com"),
        ]

    def test_no_links(self):
        text = "Just plain text"
        result = extract_links(text)
        assert result == []


class TestExtractCodeBlocks:
    """Tests for extract_code_blocks function."""

    def test_single_code_block(self):
        text = "```python\nprint('hello')\n```"
        result = extract_code_blocks(text)
        assert result == [("python", "print('hello')\n")]

    def test_unspecified_language(self):
        text = "```\nsome code\n```"
        result = extract_code_blocks(text)
        assert result == [("", "some code\n")]

    def test_multiple_code_blocks(self):
        text = """```python
print('hello')
```
```javascript
console.log('hi');
```"""
        result = extract_code_blocks(text)
        assert len(result) == 2


class TestExtractCodeInline:
    """Tests for extract_code_inline function."""

    def test_single_inline_code(self):
        text = "Use `print()` function"
        result = extract_code_inline(text)
        assert result == ["print()"]

    def test_multiple_inline_codes(self):
        text = "Use `x` and `y` variables"
        result = extract_code_inline(text)
        assert result == ["x", "y"]


class TestIsValidMarkdownFilename:
    """Tests for is_valid_markdown_filename function."""

    def test_md_extension(self):
        assert is_valid_markdown_filename("readme.md") is True

    def test_markdown_extension(self):
        assert is_valid_markdown_filename("document.markdown") is True

    def test_uppercase_extension(self):
        assert is_valid_markdown_filename("README.MD") is True

    def test_invalid_extension(self):
        assert is_valid_markdown_filename("readme.txt") is False

    def test_no_extension(self):
        assert is_valid_markdown_filename("readme") is False


class TestGetTableOfContents:
    """Tests for get_table_of_contents function."""

    def test_simple_toc(self):
        text = "# Title\n## Section"
        result = get_table_of_contents(text)
        assert "## Table of Contents" in result
        assert "- [Title](#title)" in result
        assert "- [Section](#section)" in result

    def test_nested_headings(self):
        text = "# Title\n## Section\n### Subsection"
        result = get_table_of_contents(text)
        assert "- [Section](#section)" in result
        assert "  - [Subsection](#subsection)" in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
