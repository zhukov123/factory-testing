#!/usr/bin/env python3
"""CLI tool to convert Markdown to HTML."""

import argparse
import re
import sys
from pathlib import Path

# Import markdown utilities from the markdown-helpers project
import sys
from pathlib import Path

# Add projects/markdown-helpers/src to path for imports
_markdown_helpers_path = Path(__file__).parent / "projects" / "markdown-helpers" / "src"
if str(_markdown_helpers_path) not in sys.path:
    sys.path.insert(0, str(_markdown_helpers_path))

from markdown_helpers import (
    extract_headings,
    count_words,
    extract_links,
    extract_code_blocks,
    get_table_of_contents,
)


def convert_markdown(input_path: Path, output_path: Path | None = None, css_path: Path | None = None, 
                     include_toc: bool = False, show_stats: bool = False) -> dict | str:
    """Convert markdown file to HTML.
    
    Uses markdown-helpers utilities for enhanced processing.
    
    Args:
        input_path: Path to the input markdown file.
        output_path: Optional path for the output HTML file.
        css_path: Optional path to a CSS file to link.
        include_toc: Whether to include a table of contents.
        show_stats: Whether to show statistics about the document.
        
    Returns:
        If include_toc or show_stats is True, returns a dictionary with:
          - 'html': the HTML content
          - 'stats': document statistics
          - 'toc': table of contents if requested
        Otherwise returns just the HTML string (backwards compatible).
    """
    content = input_path.read_text(encoding='utf-8')
    html = _parse_markdown(content)
    
    # Use markdown_helpers utilities for additional processing
    headings = extract_headings(content)
    links = extract_links(content)
    code_blocks = extract_code_blocks(content)
    word_count = count_words(content)
    
    # Generate table of contents if requested
    toc_html = ""
    if include_toc and headings:
        toc_content = get_table_of_contents(content)
        toc_html = _parse_markdown(toc_content)
    
    # Wrap in HTML document with optional CSS
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{input_path.stem}</title>
"""
    if css_path:
        full_html += f'    <link rel="stylesheet" href="{css_path}">\n'
    
    full_html += f"""</head>
<body>
"""
    
    # Add table of contents if requested
    if toc_html:
        full_html += f"<div class='toc'>\n{toc_html}\n</div>\n"
    
    full_html += f"""{html}
</body>
</html>
"""
    
    if output_path:
        output_path.write_text(full_html, encoding='utf-8')
    
    # Return results - if new features are used, return dict; otherwise return string for backwards compatibility
    if include_toc or show_stats:
        return {
            'html': full_html,
            'stats': {
                'word_count': word_count,
                'heading_count': len(headings),
                'link_count': len(links),
                'code_block_count': len(code_blocks),
            },
            'toc': toc_html if include_toc else None
        }
    
    # Backwards compatible: return just the HTML string
    return full_html


def _parse_markdown(text: str) -> str:
    """Simple markdown to HTML converter."""
    lines = text.split('\n')
    html_lines = []
    in_list = False
    in_ordered_list = False
    
    for line in lines:
        # Headers
        if line.startswith('######'):
            level = min(len(line) - len(line.lstrip('#')), 6)
            content = _inline_format(line.lstrip('#').strip())
            html_lines.append(f'<h{level}>{content}</h{level}>')
            continue
        elif line.startswith('#####'):
            html_lines.append(f'<h5>{_inline_format(line[5:].strip())}</h5>')
            continue
        elif line.startswith('####'):
            html_lines.append(f'<h4>{_inline_format(line[4:].strip())}</h4>')
            continue
        elif line.startswith('###'):
            html_lines.append(f'<h3>{_inline_format(line[3:].strip())}</h3>')
            continue
        elif line.startswith('##'):
            html_lines.append(f'<h2>{_inline_format(line[2:].strip())}</h2>')
            continue
        elif line.startswith('#'):
            html_lines.append(f'<h1>{_inline_format(line[1:].strip())}</h1>')
            continue
        
        # Unordered list
        if line.startswith('- ') or line.startswith('* '):
            if not in_list:
                in_list = True
                html_lines.append('<ul>')
            html_lines.append(f'<li>{_inline_format(line[2:].strip())}</li>')
            continue
        elif in_list:
            in_list = False
            html_lines.append('</ul>')
        
        # Ordered list
        if re.match(r'^\d+\.\s', line):
            if not in_ordered_list:
                in_ordered_list = True
                html_lines.append('<ol>')
            content = re.sub(r'^\d+\.\s', '', line)
            html_lines.append(f'<li>{_inline_format(content.strip())}</li>')
            continue
        elif in_ordered_list:
            in_ordered_list = False
            html_lines.append('</ol>')
        
        # Horizontal rule
        if line.strip() in ['---', '***', '___']:
            html_lines.append('<hr>')
            continue
        
        # Empty line
        if not line.strip():
            continue
        
        # Paragraph
        html_lines.append(f'<p>{_inline_format(line.strip())}</p>')
    
    # Close any open lists
    if in_list:
        html_lines.append('</ul>')
    if in_ordered_list:
        html_lines.append('</ol>')
    
    return '\n'.join(html_lines)


def _inline_format(text: str) -> str:
    """Convert inline markdown formatting to HTML."""
    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    
    # Italic: *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    
    # Inline code: `code`
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    
    # Links: [text](url)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    
    return text


def main():
    """Main entry point for the markdown to HTML CLI."""
    parser = argparse.ArgumentParser(
        description='Convert Markdown to HTML',
        epilog='Examples:\n'
               '  %(prog)s input.md -o output.html\n'
               '  %(prog)s input.md --css style.css\n'
               '  %(prog)s input.md --include-toc --show-stats',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'input', 
        type=Path, 
        help='Input markdown file path'
    )
    parser.add_argument(
        '-o', 
        '--output', 
        type=Path, 
        help='Output HTML file path (default: stdout)'
    )
    parser.add_argument(
        '--css', 
        type=Path, 
        help='Optional CSS file to link in the HTML'
    )
    parser.add_argument(
        '--include-toc',
        action='store_true',
        help='Generate and include a table of contents'
    )
    parser.add_argument(
        '--show-stats',
        action='store_true',
        help='Display document statistics after conversion'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.1.0'
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    if args.css and not args.css.exists():
        print(f"Error: CSS file '{args.css}' not found", file=sys.stderr)
        sys.exit(1)
    
    result = convert_markdown(
        args.input, 
        args.output, 
        args.css,
        include_toc=args.include_toc,
        show_stats=args.show_stats
    )
    
    # Handle both dict (new API) and string (backwards compatible) returns
    if isinstance(result, dict):
        html_content = result['html']
        stats = result['stats']
    else:
        html_content = result
        stats = None
    
    if args.output:
        print(f"Converted {args.input} -> {args.output}")
    else:
        # Output to stdout
        print(html_content)
    
    # Show statistics if requested
    if args.show_stats and stats:
        print("\nDocument Statistics:")
        print(f"  Words: {stats['word_count']}")
        print(f"  Headings: {stats['heading_count']}")
        print(f"  Links: {stats['link_count']}")
        print(f"  Code blocks: {stats['code_block_count']}")


if __name__ == '__main__':
    main()