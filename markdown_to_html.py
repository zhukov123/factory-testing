#!/usr/bin/env python3
"""CLI tool to convert Markdown to HTML."""

import argparse
import re
import sys
from pathlib import Path


def convert_markdown(input_path: Path, output_path: Path | None = None, css_path: Path | None = None) -> str:
    """Convert markdown file to HTML."""
    content = input_path.read_text(encoding='utf-8')
    html = _parse_markdown(content)
    
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
{html}</body>
</html>
"""
    
    if output_path:
        output_path.write_text(full_html, encoding='utf-8')
    
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
    parser = argparse.ArgumentParser(description='Convert Markdown to HTML')
    parser.add_argument('input', type=Path, help='Input markdown file path')
    parser.add_argument('-o', '--output', type=Path, help='Output HTML file path')
    parser.add_argument('--css', type=Path, help='Optional CSS file to link')
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    if args.css and not args.css.exists():
        print(f"Error: CSS file '{args.css}' not found", file=sys.stderr)
        sys.exit(1)
    
    convert_markdown(args.input, args.output, args.css)
    
    if args.output:
        print(f"Converted {args.input} -> {args.output}")
    else:
        print("Conversion complete (output to stdout not implemented, use -o)")


if __name__ == '__main__':
    main()