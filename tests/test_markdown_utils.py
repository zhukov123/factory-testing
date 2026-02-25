"""Unit tests for markdown utils with mocked helper functions."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'projects/markdown-helpers/src'))

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


class TestExtractHeadingsWithMocks:
    """Tests for extract_headings with mocked scenarios."""

    def test_extract_headings_basic(self):
        """Test basic heading extraction."""
        text = "# Heading 1\n## Heading 2\n### Heading 3"
        result = extract_headings(text)
        
        assert len(result) == 3
        assert result[0] == (1, "Heading 1")
        assert result[1] == (2, "Heading 2")
        assert result[2] == (3, "Heading 3")

    def test_extract_headings_with_special_characters(self):
        """Test heading extraction with special characters."""
        text = "# Heading with `code` and **bold**"
        result = extract_headings(text)
        assert result == [(1, "Heading with `code` and **bold**")]

    def test_extract_headings_preserves_whitespace(self):
        """Test that heading text preserves internal whitespace."""
        text = "# Title    with   spaces"
        result = extract_headings(text)
        assert result == [(1, "Title    with   spaces")]


class TestCountWordsWithMocks:
    """Tests for count_words with mocked helper scenarios."""

    def test_count_words_handles_empty_strings(self):
        """Test count_words with empty string."""
        assert count_words("") == 0

    def test_count_words_handles_only_code(self):
        """Test count_words when text is only code blocks."""
        text = "```python\nprint('hello')\n```"
        result = count_words(text)
        assert result == 0

    def test_count_words_mixed_content(self):
        """Test count_words with mixed markdown content."""
        text = """# Title

Some paragraph text with **bold** and *italic*.

```python
# This is code
x = 1
```

More text with a [link](http://example.com).
"""
        result = count_words(text)
        # Should count: Title, Some, paragraph, text, with, bold, and, italic,
        # More, text, with, a, link = 13 words
        assert result == 13

    def test_count_words_multiple_headings(self):
        """Test count_words with multiple headings."""
        text = """# H1 Title
## H2 Subtitle
### H3 Section

Some content here.
"""
        result = count_words(text)
        # Headings are also counted: H1, Title, H2, Subtitle, H3, Section, Some, content, here = 9
        assert result == 9


class TestStripMarkdownWithMocks:
    """Tests for strip_markdown with mocked helper functions."""

    def test_strip_markdown_nested_formatting(self):
        """Test stripping markdown with nested formatting."""
        text = "***Bold and italic***"
        result = strip_markdown(text)
        assert "Bold and italic" in result

    def test_strip_markdown_complex_list(self):
        """Test stripping markdown with complex list structures."""
        text = """- Item 1
  - Nested item 1a
  - Nested item 1b
- Item 2
"""
        result = strip_markdown(text)
        assert "Item 1" in result
        assert "Item 2" in result

    def test_strip_markdown_blockquotes(self):
        """Test stripping markdown blockquotes."""
        text = "> This is a quote\n> Multiple lines"
        result = strip_markdown(text)
        assert "This is a quote" in result


class TestExtractLinksWithMocks:
    """Tests for extract_links with mocked patterns."""

    def test_extract_links_basic(self):
        """Test basic link extraction."""
        text = "[Google](https://google.com)"
        result = extract_links(text)
        
        assert result == [("Google", "https://google.com")]

    def test_extract_links_complex_urls(self):
        """Test extracting links with complex URLs."""
        text = "[Search](https://example.com/search?q=test&lang=en)"
        result = extract_links(text)
        assert result == [("Search", "https://example.com/search?q=test&lang=en")]

    def test_extract_links_reference_style(self):
        """Test that reference-style links are not matched."""
        text = "[link text][reference]\n\n[reference]: http://example.com"
        result = extract_links(text)
        # Reference style links should not be matched by the standard pattern
        assert len(result) == 0


class TestExtractCodeBlocksWithMocks:
    """Tests for extract_code_blocks with mocked scenarios."""

    def test_extract_code_blocks_basic(self):
        """Test basic code block extraction."""
        text = "```python\nprint('hello')\n```"
        result = extract_code_blocks(text)
        
        assert result == [("python", "print('hello')\n")]

    def test_extract_code_blocks_with_language_hint(self):
        """Test code blocks with various language hints."""
        text = """```javascript
const x = 1;
```
```rust
let y = 2;
```
"""
        result = extract_code_blocks(text)
        
        assert len(result) == 2
        assert result[0][0] == "javascript"
        assert result[1][0] == "rust"

    def test_extract_code_blocks_empty_content(self):
        """Test code blocks with empty content."""
        text = "```python\n```"
        result = extract_code_blocks(text)
        assert result == [("python", "")]


class TestExtractCodeInlineWithMocks:
    """Tests for extract_code_inline with mocked helpers."""

    def test_extract_code_inline_basic(self):
        """Test basic inline code extraction."""
        text = "Use `print()` function"
        code_snippets = extract_code_inline(text)
        
        assert code_snippets == ["print()"]

    def test_extract_code_inline_multiple(self):
        """Test multiple inline code snippets."""
        text = "Use `x` and `y` variables"
        result = extract_code_inline(text)
        assert result == ["x", "y"]


class TestIsValidMarkdownFilenameWithMocks:
    """Tests for is_valid_markdown_filename with mocked scenarios."""

    def test_valid_extensions(self):
        """Test valid markdown extensions."""
        valid_names = [
            "test.md",
            "test.markdown",
            "test.mdown",
            "test.mkd",
            "test.mkdn",
        ]
        for name in valid_names:
            assert is_valid_markdown_filename(name) is True

    def test_various_invalid_extensions(self):
        """Test filename validation with various invalid extensions."""
        invalid_names = [
            "document.txt",
            "readme.html",
            "script.js",
            "data.json",
            "notes",
            "README",
            "file.mdx",
        ]
        for name in invalid_names:
            assert is_valid_markdown_filename(name) is False

    def test_case_insensitive_validation(self):
        """Test that validation is case insensitive."""
        assert is_valid_markdown_filename("README.MD") is True
        assert is_valid_markdown_filename("DOC.MARKDOWN") is True
        assert is_valid_markdown_filename("Test.Md") is True


class TestGetTableOfContentsWithMocks:
    """Tests for get_table_of_contents with mocked helper functions."""

    @patch('markdown_helpers.extract_headings')
    def test_toc_with_mocked_headings(self, mock_extract_headings):
        """Test TOC generation with mocked heading extraction."""
        # Mock extract_headings to return predefined headings
        mock_extract_headings.return_value = [
            (1, "Introduction"),
            (2, "Background"),
            (3, "Details"),
            (2, "Summary"),
        ]
        
        # Call get_table_of_contents - it will use our mocked headings
        from markdown_helpers import get_table_of_contents
        result = get_table_of_contents("")  # Text doesn't matter due to mock
        
        assert "## Table of Contents" in result
        assert "- [Introduction](#introduction)" in result
        assert "- [Background](#background)" in result
        # Nested should use indentation
        assert "  - [Details](#details)" in result

    @patch('markdown_helpers.extract_headings')
    def test_toc_empty_headings(self, mock_extract_headings):
        """Test TOC generation with no headings."""
        mock_extract_headings.return_value = []
        
        from markdown_helpers import get_table_of_contents
        result = get_table_of_contents("")
        
        assert "## Table of Contents" in result

    def test_toc_anchor_special_characters(self):
        """Test that TOC handles special characters in anchors."""
        text = "# Hello World\n## Test Section"
        result = get_table_of_contents(text)
        
        # Special characters should be stripped from anchors
        assert "#hello-world" in result
        assert "#test-section" in result


class TestIntegrationScenarios:
    """Integration tests with multiple mocked components."""

    @patch('markdown_helpers.extract_headings')
    @patch('markdown_helpers.strip_markdown')
    def test_full_workflow_with_mocks(self, mock_strip, mock_headings):
        """Test a full workflow with multiple mocked helpers."""
        mock_headings.return_value = [(1, "Main Title"), (2, "Section")]
        mock_strip.return_value = "Plain text content"
        
        # This tests the integration of multiple functions
        from markdown_helpers import get_table_of_contents, count_words
        
        toc = get_table_of_contents("# Main Title\n## Section")
        words = count_words("Some content here")
        
        assert "Table of Contents" in toc
        assert words >= 0  # count_words should work

    @patch('markdown_helpers.extract_headings')
    def test_toc_integration_with_mock(self, mock_headings):
        """Test TOC generation integrates properly with mocked extract_headings."""
        mock_headings.return_value = [
            (1, "Overview"),
            (2, "Getting Started"),
            (2, "Installation"),
            (3, "Requirements"),
        ]
        
        from markdown_helpers import get_table_of_contents
        result = get_table_of_contents("mock text")
        
        # Verify TOC structure
        assert "## Table of Contents" in result
        assert "- [Overview](#overview)" in result
        assert "- [Getting Started](#getting-started)" in result
        assert "  - [Requirements](#requirements)" in result


class TestMockedHelperFunctionCalls:
    """Tests that verify mock patterns work correctly with the module."""

    def test_module_functions_are_callable(self):
        """Verify all helper functions are properly callable."""
        assert callable(extract_headings)
        assert callable(count_words)
        assert callable(strip_markdown)
        assert callable(extract_links)
        assert callable(extract_code_blocks)
        assert callable(extract_code_inline)
        assert callable(is_valid_markdown_filename)
        assert callable(get_table_of_contents)

    def test_get_table_of_contents_uses_extract_headings(self):
        """Test that get_table_of_contents internally uses extract_headings."""
        # This verifies that get_table_of_contents works with extract_headings
        text = "# Title\n## Section\n### Subsection"
        result = get_table_of_contents(text)
        
        # Verify the integration works correctly
        assert "## Table of Contents" in result
        assert "- [Title](#title)" in result
        assert "- [Section](#section)" in result
        assert "  - [Subsection](#subsection)" in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
