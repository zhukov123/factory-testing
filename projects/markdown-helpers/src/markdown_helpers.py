"""Markdown utility helpers for processing and analyzing markdown content."""

import re
from typing import List, Tuple


def extract_headings(text: str) -> List[Tuple[int, str]]:
    """Extract all headings from markdown text.
    
    Args:
        text: Markdown content to parse.
        
    Returns:
        List of tuples (level, heading_text) for each heading found.
        Level is 1-6 corresponding to h1-h6.
    """
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    headings = []
    for match in heading_pattern.finditer(text):
        level = len(match.group(1))
        heading_text = match.group(2).strip()
        headings.append((level, heading_text))
    return headings


def count_words(text: str) -> int:
    """Count words in markdown text (excluding markdown syntax).
    
    Args:
        text: Markdown content to analyze.
        
    Returns:
        Number of words in the content.
    """
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)
    # Remove links but keep link text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Remove markdown formatting characters but keep text
    text = re.sub(r'[*_#>\-+]', '', text)
    # Count words
    words = text.split()
    return len(words)


def strip_markdown(text: str) -> str:
    """Remove markdown formatting from text.
    
    Args:
        text: Markdown content to strip.
        
    Returns:
        Plain text with markdown formatting removed.
    """
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Replace links with just the text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Replace images with alt text
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
    # Remove list markers
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
    return text


def extract_links(text: str) -> List[Tuple[str, str]]:
    """Extract all links from markdown text.
    
    Args:
        text: Markdown content to parse.
        
    Returns:
        List of tuples (link_text, url) for each link found.
    """
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    return [(match.group(1), match.group(2)) for match in link_pattern.finditer(text)]


def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
    """Extract all code blocks from markdown text.
    
    Args:
        text: Markdown content to parse.
        
    Returns:
        List of tuples (language, code) for each code block found.
        Language may be empty string if not specified.
    """
    # Match fenced code blocks
    code_block_pattern = re.compile(r'```(\w*)\n([\s\S]*?)```')
    blocks = []
    for match in code_block_pattern.finditer(text):
        language = match.group(1) or ''
        code = match.group(2)
        blocks.append((language, code))
    return blocks


def extract_code_inline(text: str) -> List[str]:
    """Extract all inline code snippets from markdown text.
    
    Args:
        text: Markdown content to parse.
        
    Returns:
        List of inline code snippets.
    """
    inline_pattern = re.compile(r'`([^`]+)`')
    return [match.group(1) for match in inline_pattern.finditer(text)]


def is_valid_markdown_filename(filename: str) -> bool:
    """Check if a filename is valid for a markdown file.
    
    Args:
        filename: The filename to validate.
        
    Returns:
        True if filename ends with .md, .markdown, or .mdown.
    """
    valid_extensions = ('.md', '.markdown', '.mdown', '.mkd', '.mkdn')
    return filename.lower().endswith(valid_extensions)


def get_table_of_contents(text: str) -> str:
    """Generate a table of contents from markdown headings.
    
    Args:
        text: Markdown content to generate TOC from.
        
    Returns:
        Markdown-formatted table of contents.
    """
    headings = extract_headings(text)
    toc_lines = ["## Table of Contents\n"]
    
    for level, heading_text in headings:
        indent = "  " * (level - 1)
        # Create anchor from heading text
        anchor = heading_text.lower().replace(' ', '-')
        anchor = re.sub(r'[^\w\-]', '', anchor)
        toc_lines.append(f"{indent}- [{heading_text}](#{anchor})")
    
    return '\n'.join(toc_lines)
